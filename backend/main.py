from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np

app = FastAPI()

# ---- CORS setup ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/analyze")
async def analyze_qr(image: UploadFile = File(...)):
    # Read image bytes
    contents = await image.read()
    np_img = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)

    if img is None:
        return {"error": "Invalid image"}

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    qr_detector = cv2.QRCodeDetector()
    detected, points = qr_detector.detect(gray)

    if not detected:
        return {"fraud": True, "reason": "No QR structure detected"}

    # Structural features
    points = points[0]
    x_coords = points[:, 0]
    y_coords = points[:, 1]

    width = int(max(x_coords) - min(x_coords))
    height = int(max(y_coords) - min(y_coords))

    qr_area = width * height
    image_area = img.shape[0] * img.shape[1]
    relative_size = qr_area / image_area

    _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)
    black_pixels = np.sum(binary == 0)
    white_pixels = np.sum(binary == 255)
    bw_ratio = black_pixels / (white_pixels + 1)

    density = black_pixels / (black_pixels + white_pixels)

    fraud_score = 0
    if relative_size < 0.05:
        fraud_score += 1
    if bw_ratio < 0.3 or bw_ratio > 2.0:
        fraud_score += 1
    if density < 0.2 or density > 0.8:
        fraud_score += 1

    is_fraud = fraud_score >= 2

    return {
        "fraud": is_fraud,
        "features": {
            "relative_size": round(relative_size, 4),
            "black_white_ratio": round(bw_ratio, 2),
            "density": round(density, 2)
        }
    }
