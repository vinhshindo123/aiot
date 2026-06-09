# AIoT Course Review

Đây là tổng hợp nội dung của 5 tuần lab AIoT trong workspace `AIoT`.

## Tổng quan chung

Dự án chứa năm tuần thực hành AIoT:

- `Tuan1/` — Xây dựng hệ thống tưới tiêu thông minh AIoT với MQTT, Flask, Supabase và ESP32.
- `Tuan2/` — Chuẩn bị dữ liệu chất lượng không khí, huấn luyện baseline model và deploy bằng FastAPI.
- `Tuan3/` — Phát hiện bất thường thời gian thực, tạo event intelligence và API anomaly detection.
- `Tuan4/` — Forecasting & model training cho dữ liệu IoT, so sánh pipeline dự báo và đánh giá mô hình.
- `Tuan5/` — Dockerized multi-model AI inference service cho input telemetry và ảnh, dùng FastAPI, Docker Compose và ONNX.

## Mục lục

- [Tuần 1 — Smart Irrigation AIoT](#tuần-1---smart-irrigation-aiot)
- [Tuần 2 — Air Quality Data Preparation và Deploy Baseline](#tuần-2---air-quality-data-preparation-và-deploy-baseline)
- [Tuần 3 — Anomaly Detection & Event Intelligence](#tuần-3---anomaly-detection--event-intelligence)
- [Tuần 4 — Forecasting & Model Training](#tuần-4---forecasting--model-training)
- [Tuần 5 — Dockerized Multi-Model AI Inference Service](#tuần-5---dockerized-multi-model-ai-inference-service)
- [Ghi chú thêm](#ghi-chú-thêm)
- [Cách chạy nhanh mỗi tuần](#cách-chạy-nhanh-mỗi-tuần)

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

## Ghi chú thêm

- Tài liệu PDF cung cấp bài học nền tảng: từ thiết kế AIoT, luồng dữ liệu, dữ liệu IoT chuẩn, đến anomaly detection và deployment.
- Mục tiêu của toàn bộ dự án là xây dựng các pipeline AIoT có tính thực tế: `sensor -> backend -> data-ready -> model -> decision -> action`.
- Mỗi tuần là một bước: tuần 1 làm hệ thống AIoT cơ bản; tuần 2 tập trung data và baseline; tuần 3 tập trung anomaly/event intelligence.

## Cách chạy nhanh mỗi tuần

### Tuần 1
1. `cd Tuan1`
2. `pip install -r requirements.txt`
3. `python train_model.py`
4. `python app.py`

### Tuần 2
1. `cd Tuan2`
2. `python -m venv T2_venv`
3. `source T2_venv/bin/activate`
4. `pip install -r requirements.txt`
5. `python src/run_training_pipeline.py`
6. `uvicorn src.app:app --reload --host 127.0.0.1 --port 8000`

### Tuần 3
1. `cd Tuan3`
2. `source T3_venv/bin/activate`
3. `pip install -r requirements.txt`
4. `python src/download_data.py`
5. `python src/train_anomaly.py`
6. `uvicorn src.app:app --reload`

### Tuần 4
1. `cd Tuan4/Lab_01`
2. `python -m venv .venv`
3. `source .venv/bin/activate`
4. `pip install -r requirements.txt`
5. `python src/train_forecast.py`
6. `python src/plot_results.py`

Hoặc với Lab 4 v4 upgrade:
1. `cd Tuan4/Lab_02`
2. `python -m venv .venv`
3. `source .venv/bin/activate`
4. `pip install -r requirements.txt`
5. `python src/download_data.py`
6. `python src/prepare_datasets.py`
7. `python src/train_classical_models.py`
8. `python src/plot_results.py`

### Tuần 5
1. `cd Tuan5/Lab_01`
2. `python -m venv .venv`
3. `source .venv/bin/activate`
4. `pip install -r requirements.txt`
5. `python scripts/download_vision_model.py`
6. `uvicorn app.main:app --reload`

Hoặc chạy bằng Docker:
1. `cd Tuan5/Lab_01`
2. `docker compose up --build`
