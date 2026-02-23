import cv2
import numpy as np
import pandas as pd
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import requests
import re
import os

DATASET_PATH = "backend/dataset"  # dataset/safe and dataset/fraud

columns = ["is_https", "domain_length", "has_suspicious_words", "is_upi", "has_logo", "label"]
data_rows = []

def decode_qr(image_path):
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    qr = cv2.QRCodeDetector()
    data, _, _ = qr.detectAndDecode(gray)
    return data, img

def detect_logo(img):
    h, w = img.shape[:2]
    center = img[int(h*0.35):int(h*0.65), int(w*0.35):int(w*0.65)]
    gray = cv2.cvtColor(center, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)
    center_black_ratio = np.sum(binary == 0) / binary.size
    return 1 if center_black_ratio < 0.15 else 0

def analyze_url(url):
    features = {}
    parsed = urlparse(url)
    features["is_https"] = 1 if parsed.scheme == "https" else 0
    features["domain_length"] = len(parsed.netloc)
    suspicious_words = ["login", "verify", "bank", "update", "secure"]
    features["has_suspicious_words"] = 1 if any(word in url.lower() for word in suspicious_words) else 0
    try:
        response = requests.get(url, timeout=3)
        soup = BeautifulSoup(response.text, "html.parser")
        forms = soup.find_all("form")
        if len(forms) > 3:
            features["has_suspicious_words"] = 1
    except:
        pass
    return features

def validate_upi(data):
    upi_pattern = r"upi://pay\?pa=.*&pn=.*"
    return 1 if re.match(upi_pattern, data) else 0

for label_folder, label in [("safe", 0), ("fraud", 1)]:
    folder_path = os.path.join(DATASET_PATH, label_folder)
    if not os.path.exists(folder_path):
        continue
    for file in os.listdir(folder_path):
        if not file.lower().endswith((".png", ".jpg", ".jpeg")):
            continue
        path = os.path.join(folder_path, file)
        print(f"Processing file: {path}") 
        try:
            data, img = decode_qr(path)
            if not data:
                continue
            is_https = 0
            domain_length = 0
            has_suspicious_words = 0
            is_upi = 0
            has_logo = detect_logo(img)
            if data.startswith("http"):
                url_features = analyze_url(data)
                is_https = url_features["is_https"]
                domain_length = url_features["domain_length"]
                has_suspicious_words = url_features["has_suspicious_words"]
            elif data.startswith("upi://"):
                is_upi = validate_upi(data)
            row = [is_https, domain_length, has_suspicious_words, is_upi, has_logo, label]
            data_rows.append(row)
        except Exception as e:
            print(f"Error processing {file}: {e}")

df = pd.DataFrame(data_rows, columns=columns)
df.to_csv("qr_dataset.csv", index=False)
print("Dataset saved to qr_dataset.csv")