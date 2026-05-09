-- Smart Irrigation AIoT Database Schema
-- Created for Supabase PostgreSQL

-- Bảng devices (thiết bị)
CREATE TABLE devices (
    device_id VARCHAR(10) PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    location VARCHAR(100),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'maintenance')),
    node_role VARCHAR(10) DEFAULT 'NODE' CHECK (node_role IN ('LEADER', 'NODE')),
    firmware_version VARCHAR(20),
    last_seen TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Bảng telemetry (dữ liệu cảm biến)
CREATE TABLE telemetry (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(10) REFERENCES devices(device_id) ON DELETE CASCADE,
    timestamp TIMESTAMP DEFAULT NOW(),
    soil_moisture FLOAT CHECK (soil_moisture >= 0 AND soil_moisture <= 100),
    temperature FLOAT,
    humidity FLOAT CHECK (humidity >= 0 AND humidity <= 100),
    light INT CHECK (light >= 0 AND light <= 100),
    pump_state VARCHAR(5) CHECK (pump_state IN ('ON', 'OFF')),
    rssi INT, -- Signal strength
    node_role VARCHAR(10),
    mesh_link_quality INT CHECK (mesh_link_quality >= 0 AND mesh_link_quality <= 100),
    battery_voltage FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Bảng ai_results (kết quả AI)
CREATE TABLE ai_results (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(10) REFERENCES devices(device_id) ON DELETE CASCADE,
    timestamp TIMESTAMP DEFAULT NOW(),
    model_name VARCHAR(50) NOT NULL,
    result JSONB NOT NULL,
    confidence FLOAT CHECK (confidence >= 0 AND confidence <= 1),
    is_anomaly BOOLEAN DEFAULT FALSE,
    anomaly_reason TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Bảng commands (lệnh điều khiển)
CREATE TABLE commands (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(10) REFERENCES devices(device_id) ON DELETE CASCADE,
    command VARCHAR(50) NOT NULL CHECK (command IN ('ON', 'OFF', 'RESTART', 'UPDATE')),
    duration_seconds INT DEFAULT 0,
    source VARCHAR(20) DEFAULT 'FLASK' CHECK (source IN ('FLASK', 'AI_AUTO', 'MANUAL')),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'executed', 'failed')),
    created_at TIMESTAMP DEFAULT NOW(),
    sent_at TIMESTAMP,
    executed_at TIMESTAMP,
    ack_received BOOLEAN DEFAULT FALSE,
    error_message TEXT
);

-- Bảng anomalies (bất thường)
CREATE TABLE anomalies (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(10) REFERENCES devices(device_id) ON DELETE CASCADE,
    timestamp TIMESTAMP DEFAULT NOW(),
    anomaly_type VARCHAR(50) NOT NULL,
    anomaly_score FLOAT CHECK (anomaly_score >= 0 AND anomaly_score <= 1),
    description TEXT NOT NULL,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP,
    resolved_by VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Bảng irrigation_schedules (lịch tưới)
CREATE TABLE irrigation_schedules (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(10) REFERENCES devices(device_id) ON DELETE CASCADE,
    schedule_name VARCHAR(100) NOT NULL,
    start_time TIME NOT NULL,
    duration_minutes INT NOT NULL,
    days_of_week VARCHAR(20), -- e.g., "1,2,3,4,5" for Mon-Fri
    is_active BOOLEAN DEFAULT TRUE,
    soil_moisture_threshold FLOAT CHECK (soil_moisture_threshold >= 0 AND soil_moisture_threshold <= 100),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Bảng system_logs (nhật ký hệ thống)
CREATE TABLE system_logs (
    id SERIAL PRIMARY KEY,
    level VARCHAR(10) CHECK (level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR')),
    message TEXT NOT NULL,
    component VARCHAR(50), -- e.g., 'MQTT', 'AI', 'FLASK'
    device_id VARCHAR(10),
    timestamp TIMESTAMP DEFAULT NOW(),
    metadata JSONB
);

-- Indexes for performance
CREATE INDEX idx_telemetry_device_timestamp ON telemetry(device_id, timestamp DESC);
CREATE INDEX idx_telemetry_timestamp ON telemetry(timestamp DESC);
CREATE INDEX idx_ai_results_device_timestamp ON ai_results(device_id, timestamp DESC);
CREATE INDEX idx_commands_device_status ON commands(device_id, status);
CREATE INDEX idx_anomalies_device_resolved ON anomalies(device_id, resolved);
CREATE INDEX idx_system_logs_timestamp ON system_logs(timestamp DESC);

-- Triggers for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_devices_updated_at BEFORE UPDATE ON devices
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_irrigation_schedules_updated_at BEFORE UPDATE ON irrigation_schedules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert sample data
INSERT INTO devices (device_id, name, location, node_role) VALUES
('DEV001', 'Irrigation Node 1', 'Field A', 'LEADER'),
('DEV002', 'Irrigation Node 2', 'Field A', 'NODE'),
('DEV003', 'Irrigation Node 3', 'Field B', 'NODE');

-- Sample irrigation schedule
INSERT INTO irrigation_schedules (device_id, schedule_name, start_time, duration_minutes, days_of_week, soil_moisture_threshold) VALUES
('DEV001', 'Morning Irrigation', '06:00:00', 30, '1,2,3,4,5,6,7', 40.0);