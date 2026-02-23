# backend/main.py
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np
from urllib.parse import urlparse
import re
import joblib

app = FastAPI()

# ------------------ CORS ------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------ Load ML Model ------------------
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # backend folder
model_path = os.path.join(BASE_DIR, "model.pkl")
model = joblib.load(model_path)
# ------------------ Helper Functions ------------------
def decode_qr(image_bytes):
    np_img = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
    if img is None:
        return None, None
    qr = cv2.QRCodeDetector()
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    data, _, _ = qr.detectAndDecode(gray)
    return data, img

def detect_logo(img):
    h, w = img.shape[:2]
    center = img[int(h*0.35):int(h*0.65), int(w*0.35):int(w*0.65)]
    gray = cv2.cvtColor(center, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)
    center_black_ratio = np.sum(binary == 0) / binary.size
    return 1 if center_black_ratio < 0.15 else 0

def extract_features(data, img):
    # Default features
    is_https = 0
    domain_length = 0
    has_suspicious_words = 0
    is_upi = 0
    has_logo = detect_logo(img)

    content_type = "Other"

    if data.startswith("upi://"):
        content_type = "UPI"
        is_upi = 1
        # Optional: validate UPI format
        if not re.match(r"upi://pay\?pa=.*&pn=.*", data):
            has_suspicious_words = 1

    elif data.startswith("https://"):
        content_type = "HTTPS URL"
        parsed = urlparse(data)
        is_https = 1
        domain_length = len(parsed.netloc)
        # Simple suspicious words check
        suspicious_words = ["login", "verify", "bank", "update", "secure"]
        if any(word in data.lower() for word in suspicious_words):
            has_suspicious_words = 1

    elif data.startswith("http://"):
        content_type = "HTTP URL"
        parsed = urlparse(data)
        domain_length = len(parsed.netloc)
        has_suspicious_words = 1  # HTTP is risky

    else:
        content_type = "Text"

    features = [is_https, domain_length, has_suspicious_words, is_upi, has_logo]
    return features, content_type

# ------------------ API Endpoint ------------------
@app.post("/analyze")
async def analyze_qr(image: UploadFile = File(...)):
    contents = await image.read()
    data, img = decode_qr(contents)
    if not data or img is None:
        return {"fraud": True, "confidence": "High", "decoded_data": "", "content_type": "Unknown", "reason": "Unreadable image"}

    features, content_type = extract_features(data, img)
    
    # ML prediction (deterministic)
    prediction = model.predict([features])[0]  # 0 = safe, 1 = fraud

    confidence = "High" if prediction == 1 else "Low"
    reason = "Fraud detected" if prediction == 1 else "Safe QR"

    return {
        "decoded_data": data[:200],
        "content_type": content_type,
        "fraud": bool(prediction),
        "confidence": confidence,
        "reason": reason
    }