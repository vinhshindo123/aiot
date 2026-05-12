from __future__ import annotations

import json
import math
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import zipfile
from io import BytesIO

import joblib
import numpy as np
import pandas as pd
import requests
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = PROJECT_ROOT / "models"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
FIGURES_DIR = OUTPUTS_DIR / "figures"

AIR_QUALITY_URL = (
    "https://archive.ics.uci.edu/static/public/360/air+quality.zip"
)

RAW_FEATURES = [
    "PT08.S1(CO)", "PT08.S2(NMHC)", "PT08.S3(NOx)", "PT08.S4(NO2)", "PT08.S5(O3)",
    "Temperature", "Relative_Humidity", "Absolute_Humidity"
]

CSV_COLUMNS = {
    "Date": "Date",
    "Time": "Time",
    "CO(GT)": "CO_GT",
    "PT08.S1(CO)": "PT08.S1(CO)",
    "NMHC(GT)": "NMHC(GT)",
    "C6H6(GT)": "C6H6(GT)",
    "PT08.S2(NMHC)": "PT08.S2(NMHC)",
    "NOx(GT)": "NOx(GT)",
    "PT08.S3(NOx)": "PT08.S3(NOx)",
    "NO2(GT)": "NO2(GT)",
    "PT08.S4(NO2)": "PT08.S4(NO2)",
    "PT08.S5(O3)": "PT08.S5(O3)",
    "T": "Temperature",
    "RH": "Relative_Humidity",
    "AH": "Absolute_Humidity"
}

API_FEATURES = RAW_FEATURES + ["hour", "dayofweek"]
TARGET_COL = "CO_GT"


def make_dirs() -> None:
    for d in [DATA_DIR, MODELS_DIR, OUTPUTS_DIR, FIGURES_DIR]:
        d.mkdir(parents=True, exist_ok=True)


def generate_air_quality_fallback(n_samples: int = 5000) -> pd.DataFrame:
    """Generate synthetic air quality data for testing."""
    np.random.seed(42)
    timestamps = pd.date_range("2024-01-01", periods=n_samples, freq="H")
    
    # Simulate realistic patterns
    hour_of_day = timestamps.hour
    temp = 15 + 10 * np.sin(2 * np.pi * hour_of_day / 24) + np.random.normal(0, 2, n_samples)
    rh = 60 + 20 * np.sin(2 * np.pi * hour_of_day / 24 + np.pi) + np.random.normal(0, 5, n_samples)
    ah = (rh / 100) * 0.006 * np.exp(17.27 * temp / (temp + 237.3))  # Simple approximation
    
    # Sensor responses
    co_sensor = 1000 + 500 * np.sin(2 * np.pi * hour_of_day / 24) + np.random.normal(0, 100, n_samples)
    co_target = 2 + 1.5 * np.sin(2 * np.pi * hour_of_day / 24) + np.random.normal(0, 0.5, n_samples)
    
    df = pd.DataFrame({
        "DateTime": timestamps,
        "PT08.S1(CO)": np.clip(co_sensor, 500, 2000),
        "PT08.S2(NMHC)": np.clip(co_sensor * 0.8 + np.random.normal(0, 50, n_samples), 400, 1600),
        "PT08.S3(NOx)": np.clip(co_sensor * 0.6 + np.random.normal(0, 80, n_samples), 300, 1500),
        "PT08.S4(NO2)": np.clip(co_sensor * 0.5 + np.random.normal(0, 70, n_samples), 200, 1200),
        "PT08.S5(O3)": np.clip(800 - co_sensor * 0.3 + np.random.normal(0, 100, n_samples), 100, 1500),
        "Temperature": np.clip(temp, 0, 40),
        "Relative Humidity": np.clip(rh, 20, 95),
        "Absolute Humidity": np.clip(ah, 5, 25),
        "CO_GT": np.clip(co_target, 0.5, 5)
    })
    
    return df


