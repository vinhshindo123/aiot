import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib
import os
from datetime import datetime

# Tạo dữ liệu mẫu để huấn luyện
def generate_training_data(n_samples=1000):
    np.random.seed(42)

    # Tạo dữ liệu soil moisture
    soil_moisture = np.random.normal(50, 15, n_samples)
    soil_moisture = np.clip(soil_moisture, 0, 100)

    # Tạo dữ liệu temperature, humidity, light
    temperature = np.random.normal(30, 5, n_samples)
    humidity = np.random.normal(60, 10, n_samples)
    light = np.random.normal(70, 20, n_samples)

    # Tạo anomalies (outliers)
    anomaly_indices = np.random.choice(n_samples, size=int(n_samples*0.05), replace=False)
    soil_moisture[anomaly_indices] = np.random.choice([120, -10], size=len(anomaly_indices))

    # Tạo target cho forecasting (moisture sau 30 phút)
    future_moisture = soil_moisture - np.random.normal(5, 2, n_samples) * (temperature/40) * ((100-humidity)/100)
    future_moisture = np.clip(future_moisture, 0, 100)

    data = pd.DataFrame({
        'soil_moisture': soil_moisture,
        'temperature': temperature,
        'humidity': humidity,
        'light': light,
        'future_moisture': future_moisture
    })

    return data

# Huấn luyện model Anomaly Detection
def train_anomaly_model():
    print("Training Anomaly Detection Model...")

    data = generate_training_data()

    # Features cho anomaly detection
    features = ['soil_moisture', 'temperature', 'humidity', 'light']
    X = data[features]

    # Isolation Forest
    model = IsolationForest(contamination=0.05, random_state=42)
    model.fit(X)

    # Lưu model
    joblib.dump(model, 'models/anomaly_model.pkl')
    print("Anomaly model saved to models/anomaly_model.pkl")

    return model

# Huấn luyện model Forecasting
def train_forecasting_model():
    print("Training Moisture Forecasting Model...")

    data = generate_training_data()

    # Features
    features = ['soil_moisture', 'temperature', 'humidity', 'light']
    X = data[features]
    y = data['future_moisture']

    # Random Forest Regressor
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)

    # Lưu model
    joblib.dump(model, 'models/forecast_model.pkl')
    print("Forecast model saved to models/forecast_model.pkl")

    return model

# Load models
def load_anomaly_model():
    os.makedirs('models', exist_ok=True)
    if os.path.exists('models/anomaly_model.pkl'):
        return joblib.load('models/anomaly_model.pkl')
    else:
        print("Anomaly model not found, training new one...")
        return train_anomaly_model()

def load_forecasting_model():
    os.makedirs('models', exist_ok=True)
    if os.path.exists('models/forecast_model.pkl'):
        return joblib.load('models/forecast_model.pkl')
    else:
        print("Forecast model not found, training new one...")
        return train_forecasting_model()

# Predict functions
def predict_anomaly(model, data):
    features = np.array([[data.get('soil_moisture', 50),
                         data.get('temperature', 30),
                         data.get('humidity', 60),
                         data.get('light', 70)]])

    prediction = model.predict(features)[0]

    # Isolation Forest: -1 là anomaly, 1 là normal
    is_anomaly = prediction == -1

    # Tính anomaly score (decision function)
    anomaly_score = -model.decision_function(features)[0]  # Higher score = more anomalous

    return {
        "is_anomaly": bool(is_anomaly),
        "anomaly_score": float(anomaly_score),
        "reason": "Anomaly detected by ML model" if is_anomaly else "Normal"
    }

def predict_moisture(model, data):
    features = np.array([[data.get('soil_moisture', 50),
                         data.get('temperature', 30),
                         data.get('humidity', 60),
                         data.get('light', 70)]])

    predicted_30 = model.predict(features)[0]

    # Dự báo 60 phút: dùng kết quả 30 phút làm input tiếp cho model
    features_60 = np.array([[predicted_30,
                             data.get('temperature', 30),
                             data.get('humidity', 60),
                             data.get('light', 70)]])
    predicted_60 = model.predict(features_60)[0]

    return {
        "predicted_moisture_30min": float(predicted_30),
        "predicted_moisture_60min": float(predicted_60),
        "risk_level": "HIGH" if predicted_30 < 30 else "MEDIUM" if predicted_30 < 45 else "LOW",
        "recommendation": "Irrigation needed" if predicted_30 < 30 else "Monitor" if predicted_30 < 45 else "Adequate"
    }

if __name__ == "__main__":
    # Tạo thư mục models nếu chưa có
    os.makedirs('models', exist_ok=True)

    # Huấn luyện models
    anomaly_model = train_anomaly_model()
    forecast_model = train_forecasting_model()

    print("Training completed!")