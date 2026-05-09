import paho.mqtt.client as mqtt
import json
import threading
from datetime import datetime
from supabase import create_client

# Supabase config
SUPABASE_URL = "https://rhzayezieiosgjicokfg.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJoemF5ZXppZWlvc2dqaWNva2ZnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc5ODY1MzEsImV4cCI6MjA5MzU2MjUzMX0.7stVY88kzXym6HS5g72McqjnQ_s6DlC2Zv606-XNi2Y"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# MQTT config
MQTT_BROKER = "192.168.0.105"
MQTT_PORT = 1883
MQTT_TOPIC_TELEMETRY = "smart_irrigation/telemetry"
MQTT_TOPIC_COMMAND = "smart_irrigation/command"
MQTT_TOPIC_ACK = "smart_irrigation/ack"

mqtt_client = mqtt.Client()

# Callback để Flask nhận dữ liệu
telemetry_callbacks = []
ack_callbacks = []

def add_telemetry_callback(callback):
    telemetry_callbacks.append(callback)

def add_ack_callback(callback):
    ack_callbacks.append(callback)

def on_connect(client, userdata, flags, rc):
    print(f"MQTT Connected with result code {rc}")
    client.subscribe(MQTT_TOPIC_TELEMETRY)
    client.subscribe(MQTT_TOPIC_ACK)

def on_message(client, userdata, msg):
    if msg.topic == MQTT_TOPIC_TELEMETRY:
        data = json.loads(msg.payload.decode())
        # Lưu telemetry
        save_telemetry(data)
        # Gọi callbacks để Flask nhận dữ liệu tức thì
        for callback in telemetry_callbacks:
            threading.Thread(target=callback, args=(data,)).start()
    elif msg.topic == MQTT_TOPIC_ACK:
        ack_data = json.loads(msg.payload.decode())
        # Cập nhật status command
        update_command_status(ack_data)
        # Gọi callbacks
        for callback in ack_callbacks:
            threading.Thread(target=callback, args=(ack_data,)).start()

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

def start_mqtt():
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_start()

def stop_mqtt():
    mqtt_client.loop_stop()
    mqtt_client.disconnect()

def send_command(device_id, command, duration=0):
    cmd_data = {
        "device_id": device_id,
        "command": command,
        "duration": duration,
        "timestamp": datetime.now().isoformat()
    }
    mqtt_client.publish(MQTT_TOPIC_COMMAND, json.dumps(cmd_data))

    # Save to commands table
    supabase.table("commands").insert({
        "device_id": device_id,
        "command": command,
        "duration_seconds": duration,
        "source": "FLASK",
        "status": "sent"
    }).execute()

    return cmd_data

def save_telemetry(data):
    supabase.table("telemetry").insert({
        "device_id": data.get("device_id"),
        "soil_moisture": data.get("soil_moisture"),
        "temperature": data.get("temperature"),
        "humidity": data.get("humidity"),
        "light": data.get("light"),
        "pump_state": data.get("pump_state"),
        "rssi": data.get("rssi"),
        "node_role": data.get("node_role"),
        "mesh_link_quality": data.get("mesh_link_quality")
    }).execute()

def update_command_status(ack_data):
    supabase.table("commands")\
        .update({"status": "executed", "executed_at": datetime.now().isoformat(), "ack_received": True})\
        .eq("device_id", ack_data.get("device_id"))\
        .eq("command", ack_data.get("command"))\
        .execute()