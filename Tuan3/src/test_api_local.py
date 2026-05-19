from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from fastapi.testclient import TestClient

from app import app

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)
DATA_FILE = ROOT / "data" / "measurements.csv"
if not DATA_FILE.exists():
    raise FileNotFoundError("Thiếu data/measurements.csv. Hãy chạy python src/download_data.py")

df = pd.read_csv(DATA_FILE).sort_values("created_at").tail(40)
history = [
    {
        "timestamp": str(row["created_at"]),
        "node_id": row["node_id"],
        "temp": float(row["temp"]),
        "humi": float(row["humi"]),
        "soil": float(row["soil"]),
        "light": float(row["light"]),
    }
    for _, row in df.iterrows()
]

client = TestClient(app)
print("Kiểm tra /health")
health = client.get("/health").json()
print(health)

print("\nKiểm tra /model-info")
model_info = client.get("/model-info").json()
print(model_info)

print("\nKiểm tra /detect-anomaly")
resp = client.post("/detect-anomaly", json={"history": history})
print(resp.status_code)
data = resp.json()
print(json.dumps(data, ensure_ascii=False, indent=2))
assert resp.status_code == 200
assert "model_output" in data
assert "event" in data
assert "anomaly_score" in data["model_output"]
assert "decision" in data["event"]
assert "severity" in data["event"]

(OUT / "api_test_result.json").write_text(json.dumps({"health": health, "model_info": model_info, "detect_anomaly": data}, ensure_ascii=False, indent=2), encoding="utf-8")
print("\nPASS: API response schema hợp lệ.")
print("Đã lưu outputs/api_test_result.json")
