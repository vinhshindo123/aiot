from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
MODEL_DIR = PROJECT_ROOT / "models"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
FIGURE_DIR = PROJECT_ROOT / "figures"

DATA_DIR.mkdir(exist_ok=True)
MODEL_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
FIGURE_DIR.mkdir(exist_ok=True)

DATASET_PATH = DATA_DIR / "lab4_forecast_NODE03_augmented.csv"
DATE_COL = "created_at"
NODE_ID_COL = "node_id"
TARGET_COL = "target_temp_next_1"
TARGET_COLUMNS = [
    "target_temp_next_1",
    "target_temp_next_2",
    "target_temp_next_3",
    "target_temp_next_5",
]
HORIZON_STEPS = 1
HORIZON_MINUTES = 5
MODEL_VERSION = "forecast_v1"

RAW_FEATURE_COLUMNS = [
    "temp", "humi", "light", "soil",
    "temp_lag_1", "temp_lag_2", "temp_lag_3",
    "humi_lag_1", "humi_lag_2",
    "light_lag_1",
    "soil_lag_1", "soil_lag_2",
    "temp_rolling_mean_3", "temp_rolling_mean_5",
    "temp_rolling_std_3", "temp_rolling_std_5",
    "humi_rolling_mean_3",
    "soil_rolling_mean_3", "soil_rolling_mean_5",
    "soil_rolling_min_3", "soil_rolling_max_3",
    "hour", "minute", "day_of_week", "is_weekend", "hour_sin", "hour_cos",
    "temp_delta_1", "temp_delta_3",
    "humi_delta_1", "soil_delta_1",
    "temp_humi_product", "temp_soil_ratio", "humi_soil_product", "temp_light_ratio",
    "cmd_count", "cmd_failure_rate", "cmd_timeout_count",
    "rssi_mean", "rssi_min", "rssi_std",
]
FEATURE_COLUMNS = RAW_FEATURE_COLUMNS.copy()
ALL_COLUMNS = [DATE_COL, NODE_ID_COL] + FEATURE_COLUMNS + TARGET_COLUMNS


