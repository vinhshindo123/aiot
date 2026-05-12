from __future__ import annotations

from datetime import datetime
from typing import Optional
import json
import os

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.data_utils import API_FEATURES, RAW_FEATURES, compute_anomaly_score, load_model_bundle

app = FastAPI(
    title="Lab 2 AIoT Air Quality Inference API",
    description="Demo deploy model cơ bản với dashboard: telemetry → CO prediction → decision/visualization.",
    version="lab2-airquality-v1",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cho phép tất cả origins (chỉ dùng cho development)
    allow_credentials=True,
    allow_methods=["*"],  # Cho phép tất cả methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Cho phép tất cả headers
)

app.mount("/static", StaticFiles(directory="frontend"), name="static")

MODEL_BUNDLE = load_model_bundle()
MODEL = MODEL_BUNDLE["model"]
TRAIN_STATS = MODEL_BUNDLE["train_stats"]
METRICS = MODEL_BUNDLE.get("metrics", {})

# Load datasets for visualization
try:
    CLEAN_DF = pd.read_csv("data/telemetry_clean.csv")
    DECISION_DF = pd.read_csv("outputs/decision_log.csv")
except:
    CLEAN_DF = None
    DECISION_DF = None


class AirQualityInput(BaseModel):
    location: Optional[str] = Field(default="station_center")  # Đổi thành Optional
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
async def root():
    return FileResponse("frontend/index.html")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "model_loaded": MODEL is not None,
        "model_version": MODEL_BUNDLE.get("model_version", "unknown"),
    }

@app.get("/metrics-data")
def get_metrics_data():
    """API endpoint để lấy metrics data cho dashboard"""
    return {
        "metrics": {
            "r2": METRICS.get("r2", 0),
            "rmse": METRICS.get("rmse", 0),
            "mae": METRICS.get("mae", 0),
            "mse": METRICS.get("mse", 0)
        },
        "total_samples": len(DECISION_DF) if DECISION_DF is not None else 0
    }


@app.get("/data-analysis")
def get_data_analysis():
    """API endpoint để lấy dữ liệu phân tích"""
    if CLEAN_DF is None or DECISION_DF is None:
        return {"error": "Data not available"}
    
    # Lấy dữ liệu cho biểu đồ
    co_dist = CLEAN_DF['CO_GT'].tolist()[:1000]  # Giới hạn 1000 điểm
    temp_dist = CLEAN_DF['Temperature'].tolist()[:1000]
    decision_counts = DECISION_DF['decision'].value_counts().to_dict()
    
    # Lấy dữ liệu cho biểu đồ predictions vs actual
    pred_actual_data = None
    if DECISION_DF is not None:
        last_n = min(100, len(DECISION_DF))
        pred_actual_data = {
            "actual": DECISION_DF['actual_co'].tail(last_n).tolist(),
            "predicted": DECISION_DF['co_prediction'].tail(last_n).tolist()
        }
    
    return {
        "co_distribution": co_dist,
        "temperature_distribution": temp_dist,
        "decision_distribution": decision_counts,
        "pred_actual": pred_actual_data
    }

@app.get("/model-info")
def model_info():
    return {
        "model_name": MODEL_BUNDLE.get("model_name"),
        "model_version": MODEL_BUNDLE.get("model_version"),
        "feature_cols": MODEL_BUNDLE.get("feature_cols"),
        "metrics": METRICS,
        "decision_outputs": [
            "CHECK_SENSOR_CALIBRATION",
            "AIR_QUALITY_HAZARDOUS",
            "AIR_QUALITY_POOR",
            "AIR_QUALITY_MODERATE",
            "AIR_QUALITY_GOOD",
        ],
    }


@app.get("/metrics-data")
def get_metrics_data():
    """API endpoint để lấy metrics data cho dashboard"""
    return {
        "metrics": METRICS,
        "total_samples": len(DECISION_DF) if DECISION_DF is not None else 0
    }


@app.get("/data-analysis")
def get_data_analysis():
    """API endpoint để lấy dữ liệu phân tích"""
    if CLEAN_DF is None or DECISION_DF is None:
        return {"error": "Data not available"}
    
    # Lấy dữ liệu cho biểu đồ
    co_dist = CLEAN_DF['CO_GT'].tolist()
    temp_dist = CLEAN_DF['Temperature'].tolist()
    decision_counts = DECISION_DF['decision'].value_counts().to_dict()
    
    # Lấy dữ liệu cho biểu đồ predictions vs actual
    pred_actual_data = None
    if DECISION_DF is not None:
        last_n = min(100, len(DECISION_DF))
        pred_actual_data = {
            "actual": DECISION_DF['actual_co'].tail(last_n).tolist(),
            "predicted": DECISION_DF['co_prediction'].tail(last_n).tolist()
        }
    
    return {
        "co_distribution": co_dist,
        "temperature_distribution": temp_dist,
        "decision_distribution": decision_counts,
        "pred_actual": pred_actual_data
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
    print(f"Received payload: {payload}")  # Debug log
    try:
        features = build_feature_row(payload)
        co_prediction = float(MODEL.predict(features[API_FEATURES])[0])
        air_quality_level = get_air_quality_level(co_prediction)
        
        result = {
            "predicted_co_concentration_mg_per_m3": round(co_prediction, 3),
            "air_quality_level": air_quality_level,
            "status": "success"
        }
        print(f"Prediction result: {result}")  # Debug log
        return result
    except Exception as e:
        print(f"Error in prediction: {e}")  # Debug log


@app.get("/static/{file_path:path}")
async def serve_static(file_path: str):
    """Phục vụ các file tĩnh"""
    return FileResponse(f"static/{file_path}")