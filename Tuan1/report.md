# BÁO CÁO LAB 1.1: THIẾT KẾ VÀ MÔ PHỎNG LUỒNG DỮ LIỆU CHO HỆ THỐNG AIoT

## Hệ thống tưới cây thông minh với mesh network và phát hiện bất thường

---

### 1. Thông tin nhóm

| Mục | Nội dung |
|-----|----------|
| Tên nhóm | Nhóm 4 |
| Thành viên | Nguyễn Quang Vinh, Phùng Mạnh Đức, Phạm Thành Vinh |
| Tên hệ thống | Smart Irrigation AIoT System with Mesh Network & Anomaly Detection |
| Người dùng mục tiêu | Chủ trang trại, người vận hành hệ thống tưới tiêu |

---

### 2. Bối cảnh thực tế

**Vấn đề thực tế cần giải quyết:**
- Tưới cây thủ công tốn thời gian và không chính xác
- Mất kết nối giữa các node trong vườn lớn
- Không phát hiện sớm cảm biến lỗi hoặc rò rỉ nước
- Lãng phí nước do tưới sai thời điểm
- Không có khả năng dự báo nhu cầu nước trong tương lai
- Khi một node/leader chết, toàn bộ vùng mất điều khiển

**Giá trị của AI:**
- Phát hiện sớm bất thường (sensor lỗi, rò rỉ)
- Dự báo độ ẩm đất để tưới đúng thời điểm
- Dự báo leader failure để failover kịp thời
- Tiết kiệm nước >20% so với tưới thủ công

**Rủi ro nếu AI sai:**
- Tưới sai thời điểm gây hại cây trồng
- Cảnh báo giả gây phiền người dùng
- Bỏ sót tình huống đất quá khô

---

### 3. Sơ đồ kiến trúc AIoT

**Giá trị của AI đã triển khai:**
- ✅ **Anomaly Detection**: Phát hiện sớm bất thường (sensor lỗi, rò rỉ) → **Isolation Forest ML model**
- ✅ **Moisture Forecasting**: Dự báo độ ẩm đất để tưới đúng thời điểm → **Random Forest Regressor**
- ✅ **Leader Failure Prediction**: Dự báo leader failure để failover kịp thời → **RSSI-based scoring**
- ✅ **Tiết kiệm nước**: >20% so với tưới thủ công thông qua tự động hóa thông minh
- ✅ **Real-time Decision Engine**: Tự động ra quyết định tưới dựa trên confidence scores

**Mitigations cho các rủi ro:**
- Tưới sai thời điểm gây hại cây → Mitigated bằng confidence scoring > 80%
- Cảnh báo giả gây phiền người dùng → Require human approval cho MEDIUM risk decisions
- Bỏ sót tình huống đất quá khô → Fallback to manual control + critical alerts

---

### 3. Kiến trúc hệ thống (Refactored)

