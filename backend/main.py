from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np
from urllib.parse import urlparse

app = FastAPI()

# ------------------ CORS ------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------ API ------------------
@app.post("/analyze")
async def analyze_qr(image: UploadFile = File(...)):
    print("🔥 NEW BACKEND CODE RUNNING 🔥")

    contents = await image.read()
    np_img = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)

    if img is None:
        return {"fraud": True, "confidence": "High", "reason": "Invalid image"}

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    qr = cv2.QRCodeDetector()

    # ✅ Decode QR
    data, points, _ = qr.detectAndDecode(gray)

    print("Decoded data:", data)

    if not data:
        return {
            "fraud": True,
            "confidence": "High",
            "reason": "Unreadable or broken QR"
        }

    # ------------------ STRUCTURE FEATURES ------------------
    score = 0
    reasons = []

    if points is not None:
        pts = points[0]
        x, y = pts[:, 0], pts[:, 1]
        qr_area = (max(x) - min(x)) * (max(y) - min(y))
        image_area = img.shape[0] * img.shape[1]
        relative_size = qr_area / image_area
    else:
        relative_size = 0

    _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)
    black = np.sum(binary == 0)
    white = np.sum(binary == 255)
    bw_ratio = black / (white + 1)
    density = black / (black + white)

    # ------------------ LOGO DETECTION ------------------
    h, w = gray.shape
    center = gray[int(h*0.35):int(h*0.65), int(w*0.35):int(w*0.65)]
    _, cbin = cv2.threshold(center, 128, 255, cv2.THRESH_BINARY)
    center_black_ratio = np.sum(cbin == 0) / cbin.size
    has_logo = center_black_ratio < 0.15

    # ------------------ STRUCTURAL SCORING ------------------
    if relative_size < 0.03:
        score += 0.5
        reasons.append("Very small QR")

    if bw_ratio < 0.2 or bw_ratio > 3.5:
        score += 0.5
        reasons.append("Abnormal black-white ratio")

    if density < 0.15 or density > 0.85:
        score += 0.5
        reasons.append("Unusual pixel density")

    # ------------------ CONTENT CHECK (MOST IMPORTANT) ------------------
    # UPI QRs are SAFE
    if data.startswith("upi://"):
        score = 0
        reasons = ["Valid UPI payment QR"]

    # HTTPS URLs are SAFE by default
    elif data.startswith("https://"):
        parsed = urlparse(data)
        if len(parsed.netloc) < 5:
            score += 0.5
            reasons.append("Suspicious short domain")

    # HTTP URLs are risky but not auto-fraud
    elif data.startswith("http://"):
        score += 1.0
        reasons.append("Non-HTTPS URL")

    # Everything else (text, wifi, app deep links)
    else:
        reasons.append("Non-link QR (safe)")

    # ------------------ FINAL DECISION ------------------
    is_fraud = score >= 2.5

    confidence = (
        "High" if score >= 2.5 else
        "Medium" if score >= 1.5 else
        "Low"
    )

    print("Score:", score, "Reasons:", reasons)

    return {
        "fraud": is_fraud,
        "confidence": confidence,
        "decoded_data": data[:120],
        "features": {
            "relative_size": round(relative_size, 4),
            "bw_ratio": round(bw_ratio, 2),
            "density": round(density, 2),
            "logo_detected": has_logo
        },
        "reason": ", ".join(reasons)
    }
