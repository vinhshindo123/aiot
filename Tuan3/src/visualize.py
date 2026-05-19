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

# Get available sensor columns (numeric columns except metadata)
sensor_cols = [c for c in df.columns if c in ['temp', 'humi', 'ph', 'ec', 'water_temp', 'light', 'co2'] 
               and c in df.columns]

threshold = None
if metrics_file.exists():
    metrics = json.loads(metrics_file.read_text(encoding="utf-8"))
    threshold = metrics.get("threshold")

# Plot 1: All sensor series with anomalies
fig, axes = plt.subplots(len(sensor_cols), 1, figsize=(14, 3*len(sensor_cols)), sharex=True)
if len(sensor_cols) == 1:
    axes = [axes]

for idx, sensor in enumerate(sensor_cols):
    axes[idx].plot(df["created_at"], df[sensor], label=sensor, linewidth=1.5)
    axes[idx].scatter(df[df["is_anomaly"] == 1]["created_at"], 
                     df[df["is_anomaly"] == 1][sensor], 
                     color="red", label="detected anomaly", s=30, zorder=5)
    axes[idx].set_ylabel(sensor.upper())
    axes[idx].legend(loc='upper right')
    axes[idx].grid(True, alpha=0.3)

axes[-1].set_xlabel("Timestamp")
plt.suptitle("Hydroponics Sensor Series and Detected Anomalies", fontsize=14, y=1.02)
plt.tight_layout()
plt.savefig(FIG / "anomaly_detection_result.png", dpi=160, bbox_inches='tight')
plt.close()

# Plot 2: Anomaly scores over time
plt.figure(figsize=(14, 5))
plt.plot(df["created_at"], df["anomaly_score"], label="anomaly_score", color="#fb7185", linewidth=1.5)
if threshold is not None:
    plt.axhline(float(threshold), linestyle="--", color="#38bdf8", label=f"threshold={threshold}")
plt.fill_between(df["created_at"], 0, df["anomaly_score"], where=df["anomaly_score"]>=threshold if threshold else False,
                  color="red", alpha=0.3, label="anomaly region")
plt.title("Anomaly Score Over Time - Hydroponics System", fontsize=14)
plt.xlabel("Timestamp")
plt.ylabel("Anomaly Score")
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(FIG / "anomaly_score_over_time.png", dpi=160)
plt.close()

# Plot 3: Confusion matrix heatmap (if metrics available)
if metrics and 'confusion_matrix' in metrics:
    import seaborn as sns
    cm = metrics['confusion_matrix']
    plt.figure(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=['Normal', 'Anomaly'], 
                yticklabels=['Normal', 'Anomaly'])
    plt.title('Confusion Matrix - Anomaly Detection')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.tight_layout()
    plt.savefig(FIG / "confusion_matrix.png", dpi=160)
    plt.close()

# Print summary
print(f"Saved figures to {FIG}")
print(f"\nDetection Summary:")
print(f"Total test samples: {len(df)}")
print(f"Anomalies detected: {df['is_anomaly'].sum()}")
if 'label' in df.columns:
    print(f"Actual anomalies: {df['label'].sum()}")
    from sklearn.metrics import classification_report
    print("\nClassification Report:")
    print(classification_report(df['label'], df['is_anomaly'], 
                                target_names=['Normal', 'Anomaly']))