```
┌──────────────────────────────────────────────────────────────────┐
│                    DASHBOARD (Web UI)                            │
│  ✓ Dynamic device selector   ✓ Real-time charts                 │
│  ✓ Anomaly alerts            ✓ Command panel (ON/OFF)           │
│  ✓ Auto-refresh (30s)        ✓ Empty state with sample data btn │
└────────────────────┬─────────────────────────────────────────────┘
                     │ WebSocket (Socket.IO) & REST APIs
        ┌────────────┴──────────────────┐
        │                               │
┌───────▼──────────────────┐   ┌────────▼──────────────────────┐
│    FLASK APP (app.py)     │   │  MQTT HANDLER (mqtt_handler) │
│  ✓ REST API Endpoints     │   │  ✓ MQTT Client (Mosquitto)   │
│  ✓ SocketIO Events        │   │  ✓ Telemetry Reception       │
│  ✓ AI Decision Engine     │   │  ✓ Command Publishing        │
│  ✓ Device selector logic  │   │  ✓ Callbacks to Flask        │
│  ✓ Setup endpoints        │   │  ✓ Real-time integration     │
└────────┬──────────────────┘   └────────┬──────────────────────┘
         │                               │
         │        ┌──────────────────────┘
         │        │
         │   ┌────▼─────────────────────────┐
         │   │  AI MODELS (train_model.py)  │
         │   │  ✓ Anomaly Detection (IF)    │
         │   │  ✓ Moisture Forecast (RF)    │
         │   │  ✓ Leader Failure Predict    │
         │   │  ✓ Auto-train on first run   │
         │   └────┬─────────────────────────┘
         │        │
         │   ┌────▼──────────────────────────┐
         └───┤ DATABASE (connect_database.py)│
             │  ✓ Supabase PostgreSQL        │
             │  ✓ Full CRUD Operations       │
             │  ✓ Connection Management      │
             │  ✓ Error handling             │
             └────┬──────────────────────────┘
                  │
         ┌────────┴──────────────────┐
         │  7 Database Tables:        │
         │  • devices                 │
         │  • telemetry (time-series) │
         │  • ai_results              │
         │  • commands                │
         │  • anomalies               │
         │  • irrigation_schedules    │
         │  • system_logs             │
         └────────────────────────────┘

                    ↓ MQTT (127.0.0.1:1883)

    ┌─────────────────────────────────────────────────────┐
    │         ESP32 Devices (Mesh Network)                │
    │  • DEV001 (LEADER) - Field A                       │
    │  • DEV002 (NODE) - Field A                         │
    │  • DEV003 (NODE) - Field B                         │
    │                                                     │
    │  Sensors:  Soil Moisture, DHT11, LDR              │
    │  Actuators: Relay (Pump)                          │
    └─────────────────────────────────────────────────────┘
```

---

### 4. Luồng dữ liệu chính

#### 4.1 Telemetry Ingestion (Real-time)
```
ESP32 device publishes MQTT message
    ↓
MQTT Broker (Mosquitto) receives on "smart_irrigation/telemetry"
    ↓
mqtt_handler.on_message() triggered
    ↓
save_telemetry(data) → Supabase telemetry table
    ↓
on_telemetry_received() callback invoked
    ↓
run_ai_analysis(data) → Run 3 AI models simultaneously
    ├─ anomaly_detection() → Isolation Forest
    ├─ moisture_forecasting() → Random Forest
    └─ leader_failure_prediction() → RSSI scoring
    ↓
save_ai_results() → Supabase ai_results table
    ↓
IF anomaly detected → save_anomalies() table
    ↓
socketio.emit('telemetry_update') → Dashboard (WebSocket)
    ↓
Decision Engine executes if action needed
```

#### 4.2 AI Decision Engine (Advanced Logic)
```
New telemetry received
    ↓
┌─── STEP 1: ANOMALY DETECTION ───┐
│  • Is reading out of range?       │
│    (soil_moisture < 0 || > 100)   │
│  • Is there sudden change?        │
│    (Z-score > 2.5)                │
│  • Detect water leak?             │
│    (drop > 20% when pump OFF)     │
└───────────────────────────────────┘
    ↓ IF ANOMALY → No automatic action, notify user
    ↓ IF NORMAL → Continue

┌─── STEP 2: MOISTURE FORECASTING ───┐
│  • Predict soil_moisture in 30min   │
│  • Calculate risk level:            │
│    - HIGH: predicted < 30%          │
│    - MEDIUM: 30-45%                 │
│    - LOW: > 45%                     │
└─────────────────────────────────────┘
    ↓

┌─── STEP 3: LEADER FAILURE CHECK ───┐
│  • Health score = 100 - penalties   │
│  • Penalties:                       │
│    - RSSI < -90: -40 points         │
│    - Last seen > 30s: -30 points    │
│  • Failure risk classification      │
└─────────────────────────────────────┘
    ↓

┌──── STEP 4: DECISION ENGINE ────┐
│  IF anomaly detected:             │
│    → action = "NONE"              │
│    → requires_confirmation = true │
│                                   │
│  IF HIGH risk + auto_mode:        │
│    IF confidence > 0.92:          │
│      → action = "PUMP_ON" ✓ AUTO  │
│    ELSE:                          │
│      → action = "RECOMMEND"       │
│      → requires_confirmation = true
│                                   │
│  IF pump ON + moisture > 55%:     │
│    → action = "PUMP_OFF" ✓ AUTO   │
│                                   │
│  ELSE:                            │
│    → action = "NONE"              │
│    → reason = "Conditions normal" │
└───────────────────────────────────┘
    ↓

┌──── STEP 5: COMMAND EXECUTION ────┐
│  Publish MQTT to:                 │
│  "smart_irrigation/command"       │
│  {                                │
│    "device_id": "DEV001",        │
│    "command": "ON",               │
│    "duration": 180,               │
│    "confidence": 0.92             │
│  }                                │
└────────────────────────────────────┘
    ↓
Saved to commands table + awaiting ACK
```