def save_json(obj, path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def dataset_candidates() -> list[Path]:
    return [DATASET_PATH]


def find_dataset_path() -> Path:
    for path in dataset_candidates():
        if path.exists():
            return path
    raise FileNotFoundError(
        f"Không tìm thấy dataset. Hãy đặt file '{DATASET_PATH.name}' vào thư mục data/."
    )


def load_dataset(path: str | Path | None = None) -> pd.DataFrame:
    if path is None:
        path = find_dataset_path()
    path = Path(path)
    df = pd.read_csv(path)
    if DATE_COL not in df.columns:
        raise ValueError(f"Dataset phải có cột `{DATE_COL}`.")
    if TARGET_COL not in df.columns:
        raise ValueError(f"Dataset phải có cột target `{TARGET_COL}`.")

    df[DATE_COL] = pd.to_datetime(df[DATE_COL], utc=True, errors="coerce")
    df = df.sort_values(DATE_COL).drop_duplicates(DATE_COL).reset_index(drop=True)

    for col in FEATURE_COLUMNS + TARGET_COLUMNS + [NODE_ID_COL]:
        if col == NODE_ID_COL:
            if col not in df.columns:
                df[col] = ""
            continue
        if col not in df.columns:
            df[col] = np.nan
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df[[DATE_COL, NODE_ID_COL] + FEATURE_COLUMNS + TARGET_COLUMNS]


def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if DATE_COL not in out.columns:
        raise ValueError(f"Dữ liệu phải có cột {DATE_COL} để tạo time features.")
    out[DATE_COL] = pd.to_datetime(out[DATE_COL], utc=True, errors="coerce")
    out = out.sort_values(DATE_COL).reset_index(drop=True)
    out["hour"] = out[DATE_COL].dt.hour
    out["minute"] = out[DATE_COL].dt.minute
    out["day_of_week"] = out[DATE_COL].dt.dayofweek
    out["is_weekend"] = (out["day_of_week"] >= 5).astype(int)
    out["hour_sin"] = np.sin(2 * np.pi * out["hour"] / 24.0)
    out["hour_cos"] = np.cos(2 * np.pi * out["hour"] / 24.0)
    return out


def add_lag_rolling_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in ["temp", "humi", "soil", "light"]:
        if col not in out.columns:
            continue
        for lag in [1, 2, 3]:
            out[f"{col}_lag_{lag}"] = out[col].shift(lag)

    if "temp" in out.columns:
        out["temp_rolling_mean_3"] = out["temp"].rolling(window=3, min_periods=3).mean()
        out["temp_rolling_mean_5"] = out["temp"].rolling(window=5, min_periods=5).mean()
        out["temp_rolling_std_3"] = out["temp"].rolling(window=3, min_periods=3).std()
        out["temp_rolling_std_5"] = out["temp"].rolling(window=5, min_periods=5).std()

    if "humi" in out.columns:
        out["humi_rolling_mean_3"] = out["humi"].rolling(window=3, min_periods=3).mean()

    if "soil" in out.columns:
        out["soil_rolling_mean_3"] = out["soil"].rolling(window=3, min_periods=3).mean()
        out["soil_rolling_mean_5"] = out["soil"].rolling(window=5, min_periods=5).mean()
        out["soil_rolling_min_3"] = out["soil"].rolling(window=3, min_periods=3).min()
        out["soil_rolling_max_3"] = out["soil"].rolling(window=3, min_periods=3).max()

    if "temp" in out.columns and "temp_lag_1" in out.columns:
        out["temp_delta_1"] = out["temp"] - out["temp_lag_1"]
    if "temp" in out.columns and "temp_lag_3" in out.columns:
        out["temp_delta_3"] = out["temp"] - out["temp_lag_3"]
    if "humi" in out.columns and "humi_lag_1" in out.columns:
        out["humi_delta_1"] = out["humi"] - out["humi_lag_1"]
    if "soil" in out.columns and "soil_lag_1" in out.columns:
        out["soil_delta_1"] = out["soil"] - out["soil_lag_1"]

    if "temp" in out.columns and "humi" in out.columns:
        out["temp_humi_product"] = out["temp"] * out["humi"]
    if "temp" in out.columns and "soil" in out.columns:
        out["temp_soil_ratio"] = out["temp"] / (out["soil"] + 0.1)
    if "humi" in out.columns and "soil" in out.columns:
        out["humi_soil_product"] = out["humi"] * out["soil"]
    if "temp" in out.columns and "light" in out.columns:
        out["temp_light_ratio"] = out["temp"] / (out["light"] + 1.0)

    return out


def make_supervised_frame(df: pd.DataFrame, horizon_steps: int = HORIZON_STEPS, include_target: bool = True) -> pd.DataFrame:
    out = add_time_features(df)
    out = add_lag_rolling_features(out)
    if include_target:
        out["target_future"] = out[TARGET_COL]
    return out


def clean_supervised_frame(df: pd.DataFrame, feature_columns: list[str] | None = None, require_target: bool = True) -> pd.DataFrame:
    if feature_columns is None:
        feature_columns = FEATURE_COLUMNS
    needed = feature_columns + (["target_future"] if require_target else [])
    out = df.copy()
    for col in needed:
        if col not in out.columns:
            out[col] = np.nan
    out = out.replace([np.inf, -np.inf], np.nan)
    out = out.dropna(subset=needed).reset_index(drop=True)
    return out


def time_split(df: pd.DataFrame, train_ratio: float = 0.75) -> tuple[pd.DataFrame, pd.DataFrame]:
    if not 0.5 <= train_ratio <= 0.9:
        raise ValueError("train_ratio nên nằm trong khoảng 0.5 đến 0.9")
    split_idx = int(len(df) * train_ratio)
    return df.iloc[:split_idx].copy(), df.iloc[split_idx:].copy()


def regression_metrics(y_true, y_pred) -> dict:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    err = y_pred - y_true
    mae = np.mean(np.abs(err))
    rmse = float(np.sqrt(np.mean(err ** 2)))
    denom = np.maximum(np.abs(y_true), 1e-6)
    mape = np.mean(np.abs(err) / denom) * 100.0
    bias = np.mean(err)
    return {
        "mae": float(round(mae, 4)),
        "rmse": float(round(rmse, 4)),
        "mape_percent": float(round(mape, 4)),
        "forecast_bias": float(round(bias, 4)),
    }


def risk_from_prediction(predicted_value: float, thresholds: dict) -> str:
    if predicted_value >= thresholds["critical"]:
        return "CRITICAL"
    if predicted_value >= thresholds["high"]:
        return "HIGH"
    if predicted_value >= thresholds["warning"]:
        return "WARNING"
    return "NORMAL"


def recommendation_from_risk(risk_level: str) -> str:
    if risk_level == "CRITICAL":
        return "HUMAN_CHECK_BEFORE_ACTUATOR_CONTROL"
    if risk_level == "HIGH":
        return "REDUCE_NON_CRITICAL_LOAD_OR_CHECK_HVAC"
    if risk_level == "WARNING":
        return "MONITOR_AND_PREPARE_ENERGY_SAVING_ACTION"
    return "CONTINUE_MONITORING"


def reason_from_risk(predicted_value: float, thresholds: dict) -> str:
    return (
        f"Predicted temperature is {predicted_value:.2f} °C; "
        f"warning/high/critical boundaries are "
        f"{thresholds['warning']:.2f}/{thresholds['high']:.2f}/{thresholds['critical']:.2f} °C."
    )


def build_forecast_log(test_df: pd.DataFrame, predicted_values, thresholds: dict, model_version: str = MODEL_VERSION) -> pd.DataFrame:
    out = test_df[[DATE_COL, "target_future"]].copy()
    out = out.rename(columns={DATE_COL: "timestamp", "target_future": "actual_value"})
    out["predicted_value"] = np.asarray(predicted_values, dtype=float)
    out["forecast_error"] = out["predicted_value"] - out["actual_value"]
    out["abs_error"] = out["forecast_error"].abs()
    out["risk_level"] = [risk_from_prediction(v, thresholds) for v in out["predicted_value"]]
    out["recommendation"] = [recommendation_from_risk(r) for r in out["risk_level"]]
    out["reason"] = [reason_from_risk(v, thresholds) for v in out["predicted_value"]]
    out["model_version"] = model_version
    return out


def fill_missing_for_api(df: pd.DataFrame, medians: dict) -> pd.DataFrame:
    out = df.copy()
    if DATE_COL in out.columns:
        out[DATE_COL] = pd.to_datetime(out[DATE_COL], utc=True, errors="coerce")
    for col in FEATURE_COLUMNS:
        if col not in out.columns:
            out[col] = np.nan
        out[col] = pd.to_numeric(out[col], errors="coerce")
    for col, value in medians.items():
        if col in out.columns:
            out[col] = out[col].fillna(float(value))
    return out
