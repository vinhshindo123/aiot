from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import numpy as np
from datetime import datetime, timedelta
import json
import threading
import time
import os

# Import custom modules
from mqtt_handler import start_mqtt, stop_mqtt, send_command as mqtt_send_command, add_telemetry_callback, add_ack_callback
from connect_database import supabase, save_telemetry, save_ai_result, save_anomaly, update_command_status
from train_model import load_anomaly_model, load_forecasting_model, predict_anomaly, predict_moisture

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Load AI models
anomaly_model = load_anomaly_model()
forecast_model = load_forecasting_model()

# ==================== MQTT Callbacks ====================

def on_telemetry_received(data):
    """Callback khi nhận telemetry từ MQTT"""
    print(f"Telemetry received: {data.get('device_id')}")

    # Chạy AI analysis
    ai_result = run_ai_analysis(data)

    # Emit to dashboard via SocketIO
    socketio.emit('telemetry_update', {
        'device_id': data.get('device_id'),
        'data': data,
        'ai_result': ai_result
    })

def on_ack_received(ack_data):
    """Callback khi nhận ACK từ MQTT"""
    print(f"ACK received: {ack_data}")

    # Emit to dashboard
    socketio.emit('command_ack', ack_data)

# Register callbacks
add_telemetry_callback(on_telemetry_received)
add_ack_callback(on_ack_received)

# ==================== AI MODULES ====================

def anomaly_detection(data):
    """Detect anomalies using trained ML model"""
    return predict_anomaly(anomaly_model, data)

def moisture_forecasting(data):
    """Forecast moisture using trained ML model"""
    return predict_moisture(forecast_model, data)

def leader_failure_prediction(data):
    """Simple leader failure prediction (can be enhanced with ML)"""
    rssi = data.get("rssi", -70)
    node_role = data.get("node_role", "NODE")

    health_score = 100
    failure_risk = "LOW"

    # RSSI based scoring
    if rssi < -90:
        health_score -= 40
        failure_risk = "HIGH"
    elif rssi < -80:
        health_score -= 20
        failure_risk = "MEDIUM"
    elif rssi < -70:
        health_score -= 10
        failure_risk = "LOW"

    # Leader specific checks
    if node_role == "LEADER":
        # Check last seen (this would need historical data)
        health_score -= 10  # Simplified

    return {
        "leader_health_score": max(0, health_score),
        "failure_risk": failure_risk,
        "recommended_action": "Initiate failover" if failure_risk == "HIGH" else "Monitor only"
    }

# ==================== DECISION ENGINE ====================

def decision_engine(data, forecast, anomaly):
    auto_mode = True  # Configurable via dashboard

    if anomaly["is_anomaly"]:
        return {
            "action": "NONE",
            "confidence": 1.0,
            "reason": f"Anomaly detected: {anomaly['reason']}",
            "requires_confirmation": True
        }

    if forecast["risk_level"] == "HIGH" and forecast["predicted_moisture_30min"] < 30:
        if auto_mode and forecast["predicted_moisture_30min"] < 25:
            return {
                "action": "PUMP_ON",
                "duration": 180,
                "confidence": 0.92,
                "reason": f"AI predicts moisture will drop to {forecast['predicted_moisture_30min']:.1f}% in 30min",
                "requires_confirmation": False
            }
        else:
            return {
                "action": "RECOMMEND_PUMP_ON",
                "duration": 180,
                "confidence": 0.85,
                "reason": f"AI recommends irrigation (predicted: {forecast['predicted_moisture_30min']:.1f}%)",
                "requires_confirmation": True
            }

    if data.get("pump_state") == "ON" and forecast["predicted_moisture_30min"] > 55:
        return {
            "action": "PUMP_OFF",
            "duration": 0,
            "confidence": 0.88,
            "reason": "Soil moisture adequate, turning off pump",
            "requires_confirmation": False
        }

    return {
        "action": "NONE",
        "confidence": 1.0,
        "reason": "Conditions normal, no action needed",
        "requires_confirmation": False
    }

def run_ai_analysis(data):
    print(f"Running AI analysis for {data.get('device_id')}")

    # Run AI modules
    anomaly = anomaly_detection(data)
    forecast = moisture_forecasting(data)
    leader_pred = leader_failure_prediction(data)

    # Save AI results
    save_ai_result(data.get("device_id"), "anomaly_detection", anomaly, 1 - anomaly.get("anomaly_score", 0))
    save_ai_result(data.get("device_id"), "moisture_forecast", forecast, 0.9)

    # If anomaly detected, save to anomalies table
    if anomaly["is_anomaly"]:
        save_anomaly(data.get("device_id"), "sensor_anomaly", anomaly["anomaly_score"], anomaly["reason"])

    # Decision engine
    decision = decision_engine(data, forecast, anomaly)

    if decision["action"] == "PUMP_ON":
        mqtt_send_command(data.get("device_id"), "ON", decision["duration"])
    elif decision["action"] == "PUMP_OFF":
        mqtt_send_command(data.get("device_id"), "OFF", 0)

    return {
        "anomaly": anomaly,
        "forecast": forecast,
        "leader_prediction": leader_pred,
        "decision": decision
    }