#### 4.3 Command Flow (Complete Cycle)
```
Dashboard UI
    ↓
User clicks "Bật bơm" (Turn ON pump)
    ↓
JavaScript: fetch('/api/command', {method: 'POST', body: {...}})
    ↓
Flask: send_manual_command() endpoint
    ↓
mqtt_send_command() → MQTT publish to "smart_irrigation/command"
    ↓
save_command() → Supabase commands table (status="sent")
    ↓
ESP32 receives MQTT message
    ↓
ESP32 executes command (turns relay ON)
    ↓
ESP32 sends ACK to "smart_irrigation/ack"
    ↓
mqtt_handler.on_message() receives ACK
    ↓
on_ack_received() callback
    ↓
update_command_status() → Supabase (status="executed", ack_received=true)
    ↓
socketio.emit('command_ack', ack_data)
    ↓
Dashboard receives WebSocket event
    ↓
UI updates: "✓ Command executed successfully"
    ↓
Auto-refresh telemetry after 2s
```

---

Sơ đồ bao gồm 4 tầng chính:
1. **Edge Layer**: ESP32 nodes với cảm biến (độ ẩm, DHT11, LDR, relay) và kết nối LoRa mesh
2. **Gateway/Backend Layer**: Flask API, Supabase database, MQTT broker
3. **AI Services**: Anomaly Detection, Moisture Forecasting, Leader Failure Prediction
4. **Dashboard Layer**: Real-time charts, alerts, command panel, feedback loop

---

### 4. Bảng dữ liệu cần thu thập

| STT | Tên trường | Kiểu dữ liệu | Nguồn | Tần suất | Dùng cho AI/hệ thống |
|-----|------------|--------------|-------|----------|----------------------|
| 1 | device_id | string | ESP32 | Mỗi bản tin | Phân biệt node |
| 2 | timestamp | datetime | Backend | Mỗi bản tin | Chuỗi thời gian |
| 3 | soil_moisture | float (0-100%) | Cảm biến đất | 25 giây/lần | Dự báo, phát hiện rò rỉ |
| 4 | temperature | float (°C) | DHT11 | 25 giây/lần | Dự báo tốc độ khô |
| 5 | humidity | float (%) | DHT11 | 25 giây/lần | Dự báo nấm bệnh |
| 6 | light | int (0-100%) | LDR | 25 giây/lần | Phân tích ảnh hưởng ánh sáng |
| 7 | pump_state | boolean | Relay | Khi thay đổi | Đánh giá hiệu quả tưới |
| 8 | rssi | int (dBm) | LoRa | 10-30s | Phát hiện mất kết nối |
| 9 | node_role | string | Leader election | Khi thay đổi | Quản lý topology |
| 10 | mesh_link_quality | int | Mesh discovery | 45 giây | Đánh giá chất lượng mạng |

---

### 5. 03 JSON telemetry mẫu

*(Đã trình bày ở Phần 4)*

1. **Bản tin bình thường**: Dữ liệu sensor bình thường, pump OFF
2. **Bản tin bất thường**: sensor_timeout, giá trị -999, RSSI kém
3. **Bản tin sau điều khiển**: pump ON, kèm duration, command_source, confidence

---

### 6. Module AI (03 module)

| STT | Module AI | Đầu vào | Đầu ra | Vai trò | Nơi chạy |
|-----|-----------|---------|--------|---------|----------|
| 1 | Anomaly Detection | soil_moisture, temp, pump_state, rssi (30 phút) | is_anomaly, anomaly_score, reason | Phát hiện sensor lỗi, rò rỉ | Backend |
| 2 | Moisture Forecasting | soil_moisture, temp, humidity, light (2h) | predicted_30min, predicted_60min, risk_level | Dự báo độ ẩm, khuyến nghị tưới | Backend |
| 3 | Leader Failure Prediction | rssi_history, node_role, last_seen, packet_loss | health_score, failure_risk, action | Dự báo leader chết, failover | Backend |

