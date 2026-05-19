from __future__ import annotations

import json
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.exceptions import ConvergenceWarning
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from utils import (
    MODEL_DIR, OUTPUT_DIR,
    load_dataset, add_time_features, time_split, build_events,
    evaluate_detection, make_windows, save_json, normalize_scores, infer_sensor_columns
)

MODEL_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

MODEL_VERSION = "iforest_v2"
MODEL_BUNDLE_PATH = MODEL_DIR / "anomaly_model_bundle_iforest_v2.joblib"
LEGACY_MODEL_PATH = MODEL_DIR / "isolation_forest_iforest_v1.joblib"


def train_isolation_forest() -> dict:
    df = add_time_features(load_dataset())
    train_df, test_df = time_split(df, train_ratio=0.65)
    train_normal = train_df[train_df["label"] == 0].copy()
    if len(train_normal) < 50:
        train_normal = train_df.copy()
    
    # Infer feature columns from the processed dataframe
    feature_columns = infer_sensor_columns(train_normal)
    print(f"Using features: {feature_columns}")

    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("detector", IsolationForest(n_estimators=200, contamination=0.05, random_state=42))
    ])
    pipeline.fit(train_normal[feature_columns])

    train_raw_scores = -pipeline.named_steps["detector"].score_samples(
        pipeline.named_steps["scaler"].transform(train_normal[feature_columns])
    )
    score_min = float(np.min(train_raw_scores))
    score_max = float(np.max(train_raw_scores))
    train_scores = normalize_scores(train_raw_scores, score_min, score_max)
    threshold = float(np.quantile(train_scores, 0.96))

    test_raw_scores = -pipeline.named_steps["detector"].score_samples(
        pipeline.named_steps["scaler"].transform(test_df[feature_columns])
    )
    test_scores = normalize_scores(test_raw_scores, score_min, score_max)

    test_result = test_df.copy()
    test_result["anomaly_score"] = test_scores
    test_result["is_anomaly"] = (test_result["anomaly_score"] >= threshold).astype(int)
    test_result["model_version"] = MODEL_VERSION

    metrics = evaluate_detection(test_result["label"], test_result["is_anomaly"])
    metrics.update({
        "threshold": float(round(threshold, 4)),
        "score_min_train": float(round(score_min, 6)),
        "score_max_train": float(round(score_max, 6)),
        "train_rows": int(len(train_df)),
        "train_normal_rows": int(len(train_normal)),
        "test_rows": int(len(test_df)),
        "model_type": "IsolationForest",
        "model_version": MODEL_VERSION,
        "feature_columns": feature_columns,
        "threshold_policy": "Threshold lấy từ phân bố anomaly_score của train_normal",
        "note": "Precision/Recall/F1 chỉ có ý nghĩa khi nhãn anomaly có sẵn."
    })

    model_bundle = {
        "pipeline": pipeline,
        "feature_columns": feature_columns,
        "score_min": score_min,
        "score_max": score_max,
        "threshold": threshold,
        "model_version": MODEL_VERSION,
    }
    joblib.dump(model_bundle, MODEL_BUNDLE_PATH)
    joblib.dump(pipeline, LEGACY_MODEL_PATH)

    save_json(metrics, OUTPUT_DIR / "iforest_metrics.json")
    test_result.to_csv(OUTPUT_DIR / "iforest_test_predictions.csv", index=False)

    events = build_events(test_result, threshold=threshold)
    events.to_csv(OUTPUT_DIR / "anomaly_event_log.csv", index=False)

    print("=== Isolation Forest metrics ===")
    print(json.dumps(metrics, indent=2, ensure_ascii=False))
    print(f"Đã lưu model bundle: {MODEL_BUNDLE_PATH}")
    print(f"Đã lưu event log: {OUTPUT_DIR / 'anomaly_event_log.csv'}")
    return metrics


def train_neural_autoencoder_demo(window_size: int = 24) -> dict:
    df = add_time_features(load_dataset())
    train_df, test_df = time_split(df, train_ratio=0.65)
    
    # Use temp as primary sensor for autoencoder
    train_normal_values = train_df.loc[train_df["label"] == 0, "temp"].values
    if len(train_normal_values) < window_size + 10:
        train_normal_values = train_df["temp"].values

    scaler = StandardScaler()
    train_scaled = scaler.fit_transform(train_normal_values.reshape(-1, 1)).ravel()
    test_scaled = scaler.transform(test_df["temp"].values.reshape(-1, 1)).ravel()

    X_train = make_windows(train_scaled, window_size=window_size)
    X_test = make_windows(test_scaled, window_size=window_size)

    ae = MLPRegressor(
        hidden_layer_sizes=(16, 6, 16),
        activation="relu",
        solver="adam",
        max_iter=250,
        random_state=42,
        early_stopping=True,
        n_iter_no_change=25,
    )

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=ConvergenceWarning)
        ae.fit(X_train, X_train)

    reconstructed = ae.predict(X_test)
    reconstruction_mse = ((X_test - reconstructed) ** 2).mean(axis=1)

    train_reconstructed = ae.predict(X_train)
    train_mse = ((X_train - train_reconstructed) ** 2).mean(axis=1)
    threshold = float(np.quantile(train_mse, 0.96))

    pred = (reconstruction_mse >= threshold).astype(int)
    aligned = test_df.iloc[window_size - 1 :].copy().reset_index(drop=True)
    aligned["reconstruction_mse"] = reconstruction_mse
    aligned["is_anomaly_ae"] = pred

    metrics = evaluate_detection(aligned["label"], aligned["is_anomaly_ae"])
    metrics.update({
        "threshold_mse": float(round(threshold, 6)),
        "model_type": "MLPRegressor Autoencoder demo",
        "window_size": int(window_size),
        "mse_mean": float(round(float(reconstruction_mse.mean()), 6)),
        "mse_max": float(round(float(reconstruction_mse.max()), 6)),
        "threshold_policy": "Threshold MSE lấy từ reconstruction error trên train windows.",
        "note": "MSE cao nghĩa là model tái tạo window kém, có thể là anomaly."
    })

    joblib.dump(
        {"scaler": scaler, "autoencoder": ae, "window_size": window_size, "threshold": threshold},
        MODEL_DIR / "mlp_autoencoder_demo.joblib",
    )
    save_json(metrics, OUTPUT_DIR / "autoencoder_metrics.json")
    aligned.to_csv(OUTPUT_DIR / "autoencoder_test_predictions.csv", index=False)

    print("=== Neural Autoencoder demo metrics ===")
    print(json.dumps(metrics, indent=2, ensure_ascii=False))
    return metrics


if __name__ == "__main__":
    train_isolation_forest()
    train_neural_autoencoder_demo()