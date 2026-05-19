from __future__ import annotations

from pathlib import Path
import json
import numpy as np
import pandas as pd
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
MODEL_DIR = PROJECT_ROOT / "models"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

FEATURE_COLUMNS: list[str] = []


def infer_sensor_columns(df: pd.DataFrame) -> list[str]:
    """Return list of columns that should be used as numeric sensor features.
    
    Excludes meta columns: created_at, node_id, label, id, and any columns with 'id' in name
    """
    # Loại bỏ các cột cụ thể
    exclude = {"created_at", "node_id", "label", "id", "ID", "Id", "isDefault"}
    
    # Hoặc loại bỏ tất cả cột có chứa 'id' (không phân biệt hoa thường)
    numeric_cols = []
    for c in df.columns:
        if pd.api.types.is_numeric_dtype(df[c]):
            # Kiểm tra nếu cột không nằm trong exclude và không chứa 'id'
            if c not in exclude and 'id' not in c.lower():
                numeric_cols.append(c)
    
    return numeric_cols


def load_dataset(path: str | Path | None = None) -> pd.DataFrame:
    if path is None:
        candidates = [
            DATA_DIR / "measurements.csv",
            DATA_DIR / "sample_measurements.csv",
        ]
        for p in candidates:
            if p.exists():
                path = p
                break
        else:
            raise FileNotFoundError("Không tìm thấy dataset measurements. Hãy chạy: python src/download_data.py --source <path_to_hydroponics.csv>")

    df = pd.read_csv(path)
    if "created_at" in df.columns:
        df["created_at"] = pd.to_datetime(df["created_at"])
    df = df.sort_values(["node_id", "created_at"]).drop_duplicates(["node_id", "created_at"]).reset_index(drop=True)
    if "label" not in df.columns:
        df["label"] = 0
    df["label"] = df["label"].fillna(0).astype(int)
    return df


