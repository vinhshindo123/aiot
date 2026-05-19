from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)
DATA_FILE = ROOT / "data" / "measurements.csv"
if not DATA_FILE.exists():
    raise FileNotFoundError("Thiếu data/measurements.csv. Hãy chạy python src/download_data.py --source <path_to_csv>")

df = pd.read_csv(DATA_FILE).sort_values("created_at").tail(40)

# Get available sensor columns
sensor_cols = [c for c in ['temp', 'humi', 'ph', 'ec', 'water_temp', 'light', 'co2'] 
               if c in df.columns]

# Build history with available sensors
history = []
for _, row in df.iterrows():
    point = {
        "timestamp": str(row["created_at"]),
        "node_id": row["node_id"],
    }
    # Add each sensor if exists
    for sensor in sensor_cols:
        point[sensor] = float(row[sensor])
    history.append(point)

try:
    print("Kiểm tra /health")
    health = requests.get("http://127.0.0.1:8000/health", timeout=10).json()
    print(health)

    print("\nKiểm tra /model-info")
    model_info = requests.get("http://127.0.0.1:8000/model-info", timeout=10).json()
    print(model_info)

    print("\nKiểm tra /detect-anomaly")
    resp = requests.post("http://127.0.0.1:8000/detect-anomaly", json={"history": history}, timeout=10)
    data = resp.json()
    print(json.dumps(data, ensure_ascii=False, indent=2))
    assert resp.status_code == 200
    assert "model_output" in data
    assert "event" in data
    assert "anomaly_score" in data["model_output"]
    assert "decision" in data["event"]

    (OUT / "api_test_result.json").write_text(
        json.dumps({"health": health, "model_info": model_info, "detect_anomaly": data}, 
                   ensure_ascii=False, indent=2), 
        encoding="utf-8"
    )
    print("\nPASS: API response schema hợp lệ.")
    print(f"Đã lưu outputs/api_test_result.json")
    
except requests.exceptions.ConnectionError:
    print("ERROR: Cannot connect to API server. Please run: uvicorn src.app:app --reload")
except Exception as e:
    print(f"ERROR: {e}")