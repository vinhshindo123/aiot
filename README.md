# AIoT Course Review

Đây là tổng hợp nội dung của 8 tuần lab AIoT trong workspace `AIoT`.

## Tổng quan chung

Dự án chứa tám tuần thực hành AIoT:

- `Tuan1/` — Xây dựng hệ thống tưới tiêu thông minh AIoT với MQTT, Flask, Supabase và ESP32.
- `Tuan2/` — Chuẩn bị dữ liệu chất lượng không khí, huấn luyện baseline model và deploy bằng FastAPI.
- `Tuan3/` — Phát hiện bất thường thời gian thực, tạo event intelligence và API anomaly detection.
- `Tuan4/` — Forecasting & model training cho dữ liệu IoT, so sánh pipeline dự báo và đánh giá mô hình.
- `Tuan5/` — Dockerized multi-model AI inference service cho input telemetry và ảnh, dùng FastAPI, Docker Compose và ONNX.
- `Tuan6/` — Computer vision & AI vision upgrade: camera as IoT sensor, motion + Faster R-CNN detection, dashboard và event logging.
- `Tuan7/` — Object detection & computer vision model zoo: YOLO detection, vision task engines (tracking, pose, face, OCR, segmentation), model diversity.
- `Tuan8/` — LLM reasoning & context-aware decision: tổng hợp tất cả evidence từ các tuần trước, dùng LLM để giải thích, trả decision với safety gate.

## Mục lục

