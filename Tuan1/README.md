# Smart Irrigation AIoT System

Hệ thống tưới tiêu thông minh sử dụng AIoT với Flask, MQTT, và Supabase.

## Cấu trúc dự án

```
├── app.py                 # Flask application chính
├── mqtt_handler.py        # Xử lý MQTT communications
├── connect_database.py    # Database operations với Supabase
├── train_model.py         # Huấn luyện AI models
├── schema.sql            # Database schema
├── requirements.txt       # Python dependencies
├── templates/
│   └── dashboard.html     # Dashboard UI
├── models/               # Trained AI models (tạo sau khi chạy train_model.py)
├── esp32_smart_irrigation/
│   └── esp32_smart_irrigation.ino  # ESP32 firmware
└── docs/                 # Documentation
```

## Cài đặt

1. **Cài đặt dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Tạo database:**
   - Chạy schema.sql trong Supabase dashboard
   - Hoặc sử dụng Supabase CLI

3. **Huấn luyện AI models:**
   ```bash
   python train_model.py
   ```

4. **Chạy ứng dụng:**
   ```bash
   python app.py
   ```

## Kiến trúc hệ thống

### MQTT Handler (`mqtt_handler.py`)
- Xử lý kết nối MQTT
- Nhận telemetry từ ESP32
- Gửi commands xuống devices
- Callbacks để Flask nhận dữ liệu tức thì

### AI Models (`train_model.py`)
- **Anomaly Detection**: Sử dụng Isolation Forest
- **Moisture Forecasting**: Sử dụng Random Forest Regressor
- Models được lưu trong thư mục `models/`

### Flask App (`app.py`)
- REST API endpoints
- WebSocket cho real-time updates
- Decision engine cho automatic irrigation
- Dashboard UI

### Database (`connect_database.py`)
- Supabase integration
- CRUD operations cho tất cả entities
- Connection management

## API Endpoints

### Telemetry
- `POST /api/telemetry` - Nhận dữ liệu từ devices
- `GET /api/devices/{id}/latest` - Lấy telemetry mới nhất
- `GET /api/devices/{id}/history` - Lịch sử telemetry

### AI Analysis
- `POST /api/ai/anomaly/detect` - Phát hiện bất thường
- `POST /api/ai/forecast/soil-moisture` - Dự đoán độ ẩm
- `POST /api/ai/predict/leader-failure` - Dự đoán lỗi leader

### Commands
- `POST /api/command` - Gửi lệnh điều khiển

### Dashboard
- `GET /` - Dashboard chính

## Real-time Updates

Sử dụng Socket.IO để cập nhật real-time:
- `telemetry_update`: Dữ liệu telemetry mới + AI analysis
- `command_ack`: Xác nhận lệnh đã thực hiện

## AI Decision Engine

1. **Anomaly Detection**: Phát hiện sensor errors, leaks
2. **Moisture Forecasting**: Dự đoán độ ẩm trong 30 phút
3. **Leader Failure Prediction**: Đánh giá health của mesh network
4. **Decision Making**: Tự động quyết định tưới tiêu

## ESP32 Integration

ESP32 gửi telemetry qua MQTT:
```json
{
  "device_id": "DEV001",
  "soil_moisture": 45.2,
  "temperature": 28.5,
  "humidity": 65.0,
  "light": 75,
  "pump_state": "OFF",
  "rssi": -65,
  "node_role": "NODE"
}
```

## Database Schema

- **devices**: Thông tin thiết bị
- **telemetry**: Dữ liệu cảm biến
- **ai_results**: Kết quả AI analysis
- **commands**: Lịch sử lệnh
- **anomalies**: Bất thường phát hiện
- **irrigation_schedules**: Lịch tưới
- **system_logs**: Nhật ký hệ thống

## Chạy hệ thống

1. Khởi động MQTT broker (Mosquitto)
2. Chạy Flask app: `python app.py`
3. Upload ESP32 firmware
4. Truy cập dashboard tại http://localhost:5000

## Phát triển thêm

- Thêm authentication
- Implement user management
- Enhanced AI models (LSTM, Neural Networks)
- Mobile app integration
- Cloud deployment