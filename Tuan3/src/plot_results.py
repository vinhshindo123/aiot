from __future__ import annotations

from pathlib import Path
import json
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
FIG = ROOT / "figures"
FIG.mkdir(exist_ok=True)

pred_file = OUT / "iforest_test_predictions.csv"
metrics_file = OUT / "iforest_metrics.json"
if not pred_file.exists():
    raise FileNotFoundError("Hãy chạy python src/train_anomaly.py trước.")

df = pd.read_csv(pred_file)
df["created_at"] = pd.to_datetime(df["created_at"])

threshold = None
if metrics_file.exists():
    metrics = json.loads(metrics_file.read_text(encoding="utf-8"))
    threshold = metrics.get("threshold")

plt.figure(figsize=(14, 5))
for sensor in ["temp", "humi", "soil", "light"]:
    plt.plot(df["created_at"], df[sensor], label=sensor)
plt.scatter(df[df["is_anomaly"] == 1]["created_at"], df[df["is_anomaly"] == 1]["temp"], color="red", label="detected anomaly", zorder=5)
plt.title("IoT sensor series and detected anomalies")
plt.xlabel("Timestamp")
plt.ylabel("Sensor values")
plt.legend()
plt.tight_layout()
plt.savefig(FIG / "anomaly_detection_result.png", dpi=160)
plt.close()

plt.figure(figsize=(14, 4))
plt.plot(df["created_at"], df["anomaly_score"], label="anomaly_score", color="#fb7185")
if threshold is not None:
    plt.axhline(float(threshold), linestyle="--", color="#38bdf8", label=f"threshold={threshold}")
plt.title("Anomaly score over time")
plt.xlabel("Timestamp")
plt.ylabel("Score")
plt.legend()
plt.tight_layout()
plt.savefig(FIG / "anomaly_score_over_time.png", dpi=160)
plt.close()

print("Saved figures to", FIG)
