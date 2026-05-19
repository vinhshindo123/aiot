from __future__ import annotations

import json
import time
from pathlib import Path

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.utils import (
    DATA_DIR, MODEL_DIR, OUTPUT_DIR,
    add_time_features, event_type_from_row, explanation_from_row,
    normalize_scores, severity_from_score, decision_from_severity, infer_sensor_columns
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_BUNDLE_PATH = MODEL_DIR / "anomaly_model_bundle_iforest_v2.joblib"
DASHBOARD_HTML = PROJECT_ROOT / "src" / "static" / "dashboard.html"

app = FastAPI(
    title="Hydroponics Anomaly Detection API",
    description="API for hydroponics system anomaly detection using Isolation Forest",
    version="3.0.0",
)

# Thêm CORS middleware - Đây là phần QUAN TRỌNG để fix lỗi
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cho phép tất cả origins (hoặc có thể chỉ định cụ thể)
    allow_credentials=True,
    allow_methods=["*"],  # Cho phép tất cả methods (GET, POST, PUT, DELETE...)
    allow_headers=["*"],  # Cho phép tất cả headers
)

model_bundle = None
if MODEL_BUNDLE_PATH.exists():
    model_bundle = joblib.load(MODEL_BUNDLE_PATH)


class TelemetryPoint(BaseModel):
    timestamp: str = Field(..., examples=["2024-01-01 05:00:00"])
    node_id: str = Field(..., examples=["NODE_01"])
    temp: float | None = Field(None, examples=[23.5])
    humi: float | None = Field(None, examples=[48.2])
    ph: float | None = Field(None, examples=[6.2])
    ec: float | None = Field(None, examples=[1200])
    water_temp: float | None = Field(None, examples=[22.5])
    light: float | None = Field(None, examples=[145.0])
    co2: float | None = Field(None, examples=[450])
    soil: float | None = Field(None, examples=[31.7])  # For backward compatibility


class AnomalyRequest(BaseModel):
    history: list[TelemetryPoint] = Field(
        ...,
        description="Danh sách điểm measurement lịch sử gần nhất. Nên gửi ít nhất 36 điểm để feature rolling ổn định.",
    )


@app.get("/", response_class=HTMLResponse)
def dashboard_page():
    if not DASHBOARD_HTML.exists():
        raise HTTPException(status_code=500, detail="Dashboard chưa được cài đặt.")
    return HTMLResponse(DASHBOARD_HTML.read_text(encoding="utf-8"))


@app.get("/history-sample")
def history_sample():
    file_path = DATA_DIR / "measurements.csv"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Dữ liệu mẫu chưa tồn tại. Hãy chạy python src/download_data.py --source <path_to_csv>")
    df = pd.read_csv(file_path)
    df["created_at"] = pd.to_datetime(df["created_at"])
    df = df.sort_values("created_at").tail(60)
    
    # Return available columns
    cols = ['node_id', 'created_at']
    cols.extend([c for c in ['temp', 'humi', 'ph', 'ec', 'water_temp', 'light', 'co2'] if c in df.columns])
    return {"history": df[cols].to_dict(orient="records")}


@app.get("/health")
def health():
    return {
        "status": "ok",
        "model_loaded": model_bundle is not None,
        "model_bundle_path": str(MODEL_BUNDLE_PATH),
        "dataset": "Hydroponics",
    }


@app.get("/model-info")
def model_info():
    metrics = {}
    metrics_path = OUTPUT_DIR / "iforest_metrics.json"
    if metrics_path.exists():
        metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    if model_bundle is None:
        return {
            "model_loaded": False,
            "message": "Model chưa train. Chạy python src/train_anomaly.py để tạo model.",
        }
    return {
        "model_loaded": True,
        "model_name": "IsolationForest Hydroponics Anomaly Detector",
        "model_version": model_bundle.get("model_version", "unknown"),
        "input": "Danh sách measurement với các sensor: temp, humi, ph, ec, water_temp, light, co2",
        "output": "anomaly_score, is_anomaly, threshold_used, event_type, severity, decision.",
        "threshold": round(float(model_bundle.get("threshold", 0.55)), 4),
        "feature_columns": model_bundle.get("feature_columns", []),
        "metrics": metrics,
    }


@app.post("/detect-anomaly")
def detect_anomaly(payload: AnomalyRequest):
    if model_bundle is None:
        raise HTTPException(status_code=503, detail="Model chưa được train. Chạy python src/train_anomaly.py")
    
    start = time.time()
    pipeline = model_bundle["pipeline"]
    feature_columns = model_bundle.get("feature_columns", [])
    threshold = float(model_bundle.get("threshold", 0.55))
    score_min = float(model_bundle.get("score_min", 0.0))
    score_max = float(model_bundle.get("score_max", 1.0))

    # Convert to DataFrame
    df = pd.DataFrame([point.model_dump() for point in payload.history])
    df["created_at"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("created_at").reset_index(drop=True)
    
    # Fill NaN values with forward fill then median
    df = df.fillna(method='ffill').fillna(df.median())
    
    # Add time features
    df = add_time_features(df)
    latest = df.iloc[[-1]].copy()

    # If model bundle didn't store feature columns, infer from processed frame
    if not feature_columns:
        feature_columns = infer_sensor_columns(latest)
    
    # Ensure all feature columns exist
    available_features = [c for c in feature_columns if c in latest.columns]
    if len(available_features) != len(feature_columns):
        missing = set(feature_columns) - set(available_features)
        print(f"Warning: Missing features: {missing}")

    # Calculate anomaly score
    raw_score = -pipeline.named_steps["detector"].score_samples(
        pipeline.named_steps["scaler"].transform(latest[available_features])
    )[0]
    score = float(normalize_scores([raw_score], score_min, score_max)[0])
    is_anomaly = score >= threshold
    
    latest_row = latest.iloc[-1]
    severity = severity_from_score(score, threshold=threshold)
    event_type = event_type_from_row(latest_row) if is_anomaly else "NORMAL_OPERATION"
    decision = decision_from_severity(severity) if is_anomaly else "NO_ALERT"
    explanation = explanation_from_row(latest_row) if is_anomaly else "Measurement nằm trong ngưỡng vận hành bình thường."
    
    warnings = []
    if len(payload.history) < 36:
        warnings.append("history có dưới 36 điểm; feature rolling có thể chưa ổn định.")

    # Build response with available sensors
    sensor_values = {}
    for sensor in ['temp', 'humi', 'ph', 'ec', 'water_temp', 'light', 'co2', 'soil']:
        if sensor in latest_row.index and pd.notna(latest_row[sensor]):
            sensor_values[sensor] = float(latest_row[sensor])

    return {
        "model_output": {
            "raw_score": round(float(raw_score), 6),
            "anomaly_score": round(score, 4),
            "threshold_used": round(threshold, 4),
            "is_anomaly": bool(is_anomaly),
            "model_version": model_bundle.get("model_version", "iforest_v2"),
        },
        "event": {
            "node_id": str(latest_row["node_id"]),
            "timestamp": str(latest_row["created_at"]),
            **sensor_values,
            "severity": severity,
            "decision": decision,
            "event_type": event_type,
            "explanation": explanation,
            "safety_note": "Không điều khiển tự động ngay lập tức; xác minh bằng rule an toàn.",
        },
        "api_check": {
            "latency_ms": round((time.time() - start) * 1000, 2),
            "input_points": len(payload.history),
            "warnings": warnings,
        },
    }