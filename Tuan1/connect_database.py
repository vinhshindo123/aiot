# connect_database.py
import os
from supabase import create_client, Client
from datetime import datetime
import json

# Supabase configuration
SUPABASE_URL = "https://rhzayezieiosgjicokfg.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJoemF5ZXppZWlvc2dqaWNva2ZnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc5ODY1MzEsImV4cCI6MjA5MzU2MjUzMX0.7stVY88kzXym6HS5g72McqjnQ_s6DlC2Zv606-XNi2Y"

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def test_connection():
    """Test connection to Supabase"""
    try:
        # Simple query to test connection
        result = supabase.table("devices").select("count").limit(1).execute()
        print("Supabase connection successful!")
        return True
    except Exception as e:
        print(f"Supabase connection failed: {e}")
        return False

# Device management functions
def add_device(device_id, name, location, node_role="NODE"):
    """Add a new device to the database"""
    try:
        result = supabase.table("devices").insert({
            "device_id": device_id,
            "name": name,
            "location": location,
            "node_role": node_role,
            "status": "active",
            "created_at": datetime.now().isoformat()
        }).execute()
        return result
    except Exception as e:
        print(f"Error adding device: {e}")
        return None

def get_devices():
    """Get all devices"""
    try:
        result = supabase.table("devices").select("*").execute()
        return result.data
    except Exception as e:
        print(f"Error getting devices: {e}")
        return []

def update_device_status(device_id, status):
    """Update device status"""
    try:
        result = supabase.table("devices").update({
            "status": status,
            "last_seen": datetime.now().isoformat()
        }).eq("device_id", device_id).execute()
        return result
    except Exception as e:
        print(f"Error updating device status: {e}")
        return None

# Telemetry functions
def save_telemetry(data):
    """Save telemetry data"""
    try:
        result = supabase.table("telemetry").insert({
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
        return result
    except Exception as e:
        print(f"Error saving telemetry: {e}")
        return None

def get_latest_telemetry(device_id):
    """Get latest telemetry for a device"""
    try:
        result = supabase.table("telemetry").select("*").eq("device_id", device_id).order("timestamp", desc=True).limit(1).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"Error getting latest telemetry: {e}")
        return None

def get_telemetry_history(device_id, limit=50):
    """Get telemetry history for a device"""
    try:
        result = supabase.table("telemetry").select("*").eq("device_id", device_id).order("timestamp", desc=True).limit(limit).execute()
        return result.data
    except Exception as e:
        print(f"Error getting telemetry history: {e}")
        return []

# AI Results functions
def save_ai_result(device_id, model_name, result, confidence):
    """Save AI analysis result"""
    try:
        result = supabase.table("ai_results").insert({
            "device_id": device_id,
            "model_name": model_name,
            "result": json.dumps(result),
            "confidence": confidence
        }).execute()
        return result
    except Exception as e:
        print(f"Error saving AI result: {e}")
        return None

def get_ai_results(device_id, limit=10):
    """Get AI results for a device"""
    try:
        result = supabase.table("ai_results").select("*").eq("device_id", device_id).order("timestamp", desc=True).limit(limit).execute()
        return result.data
    except Exception as e:
        print(f"Error getting AI results: {e}")
        return []

# Command functions
def save_command(device_id, command, duration, source="FLASK"):
    """Save command to database"""
    try:
        result = supabase.table("commands").insert({
            "device_id": device_id,
            "command": command,
            "duration_seconds": duration,
            "source": source,
            "status": "sent"
        }).execute()
        return result
    except Exception as e:
        print(f"Error saving command: {e}")
        return None

def update_command_status(device_id, command, status, executed_at=None):
    """Update command status"""
    try:
        update_data = {"status": status}
        if executed_at:
            update_data["executed_at"] = executed_at
            update_data["ack_received"] = True

        result = supabase.table("commands").update(update_data).eq("device_id", device_id).eq("command", command).execute()
        return result
    except Exception as e:
        print(f"Error updating command status: {e}")
        return None

def get_commands(device_id=None, limit=20):
    """Get commands, optionally filtered by device"""
    try:
        query = supabase.table("commands").select("*").order("created_at", desc=True).limit(limit)
        if device_id:
            query = query.eq("device_id", device_id)
        result = query.execute()
        return result.data
    except Exception as e:
        print(f"Error getting commands: {e}")
        return []

# Anomaly functions
def save_anomaly(device_id, anomaly_type, anomaly_score, description):
    """Save anomaly to database"""
    try:
        result = supabase.table("anomalies").insert({
            "device_id": device_id,
            "anomaly_type": anomaly_type,
            "anomaly_score": anomaly_score,
            "description": description,
            "resolved": False
        }).execute()
        return result
    except Exception as e:
        print(f"Error saving anomaly: {e}")
        return None

def get_anomalies(limit=20):
    """Get recent anomalies"""
    try:
        result = supabase.table("anomalies").select("*").order("timestamp", desc=True).limit(limit).execute()
        return result.data
    except Exception as e:
        print(f"Error getting anomalies: {e}")
        return []

def resolve_anomaly(anomaly_id):
    """Mark anomaly as resolved"""
    try:
        result = supabase.table("anomalies").update({"resolved": True}).eq("id", anomaly_id).execute()
        return result
    except Exception as e:
        print(f"Error resolving anomaly: {e}")
        return None

# Utility functions
def get_device_stats():
    """Get statistics about devices"""
    try:
        # Count devices by status
        active = supabase.table("devices").select("count", count="exact").eq("status", "active").execute()
        inactive = supabase.table("devices").select("count", count="exact").eq("status", "inactive").execute()

        return {
            "total_devices": len(get_devices()),
            "active_devices": active.count if hasattr(active, 'count') else 0,
            "inactive_devices": inactive.count if hasattr(inactive, 'count') else 0
        }
    except Exception as e:
        print(f"Error getting device stats: {e}")
        return {"total_devices": 0, "active_devices": 0, "inactive_devices": 0}

if __name__ == "__main__":
    # Test connection when running this file directly
    test_connection()