- [Tuần 1 — Smart Irrigation AIoT](#tuần-1---smart-irrigation-aiot)
- [Tuần 2 — Air Quality Data Preparation và Deploy Baseline](#tuần-2---air-quality-data-preparation-và-deploy-baseline)
- [Tuần 3 — Anomaly Detection & Event Intelligence](#tuần-3---anomaly-detection--event-intelligence)
- [Tuần 4 — Forecasting & Model Training](#tuần-4---forecasting--model-training)
- [Tuần 5 — Dockerized Multi-Model AI Inference Service](#tuần-5---dockerized-multi-model-ai-inference-service)
- [Tuần 6 — Computer Vision & AI Vision Upgrade](#tuần-6---computer-vision--ai-vision-upgrade)
- [Tuần 7 — Object Detection & Computer Vision Model Zoo](#tuần-7---object-detection--computer-vision-model-zoo)
- [Tuần 8 — LLM Reasoning & Context-aware Decision](#tuần-8---llm-reasoning--context-aware-decision)
- [Ghi chú thêm](#ghi-chú-thêm)
- [Cách chạy nhanh mỗi tuần](#cách-chạy-nhanh-mỗi-tuần)

---

## Tuần 1 — Smart Irrigation AIoT

### Mục tiêu

Tuần 1 tập trung vào xây dựng một giải pháp AIoT hoàn chỉnh cho tưới tiêu thông minh:

- Kết nối ESP32 với backend qua MQTT.
- Lưu telemetry vào database Supabase.
- Huấn luyện model AI để phát hiện bất thường và dự báo độ ẩm.
- Triển khai dashboard web và vòng feedback điều khiển bơm.

### Cấu trúc chính

- `Tuan1/app.py` — Flask app chính, API và Socket.IO dashboard.
- `Tuan1/mqtt_handler.py` — Kết nối MQTT, nhận telemetry và gửi command.
- `Tuan1/connect_database.py` — Tương tác Supabase, lưu telemetry, kết quả AI và anomalies.
- `Tuan1/train_model.py` — Sinh dữ liệu huấn luyện mẫu, train Isolation Forest và RandomForestRegressor.
- `Tuan1/esp32_smart_irrigation/esp32_smart_irrigation.ino` — Firmware ESP32 mẫu.
- `Tuan1/templates/dashboard.html` — Giao diện dashboard.
- `Tuan1/schema.sql` — Cấu trúc database.

### Những gì đã làm

- Xây dựng pipeline realtime từ sensor về backend.
- Train mô hình anomaly detection để phát hiện noisy/outlier trong cảm biến.
- Train mô hình forecast độ ẩm đất cho ra dự báo 30/60 phút.
- Tạo decision engine tự động đề xuất bật/tắt bơm.
- Triển khai dashboard hiển thị telemetry, AI result và confirm command.

### Ứng dụng

- Giám sát hệ thống nông nghiệp thông minh.
- Phát hiện sensor lỗi hoặc leak.
- Dự báo điều kiện độ ẩm và tự động tưới tiêu.
- Nâng cao AIoT bằng vòng feedback command từ dashboard đến thiết bị.

### Tài liệu PDF liên quan

- `Tuan1/pdf/Bài 1.pdf` — Giới thiệu khóa học AIoT, kiến trúc và pipeline.
- `Tuan1/pdf/Lab 1.1.pdf` — Lab 1.1: thiết kế luồng dữ liệu, JSON telemetry mẫu, AI module và rủi ro.
- `Tuan1/pdf/Lab 1.pdf` — Lab 1 tổng quan về AIoT system và deployment pipeline.

---

## Tuần 2 — Air Quality Data Preparation và Deploy Baseline

### Mục tiêu

Tuần 2 tập trung vào xử lý dữ liệu IoT để làm tiền đề cho AI:

- Tải hoặc sinh dữ liệu chất lượng không khí.
- Kiểm tra schema, clean data và feature engineering.
- Train model baseline (Linear Regression / Random Forest) để dự đoán CO.
- Deploy mô hình qua FastAPI và frontend dashboard.

### Cấu trúc chính

- `Tuan2/src/data_utils.py` — Download dataset, clean, feature engineering, build model bundle.
- `Tuan2/src/run_training_pipeline.py` — Chạy pipeline đầy đủ từ data đến model.
- `Tuan2/src/app.py` — FastAPI inference service và API dashboard.
- `Tuan2/src/test_api.py` — Kiểm tra API predict.
- `Tuan2/frontend/` — UI dashboard tương tác.
- `Tuan2/notebooks/01_data_prep_baseline_deploy_ready.ipynb` — Notebook xử lý dữ liệu và huấn luyện.
- `Tuan2/data/feature_dataset.csv` — Feature dataset sau xử lý.
- `Tuan2/models/air_quality_model.joblib` — Mô hình trained.

### Những gì đã làm

- Xây dựng pipeline data readiness: download dataset UCI Air Quality, fallback dữ liệu khi offline.
- Tổng hợp, làm sạch và chuẩn hóa dữ liệu telemetry IoT.
- Tạo feature phù hợp cho regression: giá trị cảm biến, giờ, ngày trong tuần.
- Train baseline model để dự đoán CO.
- Sinh `outputs/decision_log.csv` với kết quả dự đoán và decision rule.
- Đóng gói API `/predict` và dashboard visual.

### Ứng dụng

- Mô phỏng hệ thống giám sát chất lượng không khí.
- Dùng AI để dự đoán CO và đánh giá mức độ ô nhiễm.
- Tạo API inference cho các ứng dụng dashboard hoặc hệ thống giám sát.
- Nâng cao khả năng chuyển từ dữ liệu IoT thô sang dữ liệu model-ready.

### Tài liệu PDF liên quan

- `Tuan2/pdf/Bài 2.pdf` — Lab 2: Data readiness, IoT data cleaning, feature engineering, baseline model và deployment.

---

## Tuần 3 — Anomaly Detection & Event Intelligence

### Mục tiêu

Tuần 3 là bước nâng cao của AIoT: phát hiện bất thường trên chuỗi thời gian và tạo event intelligence:

- Xây dựng pipeline anomaly detection cho dữ liệu IoT/hydroponics.
- Train Isolation Forest và demo autoencoder.
- Chuyển kết quả anomaly thành event log, severity và decision.
- Triển khai API `/detect-anomaly` để phục vụ hệ thống trực tuyến.

### Cấu trúc chính

- `Tuan3/src/download_data.py` — Sinh dữ liệu demo hoặc chuyển đổi dataset hydroponics thực.
- `Tuan3/src/train_anomaly.py` — Train Isolation Forest và autoencoder demo, lưu metrics, predictions, event log.
- `Tuan3/src/app.py` — FastAPI anomaly detection service.
- `Tuan3/src/utils.py` — Xử lý dữ liệu, chọn feature, tạo event, đánh giá.
- `Tuan3/src/static/dashboard.html` — Dashboard hiển thị lịch sử và kết quả anomaly.

### Những gì đã làm

- Thiết kế giải pháp anomaly event intelligence: từ telemetry đến anomaly score và event.
- Sử dụng dataset NAB ambient temperature hoặc dữ liệu hydroponics để train.
- Áp dụng time split cho dữ liệu chuỗi thời gian.
- Lưu `outputs/anomaly_event_log.csv`, `outputs/iforest_metrics.json`, `outputs/autoencoder_metrics.json`.
- Cài đặt API `/detect-anomaly` để nhận history telemetry và trả về anomaly score, severity, decision và explanation.

### Ứng dụng

- Giám sát thiết bị/hệ thống IoT liên tục với cảnh báo bất thường.
- Chuyển anomaly detection thành event intelligence để vận hành an toàn.
- Tích hợp API cho hệ thống cảnh báo, dashboard hoặc operational center.
- Làm nền tảng cho predictive maintenance và công tác điều hành tự động.

### Tài liệu PDF liên quan

- `Tuan3/pdf/Buổi 3.pdf` — Slide bài học Lab 3.
- `Tuan3/pdf/Lab_3_Anomaly_Detection_Event_Intelligence_AIOT_v3.pdf` — Lab 3 chi tiết, bao gồm anomaly detection, event intelligence và API `/detect-anomaly`.

---

## Tuần 4 — Forecasting & Model Training

### Mục tiêu

Tuần 4 mở rộng sang forecasting và model training chuyên sâu cho dữ liệu IoT:

- Biến dữ liệu IoT thành bài toán forecasting.
- Xây dựng feature engineering cho chuỗi thời gian với lag, rolling stats, time features và interaction.
- Train các model dự báo và so sánh với baseline.
- Đọc metrics dự báo như MAE/RMSE/MAPE và đánh giá hành vi model.

### Cấu trúc chính

- `Tuan4/Lab_01/README.md` — Forecasting nhiệt độ NODE_03 với dataset `lab4_forecast_NODE03_augmented.csv`.
- `Tuan4/Lab_01/src/train_forecast.py` — Pipeline train forecast với Linear Regression, Random Forest, Gradient Boosting.
- `Tuan4/Lab_01/src/plot_results.py` — Biểu đồ forecast vs actual và error.
- `Tuan4/Lab_01/src/test_api_local.py` — Test logic API local.
- `Tuan4/Lab_02/README.md` — Lab 4 v4 upgrade: AI model training cho UCI appliances energy và CO2 forecasting.
- `Tuan4/Lab_02/src/train_classical_models.py` — Train và so sánh nhiều model classical.
- `Tuan4/Lab_02/src/compare_two_datasets.py` — So sánh model trên hai dataset.

### Những gì đã làm

- `Tuan4/Lab_01` xây dựng pipeline dự báo nhiệt độ 5/10/15/25 phút cho NODE_03.
- Tạo feature: sensor hiện tại, lag, rolling statistics, time/cycle features, delta và interaction.
- Huấn luyện model và lưu output: `models/forecast_model_bundle_v1.joblib`, `outputs/forecast_metrics.json`, `outputs/forecast_test_predictions.csv`.
- `Tuan4/Lab_02` mở rộng bài toán với hai dataset UCI: Appliances Energy Prediction và Occupancy Detection / CO2 Forecasting.
- Triển khai toàn bộ pipeline từ download data, prepare dataset, train, compare, và test local.
- Có mở rộng tuỳ chọn chạy LSTM để so sánh với model classical.

### Ứng dụng

- Dự báo môi trường và năng lượng trong hệ thống IoT.
- Dùng forecast để đánh giá rủi ro vận hành, ra khuyến nghị và kiểm duyệt an toàn.
- Tiền đề cho predictive maintenance và scheduling thông minh.
- So sánh model trên nhiều dataset giúp đánh giá độ tổng quát.

### Tài liệu & output liên quan

- `Tuan4/Lab_01/README.md`
- `Tuan4/Lab_02/README.md`
- `Tuan4/Lab_01/outputs/forecast_metrics.json`
- `Tuan4/Lab_01/outputs/forecast_test_predictions.csv`
- `Tuan4/Lab_01/outputs/forecast_log.csv`
- `Tuan4/Lab_01/figures/forecast_vs_actual.png`
- `Tuan4/Lab_02/outputs/model_comparison.csv`
- `Tuan4/Lab_02/outputs/metrics_all_models.csv`
- `Tuan4/Lab_02/outputs/model_card_appliances.md`
- `Tuan4/Lab_02/outputs/model_card_co2.md`

---

## Tuần 5 — Dockerized Multi-Model AI Inference Service

### Mục tiêu

Tuần 5 xây dựng một dịch vụ inference AIoT đa năng cho cả telemetry và ảnh:

- Triển khai FastAPI service hỗ trợ các endpoint sensor và ảnh.
- Kéo model ảnh ONNX nhẹ để demo inference.
- Đóng gói service bằng Docker và Docker Compose.
- So sánh chạy local và container.

### Cấu trúc chính

- `Tuan5/Lab_01/app/` — FastAPI application.
- `Tuan5/Lab_01/models/vision/` — ONNX model ảnh và nhãn ImageNet.
- `Tuan5/Lab_01/scripts/` — Script tải model và smoke test.
- `Tuan5/Lab_01/sample_images/` — Ảnh mẫu để test upload.
- `Tuan5/Lab_01/sample_requests/` — JSON mẫu cho API sensor.
- `Tuan5/Lab_01/Dockerfile` — Build image Docker.
- `Tuan5/Lab_01/docker-compose.yml` — Chạy dịch vụ bằng Compose.

### Những gì đã làm

- Tạo FastAPI inference service cho nhiều loại đầu vào: `/detect-anomaly`, `/forecast`, `/predict-risk`, `/classify-image`, `/classify-image-annotated`.
- Cung cấp giao diện upload ảnh demo tại `/classify-image-demo`.
- Hướng dẫn chạy local, build Docker và chạy Docker Compose.
- Tích hợp smoke test, log output, và tài liệu Docker cho sinh viên.

### Chạy nhanh

1. `cd Tuan5/Lab_01`
2. `python -m venv .venv`
3. `source .venv/bin/activate`
4. `pip install -r requirements.txt`
5. `python scripts/download_vision_model.py`
6. `uvicorn app.main:app --reload`

Hoặc chạy Docker:

1. `cd Tuan5/Lab_01`
2. `docker compose up --build`

### Tài liệu liên quan

- `Tuan5/Lab_01/README.md`
- `Tuan5/Lab_01/RUN_GUIDE.md`
- `Tuan5/Lab_01/docs/`

---

## Tuần 6 — Computer Vision & AI Vision Upgrade

### Mục tiêu

Tuần 6 đưa camera vào hệ thống AIoT như một cảm biến hình ảnh và nâng cấp bằng môđul phát hiện đối tượng:

- Triển khai stream camera, snapshot, và motion detection.
- Sinh metadata và event từ ảnh/stream, lưu logs để phân tích.
- Nâng cấp AI bằng Faster R-CNN (torchvision) để phát hiện `person`/`animal` với bounding box.
- Tối ưu pipeline để AI chạy bất đồng bộ, tránh làm gián đoạn luồng video.

### Cấu trúc chính

- `Tuan6/Lab_01/` — Lab 6 cơ bản: stream, snapshot, motion, preprocess, metadata, dashboard (`run_lab6_demo.py`, `app.py`, `index.html`).
- `Tuan6/Lab_upgrade/` — Bản nâng cấp: Faster R-CNN detection, async inference, snapshot + annotated images, `outputs/ai_detection_log.csv`.

### Những gì đã làm

- `Tuan6/Lab_01` cung cấp demo camera/stream như một sensor, lưu ảnh và event, có script chạy thử `run_lab6_demo.py`.
- `Tuan6/Lab_upgrade` triển khai AI detection bằng `Faster R-CNN`, lưu snapshot đã gắn bounding box, ghi log detection và event.

### Chạy nhanh (Lab_01)

1. `cd Tuan6/Lab_01`
2. `python -m venv .venv`
3. `source .venv/bin/activate`
4. `pip install -r requirements.txt`
5. `python run_lab6_demo.py`
6. `uvicorn app:app --reload --host 0.0.0.0 --port 8000`

Mở: `http://127.0.0.1:8000/` và `http://127.0.0.1:8000/docs`

### Chạy nhanh (Lab_upgrade)

1. `cd Tuan6/Lab_upgrade`
2. `python -m venv .venv`
3. `source .venv/bin/activate`
4. `pip install fastapi uvicorn[standard] opencv-python pillow numpy torch torchvision`
5. `uvicorn app:app --reload --host 0.0.0.0 --port 8000`

Mở: `http://127.0.0.1:8000/`

---

## Tuần 7 — Object Detection & Computer Vision Model Zoo

### Mục tiêu

Tuần 7 phát triển trên nền tảng Lab 6 về camera stream, motion, event logging. Mục tiêu:

- Chạy object detection với YOLO nano để phát hiện vật thể, ghi bounding box và confidence.
- Mở rộng sang nhiều task thị giác máy tính: tracking, pose estimation, face detection, OCR, segmentation, motion.
- Tạo model zoo cho phép sinh viên lựa chọn và so sánh vision task khác nhau.
- Lưu detection log, vision event, snapshot với annotation.

### Cấu trúc chính

- `Tuan7/Lab_01/` — Lab 7 cơ bản: YOLO object detection, camera stream, bounding box, confidence, detection log, `run_lab7_demo.py`.
- `Tuan7/Lab_Upgrade/` — Model zoo: nhiều engine thị giác (YOLO, tracking, pose, hand, face, OCR, segmentation, motion), fallback support, `vision_engines.py`.

### Những gì đã làm

- `Tuan7/Lab_01` triển khai YOLO nano để phát hiện object, ghi confidence, class, latency; có fallback contour detector nếu không tải được model.
- `Tuan7/Lab_Upgrade` cung cấp `vision_engines.py` với các engine: detection, tracking, pose, hand, face, OCR, segmentation, motion detection; support fallback để luôn chạy được.
- Tạo dashboard chọn vision task, quan sát kết quả real-time, lưu log detection và event.
- Lưu `outputs/detection_log.csv` và `outputs/vision_event_log.csv` để phân tích.

### Chạy nhanh (Lab_01)

1. `cd Tuan7/Lab_01`
2. `python -m venv .venv`
3. `source .venv/bin/activate`
4. `pip install -r requirements.txt`
5. `python run_lab7_demo.py`
6. `uvicorn app:app --reload --host 0.0.0.0 --port 8000`

Mở: `http://127.0.0.1:8000/`

### Chạy nhanh (Lab_Upgrade)

1. `cd Tuan7/Lab_Upgrade`
2. `python -m venv .venv`
3. `source .venv/bin/activate`
4. `pip install -r requirements_core.txt`
5. `python run_model_zoo_demo.py`
6. `uvicorn app:app --reload --host 0.0.0.0 --port 8000`

Mở: `http://127.0.0.1:8000/`

Nếu muốn chạy các model nâng cấp, cài thêm từ `requirements_optional.txt`.

---

## Tuần 8 — LLM Reasoning & Context-aware Decision

### Mục tiêu

Tuần 8 là bước hoàn chỉnh: tổng hợp tất cả evidence từ các tuần trước (telemetry, anomaly, forecast, camera, vision) và sử dụng LLM để:

- Lý luận multi-context: sensor data + AI models + camera/vision events.
- Giải thích quyết định một cách tự nhiên và dễ hiểu.
- Tạo decision JSON với reasoning.
- Áp dụng safety gate để kiểm tra quyết định trước khi thực thi.

### Cấu trúc chính

- `Tuan8/Lab01/app.py` — FastAPI backend, dashboard, tích hợp LLM reasoning.
- `Tuan8/Lab01/vision_engines.py` — Reuse từ Lab 7 Upgrade (vision tasks).
- `Tuan8/Lab01/llm_reasoner.py` — LLM reasoning, context synthesis, decision explanation.
- `Tuan8/Lab01/index.html` — Dashboard ba tầng: sensor-only, sensor+AI, sensor+AI+LLM.
- `Tuan8/Lab01/run_lab8_demo.py` — Demo không cần camera/model thật.

### Chế độ chạy LLM

- **mock**: Luôn chạy được, không cần Internet / API key / Ollama. Dùng để demo.
- **local**: Gọi Ollama tại `http://localhost:11434`, ví dụ model `qwen3:1.7b`.
- **api**: Placeholder/fallback giảng viên gắn API cloud (OpenAI, Anthropic, v.v.).

### Những gì đã làm

- Tạo dashboard ba tầng so sánh decision:
  1. Sensor only: rule cứng dựa trên telemetry.
  2. Sensor + AI models: thêm evidence từ Lab 3 (anomaly), Lab 4 (forecast), Lab 6/7 (motion/vision).
  3. Sensor + AI models + LLM: LLM tổng hợp context, giải thích, trả JSON decision, safety gate kiểm tra.
- Tích hợp LLM reasoning: tạo prompt từ sensor data + AI results, gọi LLM (mock/local/api), parse decision JSON.
- Lưu `outputs/reasoning_log.csv` với context, prompt, response, decision, safety check result.
- Hỗ trợ Ollama local: giảng viên có thể tải model (ví dụ `qwen3:1.7b` ~2GB) để chạy locally.

### Chạy nhanh

1. `cd Tuan8/Lab01`
2. `python -m venv .venv`
3. `source .venv/bin/activate`
4. `pip install -r requirements.txt`
5. `python run_lab8_demo.py`
6. `uvicorn app:app --reload --host 0.0.0.0 --port 8000`

Mở: `http://127.0.0.1:8000/`

**Chạy với LLM local (Ollama):**

1. Cài Ollama: https://ollama.ai
2. Tải model: `ollama pull qwen3:1.7b`
3. Chạy Ollama: `ollama serve`
4. Đặt `LLM_MODE=local` trong `.env` hoặc code
5. Chạy app: `uvicorn app:app --reload`

---

## Ghi chú thêm

- **Luồng học tập**: Tuần 1-3 xây dựng nền tảng AIoT (system, data, anomaly). Tuần 4 nâng cao model (forecasting). Tuần 5 deployment (Docker). Tuần 6-7 thị giác (camera, detection, model zoo). Tuần 8 tổng hợp (LLM reasoning + decision).
- **Mục tiêu chung**: `sensor -> backend -> data-ready -> model -> decision -> action`. Mỗi tuần thêm một lớp độ phức tạp và khả năng.
- **Tài liệu PDF**: Cung cấp bài học nền tảng về AIoT architecture, data pipeline, model deployment.
- **Evidence gathering**: Tuần 1-4 tập trung telemetry; Tuần 5-7 thêm multi-modality (ONNX, camera, detection); Tuần 8 tổng hợp decision.

---

## Cách chạy nhanh mỗi tuần

### Tuần 1
```bash
cd Tuan1
pip install -r requirements.txt
python train_model.py
python app.py
```

### Tuần 2
```bash
cd Tuan2
python -m venv T2_venv
source T2_venv/bin/activate
pip install -r requirements.txt
python src/run_training_pipeline.py
uvicorn src.app:app --reload --host 127.0.0.1 --port 8000
```

### Tuần 3
```bash
cd Tuan3
source T3_venv/bin/activate
pip install -r requirements.txt
python src/download_data.py
python src/train_anomaly.py
uvicorn src.app:app --reload
```

### Tuần 4 (Lab_01)
```bash
cd Tuan4/Lab_01
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python src/train_forecast.py
python src/plot_results.py
```

### Tuần 4 (Lab_02)
```bash
cd Tuan4/Lab_02
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python src/download_data.py
python src/prepare_datasets.py
python src/train_classical_models.py
python src/plot_results.py
```

### Tuần 5
```bash
cd Tuan5/Lab_01
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/download_vision_model.py
uvicorn app.main:app --reload
```

Hoặc chạy Docker:
```bash
cd Tuan5/Lab_01
docker compose up --build
```

### Tuần 6 (Lab_01)
```bash
cd Tuan6/Lab_01
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run_lab6_demo.py
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### Tuần 6 (Lab_upgrade)
```bash
cd Tuan6/Lab_upgrade
python -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn[standard] opencv-python pillow numpy torch torchvision
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### Tuần 7 (Lab_01)
```bash
cd Tuan7/Lab_01
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run_lab7_demo.py
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### Tuần 7 (Lab_Upgrade)
```bash
cd Tuan7/Lab_Upgrade
python -m venv .venv
source .venv/bin/activate
pip install -r requirements_core.txt
python run_model_zoo_demo.py
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### Tuần 8
```bash
cd Tuan8/Lab01
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run_lab8_demo.py
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Hoặc chạy với Ollama local:
```bash
# Terminal 1: Chạy Ollama
ollama serve

# Terminal 2: Chạy app (sau khi Ollama đã running)
cd Tuan8/Lab01
export LLM_MODE=local
uvicorn app:app --reload
```

---

**Ghi chú cuối**: Đây là khóa học AIoT toàn diện bao gồm từ tế nhi đến advanced: telemetry, data handling, model training, deployment, computer vision, và reasoning-based decision making dựa trên LLM.