---

### 7. Feedback loop

*(Đã trình bày ở Phần 6)*

**Luồng xử lý:**
1. Sensor → ESP32 → MQTT → Backend
2. Backend → AI Analysis (3 modules đồng thời)
3. AI → Decision Engine (xét confidence, auto_mode)
4. Decision → MQTT Command → ESP32 → Relay
5. ESP32 → ACK → Backend → Update command status
6. Backend → Dashboard real-time update
7. Đánh giá hiệu quả → Lưu vào ai_results để cải thiện model

---

### 8. Tiêu chí đánh giá

**AI Metrics:**
- Precision >85%, Recall >90%, F1 >87%
- MAE <5%, False Alarm Rate <5%

**System Metrics:**
- End-to-End Latency <5 giây
- Mesh Recovery Time <30 giây
- Packet Loss Rate <5%
- System Uptime >99.5%
- Water Saving Rate >20%

**Business Metrics:**
- User Trust Score >70%
- Manual Overrides <3 lần/ngày
- Maintenance Cost Reduction >30%

---

### 9. Phân tích rủi ro và cơ chế an toàn

**Rủi ro & Giải pháp:**

| Rủi ro | Mức độ | Giải pháp |
|--------|--------|------------|
| Dữ liệu sai từ cảm biến | CAO | Redundancy, anomaly detection, calibration |
| Model dự đoán sai | TRUNG BÌNH | Human-in-the-loop, confidence >80%, retrain weekly |
| Mất kết nối mesh | CAO | Auto leader election, heartbeat, fallback |

**Cơ chế an toàn:**
1. Confidence threshold >80% mới tự động điều khiển
2. Giới hạn thời gian bơm tối đa (5 phút/lần)
3. Kill switch khẩn cấp trên dashboard
4. Log đầy đủ mọi hành động điều khiển

---

### 10. API endpoints dự kiến

| STT | API | Method | Endpoint | Mục đích |
|-----|-----|--------|----------|----------|
| 1 | Telemetry | POST | /api/telemetry | Nhận dữ liệu sensor |
| 2 | Anomaly Detection | POST | /api/ai/anomaly/detect | Phát hiện bất thường |
| 3 | Moisture Forecast | POST | /api/ai/forecast/soil-moisture | Dự báo độ ẩm |
| 4 | Leader Failure | POST | /api/ai/predict/leader-failure | Dự báo leader chết |
| 5 | Command | POST | /api/command | Gửi lệnh điều khiển |
| 6 | Latest Data | GET | /api/devices/{id}/latest | Lấy dữ liệu mới nhất |
| 7 | History | GET | /api/devices/{id}/history | Lấy lịch sử |
| 8 | Anomalies | GET | /api/anomalies | Lấy danh sách bất thường |

---

### 11. Database schema (Supabase)

*(Đã trình bày ở Phần 9)*

Gồm 5 bảng: devices, telemetry, ai_results, commands, anomalies.

---

### 12. Kết luận

Hệ thống Smart Irrigation AIoT đã được thiết kế hoàn chỉnh với đầy đủ:
- Kiến trúc 4 tầng (Edge → Backend → AI → Dashboard)
- 3 module AI với input/output rõ ràng
- Feedback loop đầy đủ từ sensor đến actuator
- Cơ chế an toàn và đánh giá rủi ro
- Dashboard sinh động với animation, real-time charts
- API endpoints và database schema đầy đủ

**Hướng phát triển:**
- Triển khai LoRa mesh thực tế trên ESP32
- Train LSTM model với dữ liệu thực từ trang trại
- Tích hợp thêm computer vision để phát hiện sâu bệnh
- Triển khai lên cloud (AWS/GCP) cho scalability

---
*Báo cáo hoàn thành ngày: 05/05/2026*
*Nhóm 4 - Triển khai, phát triển ứng dụng AI và IoT*