def download_air_quality_dataset(timeout: int = 30) -> Tuple[bool, List[str]]:
    """Download Air Quality dataset from UCI repository."""
    make_dirs()
    raw_dir = DATA_DIR / "air_quality"
    raw_dir.mkdir(parents=True, exist_ok=True)
    messages = []
    
    csv_path = raw_dir / "AirQualityUCI.csv"
    
    if csv_path.exists() and csv_path.stat().st_size > 10000:
        messages.append("OK: AirQualityUCI.csv already exists.")
        return True, messages
    
    try:
        print(f"Downloading from {AIR_QUALITY_URL}...")
        response = requests.get(AIR_QUALITY_URL, timeout=timeout)
        response.raise_for_status()
        
        with zipfile.ZipFile(BytesIO(response.content)) as z:
            z.extractall(raw_dir)
        
        if not csv_path.exists():
            # Tìm file CSV trong thư mục
            csv_files = list(raw_dir.glob("*.csv"))
            if csv_files:
                csv_path = csv_files[0]
            else:
                raise FileNotFoundError("No CSV file found after extraction.")
        
        messages.append(f"Downloaded and extracted dataset -> {csv_path}")
        return True, messages
        
    except Exception as exc:
        messages.append(f"WARNING: Could not download dataset: {exc}")
        return False, messages

def load_and_preprocess_air_quality(csv_path: Path) -> pd.DataFrame:
    """Load Air Quality CSV with proper preprocessing."""
    # Đọc file với separator là ; và decimal là ,
    df = pd.read_csv(csv_path, sep=";", decimal=",", na_values=-200)
    
    # Đổi tên cột
    df = df.rename(columns=CSV_COLUMNS)
    
    # Gộp Date và Time thành datetime
    df["DateTime"] = pd.to_datetime(df["Date"] + " " + df["Time"], format="%d/%m/%Y %H.%M.%S", errors="coerce")
    
    # Chỉ lấy các cột cần thiết
    keep_cols = ["DateTime"] + RAW_FEATURES + [TARGET_COL]
    available_cols = [col for col in keep_cols if col in df.columns]
    df = df[available_cols]
    
    # Drop rows với DateTime bị lỗi
    df = df.dropna(subset=["DateTime"])
    
    return df

def ensure_dataset(prefer_public: bool = True) -> Tuple[pd.DataFrame, Dict]:
    """Load Air Quality dataset if available."""
    make_dirs()
    status = {
        "dataset_source": None,
        "messages": [],
    }
    
    if prefer_public and os.getenv("LAB2_OFFLINE", "0") != "1":
        ok, messages = download_air_quality_dataset(timeout=30)
        status["messages"].extend(messages)
        
        if ok:
            csv_path = DATA_DIR / "air_quality" / "AirQualityUCI.csv"
            if csv_path.exists():
                df = load_and_preprocess_air_quality(csv_path)
                status["dataset_source"] = "UCI Air Quality Dataset"
                return df, status
    
    # Fallback: tạo dữ liệu mô phỏng chất lượng không khí
    fallback_df = generate_air_quality_fallback()
    status["dataset_source"] = "Generated fallback air quality dataset"
    status["messages"].append("Using generated fallback data for air quality.")
    return fallback_df, status


def check_schema(df: pd.DataFrame) -> Dict:
    required_cols = ["DateTime"] + RAW_FEATURES + [TARGET_COL]
    missing = [c for c in required_cols if c not in df.columns]
    duplicated_rows = int(df.duplicated().sum())
    result = {
        "required_columns": required_cols,
        "missing_columns": missing,
        "duplicated_rows": duplicated_rows,
        "n_rows": int(len(df)),
        "n_columns": int(df.shape[1]),
    }
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    return result


