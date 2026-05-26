from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from Lab_01.src.utils import OUTPUT_DIR, FIGURE_DIR, DATE_COL, load_dataset

PRED_PATH = OUTPUT_DIR / "forecast_test_predictions.csv"
LOG_PATH = OUTPUT_DIR / "forecast_log.csv"
METRICS_PATH = OUTPUT_DIR / "forecast_metrics.json"


def main():
    if not PRED_PATH.exists() or not LOG_PATH.exists() or not METRICS_PATH.exists():
        raise FileNotFoundError("Hãy chạy `python src/train_forecast.py` trước khi vẽ biểu đồ.")

    FIGURE_DIR.mkdir(exist_ok=True)
    raw_df = load_dataset()
    pred = pd.read_csv(PRED_PATH, parse_dates=[DATE_COL])
    log = pd.read_csv(LOG_PATH, parse_dates=["timestamp"])
    metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
    best = metrics["best_model_name"]

    # EDA: sensor trend for first 300 rows
    eda_sample = raw_df.head(300)
    plt.figure(figsize=(12, 5))
    plt.plot(eda_sample[DATE_COL], eda_sample["temp"], label="temp")
    plt.plot(eda_sample[DATE_COL], eda_sample["humi"], label="humi")
    plt.plot(eda_sample[DATE_COL], eda_sample["soil"], label="soil")
    plt.plot(eda_sample[DATE_COL], eda_sample["light"], label="light")
    plt.xlabel("timestamp")
    plt.ylabel("value")
    plt.title("NODE_03 sensor trend (first 300 samples)")
    plt.legend()
    plt.xticks(rotation=30)
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "eda_sensor_trends.png", dpi=160)
    plt.close()

    # EDA: distribution of temperature and humidity
    plt.figure(figsize=(12, 4))
    plt.hist(raw_df["temp"].dropna(), bins=30, alpha=0.7, label="temp")
    plt.hist(raw_df["humi"].dropna(), bins=30, alpha=0.5, label="humi")
    plt.legend()
    plt.title("Distribution of temp and humi")
    plt.xlabel("value")
    plt.ylabel("frequency")
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "eda_distribution.png", dpi=160)
    plt.close()

    # EDA: correlation matrix for key features
    corr_cols = ["temp", "humi", "soil", "light", "rssi_mean", "cmd_count", "cmd_failure_rate"]
    corr = raw_df[corr_cols].corr()
    plt.figure(figsize=(8, 6))
    im = plt.imshow(corr, cmap="coolwarm", vmin=-1, vmax=1)
    plt.colorbar(im, fraction=0.04, pad=0.04)
    plt.xticks(range(len(corr_cols)), corr_cols, rotation=45, ha="right")
    plt.yticks(range(len(corr_cols)), corr_cols)
    plt.title("Correlation matrix for NODE_03 features")
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "eda_correlation_matrix.png", dpi=160)
    plt.close()

    sample = pred.tail(min(350, len(pred)))
    plt.figure(figsize=(12, 5))
    plt.plot(sample[DATE_COL], sample["actual_future_value"], label="actual future temperature")
    plt.plot(sample[DATE_COL], sample[f"pred_{best}"], label=f"prediction: {best}")
    plt.title("Forecast vs Actual (NODE_03 temperature)")
    plt.xlabel("time")
    plt.ylabel("temperature (°C)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "forecast_vs_actual.png", dpi=160)
    plt.close()

    sample_log = log.tail(min(350, len(log)))
    plt.figure(figsize=(12, 4))
    plt.plot(sample_log["timestamp"], sample_log["forecast_error"], label="forecast error")
    plt.axhline(0, linestyle="--", linewidth=1)
    plt.title("Forecast error over time")
    plt.xlabel("time")
    plt.ylabel("predicted - actual (°C)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "forecast_error_over_time.png", dpi=160)
    plt.close()

    names = list(metrics["metrics_by_model"].keys())
    maes = [metrics["metrics_by_model"][n]["mae"] for n in names]
    rmses = [metrics["metrics_by_model"][n]["rmse"] for n in names]
    plt.figure(figsize=(10, 4.5))
    plt.bar(range(len(names)), maes)
    plt.xticks(range(len(names)), names, rotation=25, ha="right")
    plt.title("Model comparison by MAE")
    plt.ylabel("MAE (°C)")
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "model_comparison_mae.png", dpi=160)
    plt.close()

    plt.figure(figsize=(10, 5))
    x = np.arange(len(names))
    width = 0.35
    plt.bar(x - width / 2, maes, width, label="MAE")
    plt.bar(x + width / 2, rmses, width, label="RMSE")
    plt.xticks(x, names, rotation=25, ha="right")
    plt.title("Model comparison by MAE and RMSE")
    plt.ylabel("Error (°C)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "model_comparison_all_metrics.png", dpi=160)
    plt.close()

    plt.figure(figsize=(10, 4.5))
    plt.hist(pred["actual_future_value"], bins=30, color="#4c72b0", alpha=0.8)
    plt.title("Distribution of target temperatures for NODE_03")
    plt.xlabel("target_temp_next_1 (°C)")
    plt.ylabel("frequency")
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "target_distribution.png", dpi=160)
    plt.close()

    print("Saved figures:")
    for fn in [
        "forecast_vs_actual.png",
        "forecast_error_over_time.png",
        "model_comparison_mae.png",
        "model_comparison_all_metrics.png",
        "target_distribution.png",
        "eda_sensor_trends.png",
        "eda_distribution.png",
        "eda_correlation_matrix.png",
    ]:
        print(FIGURE_DIR / fn)


if __name__ == "__main__":
    main()