def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add time-based and rolling features for anomaly detection"""
    out = df.copy()
    out["created_at"] = pd.to_datetime(out["created_at"])
    out = out.sort_values(["created_at"]).reset_index(drop=True)  # Bỏ qua node_id để tránh lỗi
    
    # Time features
    out["hour"] = out["created_at"].dt.hour
    out["dayofweek"] = out["created_at"].dt.dayofweek
    out["month"] = out["created_at"].dt.month
    
    # Thêm node_code nếu có node_id
    if "node_id" in out.columns:
        out["node_code"] = out["node_id"].astype("category").cat.codes
    
    # Infer sensor columns
    sensors = infer_sensor_columns(out)
    
    print(f"Đang tạo features cho các sensor: {sensors}")
    
    # Add features for each sensor
    for s in sensors:
        try:
            # Rolling statistics (window=6)
            out[f"rolling_mean_{s}"] = out[s].rolling(window=6, min_periods=1).mean()
            out[f"rolling_std_{s}"] = out[s].rolling(window=6, min_periods=2).std().fillna(0)
            
            # Delta (change)
            out[f"delta_{s}"] = out[s].diff().fillna(0)
            
            # Z-score (cẩn thận với division by zero)
            rolling_std_safe = out[f"rolling_std_{s}"].copy()
            rolling_std_safe = rolling_std_safe.replace(0, np.nan)
            out[f"zscore_{s}"] = ((out[s] - out[f"rolling_mean_{s}"]) / rolling_std_safe).fillna(0)
            
            # Stuck candidate - đơn giản hóa
            rolling_std_stuck = out[s].rolling(window=5, min_periods=2).std().fillna(1)
            sensor_range = out[s].max() - out[s].min()
            if sensor_range > 0:
                threshold = 0.01 * sensor_range
            else:
                threshold = 0.01
            out[f"is_{s}_stuck_candidate"] = (rolling_std_stuck < threshold).astype(int)
            
        except Exception as e:
            print(f"  ⚠️ Lỗi khi tạo features cho {s}: {e}")
            # Tạo default values nếu lỗi
            out[f"rolling_mean_{s}"] = out[s]
            out[f"rolling_std_{s}"] = 0
            out[f"delta_{s}"] = 0
            out[f"zscore_{s}"] = 0
            out[f"is_{s}_stuck_candidate"] = 0
    
    return out

def time_split(df: pd.DataFrame, train_ratio: float = 0.65) -> tuple[pd.DataFrame, pd.DataFrame]:
    split_idx = int(len(df) * train_ratio)
    return df.iloc[:split_idx].copy(), df.iloc[split_idx:].copy()


def normalize_scores(raw_scores, score_min: float, score_max: float) -> np.ndarray:
    raw_scores = np.asarray(raw_scores, dtype=float)
    norm = (raw_scores - score_min) / (score_max - score_min + 1e-9)
    return np.clip(norm, 0.0, 1.0)


def event_type_from_row(row: pd.Series) -> str:
    """Detect event type from hydroponics sensor data"""
    # Check for sensor stuck
    for k, v in row.items():
        if k.startswith("is_") and str(k).endswith("_stuck_candidate") and int(v or 0) == 1:
            sensor_name = k[3:-16] if k.endswith("_stuck_candidate") else k[3:]
            return f"{sensor_name.upper()}_SENSOR_STUCK"
    
    # Check for large deltas (spikes/drops)
    for k, v in row.items():
        if k.startswith("delta_"):
            sensor = k[6:]
            if abs(float(v or 0)) > 5:
                return f"{sensor.upper()}_SPIKE_DROP"
    
    # Check for pattern deviation via zscore
    for k, v in row.items():
        if k.startswith("zscore_") and abs(float(v or 0)) > 3.5:
            sensor = k[7:]
            return f"{sensor.upper()}_PATTERN_DEVIATION"
    
    # Hydroponics-specific checks
    if "ph" in row.index and abs(row.get("delta_ph", 0)) > 0.5:
        return "PH_LEVEL_ABNORMAL"
    if "ec" in row.index and abs(row.get("delta_ec", 0)) > 200:
        return "EC_LEVEL_ABNORMAL"
    if "water_temp" in row.index and abs(row.get("delta_water_temp", 0)) > 3:
        return "WATER_TEMP_ABNORMAL"
    if "co2" in row.index and abs(row.get("delta_co2", 0)) > 200:
        return "CO2_LEVEL_ABNORMAL"
    
    return "SENSOR_ANOMALY"


def severity_from_score(score: float, threshold: float, high_threshold: float = 0.78) -> str:
    if score >= high_threshold:
        return "HIGH"
    if score >= threshold:
        return "MEDIUM"
    return "LOW"


def decision_from_severity(severity: str) -> str:
    if severity == "HIGH":
        return "CREATE_ALERT_AND_HUMAN_CHECK"
    if severity == "MEDIUM":
        return "CREATE_MONITORING_EVENT"
    return "LOG_FOR_MONITORING"


def explanation_from_row(row: pd.Series) -> str:
    reasons = []
    
    # Collect reasons from engineered fields
    for k, v in row.items():
        if k.startswith("zscore_") and abs(float(v or 0)) > 3.5:
            sensor = k[7:]
            reasons.append(f"{sensor} deviates sharply from recent pattern")
        if k.startswith("delta_") and abs(float(v or 0)) > 5:
            sensor = k[6:]
            reasons.append(f"Sudden {sensor} jump/drop detected")
        if k.startswith("is_") and k.endswith("_stuck_candidate") and int(v or 0) == 1:
            sensor = k[3:-16] if k.endswith("_stuck_candidate") else k[3:]
            reasons.append(f"{sensor} sensor may be stuck")
    
    # Hydroponics-specific explanations
    if "ph" in row.index and abs(row.get("delta_ph", 0)) > 0.5:
        reasons.append(f"pH level changed by {row.get('delta_ph', 0):.2f} - outside safe range (5.5-6.5)")
    if "ec" in row.index and abs(row.get("delta_ec", 0)) > 200:
        reasons.append(f"EC changed by {row.get('delta_ec', 0):.0f} µS/cm - nutrient concentration issue")
    if "water_temp" in row.index and abs(row.get("delta_water_temp", 0)) > 3:
        reasons.append(f"Water temperature changed by {row.get('delta_water_temp', 0):.1f}°C")
    if "co2" in row.index and abs(row.get("delta_co2", 0)) > 200:
        reasons.append(f"CO2 level changed by {row.get('delta_co2', 0):.0f} ppm")
    
    if not reasons:
        reasons.append("Anomaly score exceeds operational threshold")
    
    return "; ".join(reasons)


def build_events(df: pd.DataFrame, threshold: float | None = None) -> pd.DataFrame:
    if threshold is None:
        threshold = 0.55
    events = []
    for _, row in df.iterrows():
        if int(row.get("is_anomaly", 0)) == 0:
            continue
        score = float(row.get("anomaly_score", 0.0))
        severity = severity_from_score(score, threshold=threshold)
        
        # Include all sensor numeric values in the event payload
        event = {
            "created_at": row["created_at"],
            "node_id": row.get("node_id", "unknown"),
            "anomaly_score": round(score, 4),
            "threshold_used": round(float(threshold), 4),
            "severity": severity,
            "event_type": event_type_from_row(row),
            "decision": decision_from_severity(severity),
            "explanation": explanation_from_row(row),
            "model_version": row.get("model_version", "iforest_v2"),
        }
        
        # Add all sensor values
        for c in infer_sensor_columns(df):
            try:
                event[c] = float(row.get(c, np.nan))
            except Exception:
                event[c] = row.get(c, None)
        events.append(event)
    return pd.DataFrame(events)


def evaluate_detection(y_true, y_pred) -> dict:
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    return {
        "precision": float(round(precision, 4)),
        "recall": float(round(recall, 4)),
        "f1_score": float(round(f1, 4)),
        "confusion_matrix": cm.tolist(),
        "tn": int(cm[0][0]),
        "fp": int(cm[0][1]),
        "fn": int(cm[1][0]),
        "tp": int(cm[1][1]),
    }


def make_windows(values: np.ndarray, window_size: int = 24) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    if len(values) < window_size:
        raise ValueError("Không đủ dữ liệu để tạo window.")
    return np.array([values[i:i + window_size] for i in range(len(values) - window_size + 1)])


def save_json(obj, path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")