def clean_iot_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
    """Clean Air Quality data."""
    df = df.copy()
    before_rows = len(df)
    
    # Parse timestamp
    if "DateTime" in df.columns:
        df["timestamp"] = df["DateTime"]
    elif "timestamp" not in df.columns:
        df["timestamp"] = pd.to_datetime(df.get("Date", pd.NaT), errors="coerce")
    
    bad_timestamp = int(df["timestamp"].isna().sum())
    df = df.dropna(subset=["timestamp"])
    
    # Remove duplicates
    duplicate_rows = int(df.duplicated().sum())
    df = df.drop_duplicates()
    duplicate_timestamps = int(df.duplicated(subset=["timestamp"]).sum())
    df = df.drop_duplicates(subset=["timestamp"], keep="first")
    
    # Convert numeric columns
    for col in RAW_FEATURES + [TARGET_COL]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    
    # Outlier handling for air quality (realistic bounds)
    rules = {
        "PT08.S1(CO)": (300, 3000),
        "PT08.S2(NMHC)": (200, 2500),
        "PT08.S3(NOx)": (200, 2500),
        "PT08.S4(NO2)": (150, 2000),
        "PT08.S5(O3)": (50, 2000),
        "Temperature": (-10, 50),
        "Relative Humidity": (0, 100),
        "Absolute Humidity": (0, 50),
    }
    
    outlier_counts = {}
    for col, (lo, hi) in rules.items():
        if col in df.columns:
            mask = (df[col] < lo) | (df[col] > hi)
            outlier_counts[col] = int(mask.sum())
            df.loc[mask, col] = np.nan
    
    missing_before_fill = {col: int(df[col].isna().sum()) for col in RAW_FEATURES if col in df.columns}
    
    # Sort by time and interpolate
    df = df.sort_values("timestamp").reset_index(drop=True)
    for col in RAW_FEATURES:
        if col in df.columns:
            df[col] = df[col].interpolate(method="linear", limit_direction="both")
            df[col] = df[col].ffill().bfill()
    
    # Target column handling (regression, not binary)
    if TARGET_COL in df.columns:
        df[TARGET_COL] = df[TARGET_COL].fillna(df[TARGET_COL].median())
    
    after_rows = len(df)
    report = {
        "before_rows": before_rows,
        "after_rows": after_rows,
        "removed_rows": before_rows - after_rows,
        "bad_timestamp_rows": bad_timestamp,
        "duplicate_rows": duplicate_rows,
        "duplicate_timestamps": duplicate_timestamps,
        "outlier_counts": outlier_counts,
        "missing_before_fill": missing_before_fill,
    }
    return df, report

