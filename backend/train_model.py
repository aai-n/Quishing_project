import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib

df = pd.read_csv("qr_dataset.csv")

X = df[["is_https", "domain_length", "has_suspicious_words", "is_upi", "has_logo"]]
y = df["label"]

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X, y)

joblib.dump(model, "model.pkl")
print("Random Forest trained and saved as model.pkl")