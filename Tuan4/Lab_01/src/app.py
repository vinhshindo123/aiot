from __future__ import annotations

import json
import time
from typing import Any
from pathlib import Path

import joblib
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel, Field, ConfigDict

from Lab_01.src.utils import (
    MODEL_DIR,
    OUTPUT_DIR,
    DATE_COL,
    FEATURE_COLUMNS,
    HORIZON_MINUTES,
    make_supervised_frame,
    fill_missing_for_api,
    risk_from_prediction,
    recommendation_from_risk,
    reason_from_risk,
)

MODEL_BUNDLE_PATH = MODEL_DIR / "forecast_model_bundle_v1.joblib"
METRICS_PATH = OUTPUT_DIR / "forecast_metrics.json"

app = FastAPI(
    title="LAB 4 AIoT Forecasting API",
    description="Forecast NODE_03 temperature and return risk_level with recommendation.",
    version="1.0.0",
)

model_bundle = None
if MODEL_BUNDLE_PATH.exists():
    model_bundle = joblib.load(MODEL_BUNDLE_PATH)


class TelemetryPoint(BaseModel):
    model_config = ConfigDict(extra="allow")

    created_at: str = Field(..., examples=["2026-03-16 18:37:28+00:00"])
    temp: float | None = None
    humi: float | None = None
    soil: float | None = None
    light: float | None = None
    cmd_count: float | None = None
    cmd_failure_rate: float | None = None
    cmd_timeout_count: float | None = None
    rssi_mean: float | None = None
    rssi_min: float | None = None
    rssi_std: float | None = None
    node_id: str | None = None


class ForecastRequest(BaseModel):
    history: list[TelemetryPoint] = Field(
        ...,
        description="Recent telemetry history (raw NODE_03 measurements).",
    )


def _dump_model(point: TelemetryPoint) -> dict[str, Any]:
    if hasattr(point, "model_dump"):
        return point.model_dump()
    return point.dict()


@app.get("/health")
def health():
    return {
        "status": "ok",
        "model_loaded": model_bundle is not None,
        "model_bundle_path": str(MODEL_BUNDLE_PATH),
    }


@app.get("/model-info")
def model_info():
    metrics = {}
    if METRICS_PATH.exists():
        metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8"))

    if model_bundle is None:
        return {
            "model_loaded": False,
            "message": "Chưa có model. Hãy chạy: python src/train_forecast.py",
        }

    return {
        "model_loaded": True,
        "model_name": type(model_bundle["model"]).__name__,
        "model_version": model_bundle.get("model_version", "unknown"),
        "target": model_bundle.get("target", "target_temp_next_1"),
        "forecast_horizon_minutes": model_bundle.get("forecast_horizon_minutes", HORIZON_MINUTES),
        "input": "history of NODE_03 raw telemetry rows",
        "output": "predicted_value, risk_level, recommendation, safety_note",
        "feature_count": len(model_bundle.get("feature_columns", FEATURE_COLUMNS)),
        "risk_thresholds": model_bundle.get("risk_thresholds", {}),
        "metrics": metrics,
    }


@app.post("/forecast")
def forecast(payload: ForecastRequest):
    if model_bundle is None:
        return {"error": "Model chưa được train. Hãy chạy: python src/train_forecast.py"}

    start = time.time()
    warnings = []
    if len(payload.history) < 12:
        warnings.append("history có ít hơn 12 điểm; lag/rolling feature có thể chưa ổn định.")

    rows = [_dump_model(p) for p in payload.history]
    df = pd.DataFrame(rows)
    if DATE_COL not in df.columns:
        return {"error": f"Payload cần có cột {DATE_COL} trong từng telemetry point."}

    df = df.sort_values(DATE_COL).reset_index(drop=True)
    df = fill_missing_for_api(df, model_bundle.get("raw_medians", {}))
    features_df = make_supervised_frame(df, include_target=False)
    latest = features_df.iloc[[-1]].copy()

    feature_columns = model_bundle.get("feature_columns", FEATURE_COLUMNS)
    for col in feature_columns:
        if col not in latest.columns:
            latest[col] = float(model_bundle.get("feature_medians", {}).get(col, 0.0))

    X = latest[feature_columns].replace([float("inf"), float("-inf")], pd.NA)
    X = X.fillna(model_bundle.get("feature_medians", {})).fillna(0.0)

    model = model_bundle["model"]
    predicted_value = float(model.predict(X)[0])
    thresholds = model_bundle.get("risk_thresholds", {"warning": 27.2, "high": 27.8, "critical": 28.2})
    risk_level = risk_from_prediction(predicted_value, thresholds)
    recommendation = recommendation_from_risk(risk_level)

    return {
        "model_output": {
            "target": model_bundle.get("target", "target_temp_next_1"),
            "forecast_horizon_minutes": model_bundle.get("forecast_horizon_minutes", HORIZON_MINUTES),
            "predicted_value": round(predicted_value, 4),
            "unit": "°C",
            "model_version": model_bundle.get("model_version", "forecast_v1"),
        },
        "evaluation_hint": {
            "metrics_file": "outputs/forecast_metrics.json",
            "best_model_mae": model_bundle.get("metrics_by_model", {}).get(model_bundle.get("model_version", ""), {}).get("mae"),
            "best_model_rmse": model_bundle.get("metrics_by_model", {}).get(model_bundle.get("model_version", ""), {}).get("rmse"),
        },
        "decision": {
            "risk_level": risk_level,
            "recommendation": recommendation,
            "reason": reason_from_risk(predicted_value, thresholds),
            "safety_note": "Forecast là tín hiệu khuyến nghị, không phải lệnh điều khiển tự động.",
        },
        "api_check": {
            "latency_ms": round((time.time() - start) * 1000, 2),
            "input_points": len(payload.history),
            "warnings": warnings,
        },
    }