def create_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create time-based features for air quality data."""
    df = df.copy()
    if "timestamp" not in df.columns:
        df["timestamp"] = df.get("DateTime", pd.NaT)
    
    df["hour"] = df["timestamp"].dt.hour.astype(int)
    df["dayofweek"] = df["timestamp"].dt.dayofweek.astype(int)
    
    # Rolling features for sensor data
    for sensor in ["PT08.S1(CO)", "PT08.S2(NMHC)", "PT08.S3(NOx)"]:
        if sensor in df.columns:
            df[f"{sensor}_rolling_6h"] = df[sensor].rolling(window=6, min_periods=1).mean()
    
    return df

def time_train_test_split(df: pd.DataFrame, test_ratio: float = 0.25) -> Tuple[pd.DataFrame, pd.DataFrame]:
    df = df.sort_values("timestamp").reset_index(drop=True)
    split_idx = int(len(df) * (1 - test_ratio))
    train_df = df.iloc[:split_idx].copy()
    test_df = df.iloc[split_idx:].copy()
    return train_df, test_df


def compute_train_stats(train_df: pd.DataFrame) -> Dict:
    stats = {}
    for col in RAW_FEATURES:
        std = float(train_df[col].std())
        if std == 0 or math.isnan(std):
            std = 1.0
        stats[col] = {"mean": float(train_df[col].mean()), "std": std}
    return stats


def compute_anomaly_score(row_or_df, stats: Dict) -> np.ndarray:
    df = pd.DataFrame(row_or_df)
    scores = []
    for col in RAW_FEATURES:
        mean = stats[col]["mean"]
        std = stats[col]["std"] or 1.0
        scores.append(((df[col].astype(float) - mean).abs() / std).to_numpy())
    if not scores:
        return np.zeros(len(df))
    return np.nanmax(np.vstack(scores), axis=0)


def train_baseline_model(train_df: pd.DataFrame) -> Pipeline:
    """Train regression model for air quality prediction."""
    model = Pipeline(steps=[
        ("scaler", StandardScaler()),
        ("regressor", LinearRegression()),  # Changed from LogisticRegression
    ])
    model.fit(train_df[API_FEATURES], train_df[TARGET_COL])
    return model

def evaluate_model(model: Pipeline, test_df: pd.DataFrame) -> Dict:
    """Evaluate regression model with regression metrics."""
    y_true = test_df[TARGET_COL].values
    y_pred = model.predict(test_df[API_FEATURES])
    
    metrics = {
        "mse": float(mean_squared_error(y_true, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "r2": float(r2_score(y_true, y_pred)),
    }
    return metrics


def decision_from_outputs(co_prediction: float, anomaly_score: float, temperature: float, humidity: float) -> Dict:
    """Decision logic cho Air Quality warning system"""
    is_anomaly = bool(anomaly_score >= 3.0)
    
    # Ngưỡng chất lượng không khí dựa trên WHO guidelines
    # CO: 4 mg/m³ cho 24h, 10 mg/m³ cho 8h
    co_levels = {
        "good": (0, 2),
        "moderate": (2, 4),
        "poor": (4, 10),
        "hazardous": (10, float('inf'))
    }
    
    if is_anomaly:
        decision = "CHECK_SENSOR_CALIBRATION"
        command_hint = "SENSOR_MAINTENANCE_REQUIRED"
        safety_note = "Dữ liệu cảm biến bất thường, cần kiểm tra thiết bị"
    elif co_prediction > 10:
        decision = "AIR_QUALITY_HAZARDOUS"
        command_hint = "EVACUATE_AREA"
        safety_note = "Nồng độ CO nguy hiểm! Cần sơ tán khẩn cấp"
    elif co_prediction > 4:
        decision = "AIR_QUALITY_POOR"
        command_hint = "ACTIVATE_VENTILATION"
        safety_note = "Chất lượng không khí kém, cần thông gió"
    elif co_prediction > 2:
        decision = "AIR_QUALITY_MODERATE"
        command_hint = "MONITOR_CONTINUOUSLY"
        safety_note = "Chất lượng không khí trung bình, tiếp tục theo dõi"
    else:
        decision = "AIR_QUALITY_GOOD"
        command_hint = "NORMAL_OPERATION"
        safety_note = "Chất lượng không khí tốt, duy trì hoạt động bình thường"
    
    return {
        "co_prediction": co_prediction,
        "is_anomaly": is_anomaly,
        "decision": decision,
        "command_hint": command_hint,
        "safety_note": safety_note,
        "air_quality_level": get_air_quality_level(co_prediction)  # Cần thêm hàm này
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

def make_decision_log(model: Pipeline, test_df: pd.DataFrame, train_stats: Dict, n_rows: int = 200) -> pd.DataFrame:
    sample = test_df.copy().tail(n_rows).reset_index(drop=True)
    co_predictions = model.predict(sample[API_FEATURES])
    anomaly_score = compute_anomaly_score(sample[RAW_FEATURES], train_stats)

    rows = []
    for i, r in sample.iterrows():
        d = decision_from_outputs(
            co_prediction=float(co_predictions[i]),
            anomaly_score=float(anomaly_score[i]),
            temperature=float(r.get("Temperature", 0)),
            humidity=float(r.get("Relative_Humidity", 0))
        )
        rows.append({
            "timestamp": r["timestamp"],
            "PT08_S1_CO": r.get("PT08.S1(CO)", 0),
            "PT08_S2_NMHC": r.get("PT08.S2(NMHC)", 0),
            "PT08_S3_NOx": r.get("PT08.S3(NOx)", 0),
            "Temperature": r.get("Temperature", 0),
            "Relative_Humidity": r.get("Relative_Humidity", 0),
            "co_prediction": round(float(co_predictions[i]), 4),
            "actual_co": float(r[TARGET_COL]),
            "anomaly_score": round(float(anomaly_score[i]), 4),
            "is_anomaly": d["is_anomaly"],
            "decision": d["decision"],
            "command_hint": d["command_hint"],
            "safety_note": d["safety_note"],
            "air_quality_level": d["air_quality_level"]
        })
    return pd.DataFrame(rows)


def save_artifacts(model: Pipeline, feature_cols: List[str], train_stats: Dict, metrics: Dict, dataset_status: Dict) -> None:
    make_dirs()
    bundle = {
        "model": model,
        "feature_cols": feature_cols,
        "raw_features": RAW_FEATURES,
        "train_stats": train_stats,
        "metrics": metrics,
        "dataset_status": dataset_status,
        "model_name": "air_quality_linear_regression",
        "model_version": "lab2-airquality-v1",
    }
    joblib.dump(bundle, MODELS_DIR / "air_quality_model.joblib")
    (OUTPUTS_DIR / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUTPUTS_DIR / "dataset_status.json").write_text(json.dumps(dataset_status, ensure_ascii=False, indent=2), encoding="utf-8")


def load_model_bundle(model_path: Path | None = None) -> Dict:
    if model_path is None:
        model_path = MODELS_DIR / "air_quality_model.joblib"
    if not model_path.exists():
        raise FileNotFoundError(
            f"Model not found: {model_path}. Run the notebook first or run: python src/run_training_pipeline.py"
        )
    return joblib.load(model_path)