# ==================== API ENDPOINTS ====================

@app.route('/api/devices', methods=['GET'])
def get_all_devices():
    """Lấy danh sách tất cả devices"""
    from connect_database import get_devices
    devices = get_devices()
    return jsonify(devices or [])

@app.route('/api/dashboard-data', methods=['GET'])
def get_dashboard_data():
    """Lấy tất cả dữ liệu cần cho dashboard"""
    from connect_database import get_devices, get_latest_telemetry, get_anomalies
    
    devices = get_devices()
    dashboard_data = []
    
    for device in devices:
        device_id = device.get('device_id')
        latest = get_latest_telemetry(device_id)
        dashboard_data.append({
            'device': device,
            'latest_telemetry': latest
        })
    
    anomalies = get_anomalies()
    
    return jsonify({
        'devices': dashboard_data,
        'anomalies': anomalies
    })

@app.route('/api/setup/insert-sample-data', methods=['POST'])
def insert_sample_data():
    """Insert sample data (chỉ cho development)"""
    try:
        from connect_database import add_device
        import random
        
        # Thêm devices
        devices = [
            ("DEV001", "Irrigation Node 1", "Field A", "LEADER"),
            ("DEV002", "Irrigation Node 2", "Field A", "NODE"),
            ("DEV003", "Irrigation Node 3", "Field B", "NODE"),
        ]
        
        for device_id, name, location, role in devices:
            add_device(device_id, name, location, role)
        
        # Thêm sample telemetry
        for device_id in ["DEV001", "DEV002", "DEV003"]:
            for i in range(5):
                telemetry_data = {
                    "device_id": device_id,
                    "soil_moisture": round(40 + random.uniform(-15, 15), 1),
                    "temperature": round(28 + random.uniform(-3, 3), 1),
                    "humidity": round(60 + random.uniform(-10, 10), 1),
                    "light": random.randint(50, 90),
                    "pump_state": random.choice(["ON", "OFF"]),
                    "rssi": random.randint(-90, -50),
                    "node_role": "LEADER" if device_id == "DEV001" else "NODE",
                    "mesh_link_quality": random.randint(70, 100)
                }
                supabase.table("telemetry").insert(telemetry_data).execute()
        
        return jsonify({"status": "success", "message": "Sample data inserted"})
    except Exception as e:
        print(f"Error inserting sample data: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/telemetry', methods=['POST'])
def receive_telemetry():
    data = request.json
    save_telemetry(data)
    threading.Thread(target=run_ai_analysis, args=(data,)).start()
    return jsonify({"status": "success", "message": "Telemetry received"})

@app.route('/api/ai/anomaly/detect', methods=['POST'])
def detect_anomaly():
    data = request.json
    result = anomaly_detection(data)
    return jsonify(result)

@app.route('/api/ai/forecast/soil-moisture', methods=['POST'])
def forecast_moisture():
    data = request.json
    result = moisture_forecasting(data)
    # Đảm bảo trả về cả predicted_moisture_60min
    return jsonify(result)

@app.route('/api/ai/predict/leader-failure', methods=['POST'])
def predict_leader():
    data = request.json
    result = leader_failure_prediction(data)
    return jsonify(result)

@app.route('/api/command', methods=['POST'])
def send_manual_command():
    data = request.json
    device_id = data.get("device_id")
    command = data.get("command")
    duration = data.get("duration", 180)

    result = mqtt_send_command(device_id, command, duration)
    return jsonify({"status": "success", "command": result})

@app.route('/api/devices/<device_id>/latest', methods=['GET'])
def get_latest_telemetry(device_id):
    from connect_database import get_latest_telemetry
    result = get_latest_telemetry(device_id)
    return jsonify(result or {})

@app.route('/api/devices/<device_id>/history', methods=['GET'])
def get_history(device_id):
    from connect_database import get_telemetry_history
    limit = request.args.get('limit', 50)
    result = get_telemetry_history(device_id, int(limit))
    return jsonify(result)

@app.route('/api/anomalies', methods=['GET'])
def get_anomalies():
    from connect_database import get_anomalies
    result = get_anomalies()
    return jsonify(result)

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

# ==================== SocketIO Events ====================

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    # Start MQTT handler
    start_mqtt()

    try:
        socketio.run(app, host='0.0.0.0', port=5000, debug=True)
    finally:
        stop_mqtt()