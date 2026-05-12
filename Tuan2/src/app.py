from __future__ import annotations

from datetime import datetime
from typing import Optional

import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel, Field

from src.data_utils import API_FEATURES, RAW_FEATURES, compute_anomaly_score, load_model_bundle

app = FastAPI(
    title="Lab 2 AIoT Air Quality Inference API",
    description="Demo deploy model cơ bản: telemetry -> CO prediction -> air quality decision output.",
    version="lab2-airquality-v1",
)

MODEL_BUNDLE = load_model_bundle()
MODEL = MODEL_BUNDLE["model"]
TRAIN_STATS = MODEL_BUNDLE["train_stats"]
METRICS = MODEL_BUNDLE.get("metrics", {})


class AirQualityInput(BaseModel):
    location: str = Field(default="station_center")
    timestamp: Optional[str] = None
    PT08_S1_CO: float = Field(..., ge=0, le=3000, description="CO sensor response")
    PT08_S2_NMHC: float = Field(..., ge=0, le=2500, description="NMHC sensor response")
    PT08_S3_NOx: float = Field(..., ge=0, le=2500, description="NOx sensor response")
    PT08_S4_NO2: float = Field(..., ge=0, le=2000, description="NO2 sensor response")
    PT08_S5_O3: float = Field(..., ge=0, le=2000, description="O3 sensor response")
    Temperature: float = Field(..., ge=-10, le=50)
    Relative_Humidity: float = Field(..., ge=0, le=100)
    Absolute_Humidity: float = Field(..., ge=0, le=50)


@app.get("/")
def root():
    return {
        "message": "Lab 2 AIoT model deployment demo is running.",
        "try": ["/health", "/model-info", "/docs", "/predict"],
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "model_loaded": MODEL is not None,
        "model_version": MODEL_BUNDLE.get("model_version", "unknown"),
    }


@app.get("/model-info")
def model_info():
    return {
        "model_name": MODEL_BUNDLE.get("model_name"),
        "model_version": MODEL_BUNDLE.get("model_version"),
        "feature_cols": MODEL_BUNDLE.get("feature_cols"),
        "metrics": METRICS,
        "decision_outputs": [  # Cập nhật decision mới
            "CHECK_SENSOR_CALIBRATION",
            "AIR_QUALITY_HAZARDOUS",
            "AIR_QUALITY_POOR",
            "AIR_QUALITY_MODERATE",
            "AIR_QUALITY_GOOD",
        ],
    }

def get_air_quality_level(co_value: float) -> str:
    if co_value <= 2:
        return "Good"
    elif co_value <= 4:
        return "Moderate"
    elif co_value <= 10:
        return "Poor"
    else:
        return "Hazardous"

def build_feature_row(payload: AirQualityInput) -> pd.DataFrame:
    ts = pd.to_datetime(payload.timestamp) if payload.timestamp else pd.Timestamp(datetime.now())
    row = {
        "PT08.S1(CO)": payload.PT08_S1_CO,
        "PT08.S2(NMHC)": payload.PT08_S2_NMHC,
        "PT08.S3(NOx)": payload.PT08_S3_NOx,
        "PT08.S4(NO2)": payload.PT08_S4_NO2,
        "PT08.S5(O3)": payload.PT08_S5_O3,
        "Temperature": payload.Temperature,
        "Relative_Humidity": payload.Relative_Humidity,
        "Absolute_Humidity": payload.Absolute_Humidity,
        "hour": int(ts.hour),
        "dayofweek": int(ts.dayofweek),
    }
    return pd.DataFrame([row])


@app.post("/predict")
def predict(payload: AirQualityInput):
    features = build_feature_row(payload)
    co_prediction = float(MODEL.predict(features[API_FEATURES])[0])
    air_quality_level = get_air_quality_level(co_prediction)
    
    return {
        "predicted_co_concentration_mg_per_m3": round(co_prediction, 3),
        "air_quality_level": air_quality_level,
        "status": "success"
    }