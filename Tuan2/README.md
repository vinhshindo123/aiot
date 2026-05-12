# LAB 2 - AIoT Air Quality Data Preparation, Baseline Model và Deploy Demo

## 1. Mục tiêu của project

Project này là một phiên bản LAB 2 cho AIoT, tập trung vào dữ liệu chất lượng không khí.
Luồng chính:

```text
Public Air Quality dataset / fallback generated data
→ kiểm tra schema
→ làm sạch dữ liệu IoT
→ tạo feature dataset
→ chia train/test theo thời gian
→ train Linear Regression baseline
→ tính anomaly_score bằng Z-score trên các sensor
→ sinh decision_log.csv
→ lưu model .joblib
→ deploy model bằng FastAPI
→ test API /predict
```

Dataset chính: **UCI Air Quality Dataset**.
Khi máy có Internet, script sẽ tải dữ liệu từ UCI repository. Nếu không có Internet, project vẫn tự sinh dữ liệu fallback cùng schema để chạy end-to-end.

## 2. Cấu trúc thư mục

```text
Tuan2/
├── data/
│   ├── air_quality/                  # dataset UCI Air Quality hoặc file đã tải sẵn
│   ├── DATA_SOURCES.md
│   ├── feature_dataset.csv
│   ├── telemetry_clean.csv
│   └── occupancy_fallback_same_schema.csv
├── docs/
│   └── sample_payload_predict.json
├── models/
│   └── air_quality_model.joblib
├── notebooks/
│   └── 01_data_prep_baseline_deploy_ready.ipynb
├── outputs/
│   ├── dataset_status.json
│   ├── decision_log.csv
│   ├── metrics.json
│   └── figures/
├── src/
│   ├── app.py
│   ├── check_outputs.py
│   ├── data_utils.py
│   ├── download_data.py
│   ├── run_training_pipeline.py
│   └── test_api.py
└── requirements.txt
```

## 3. Tạo môi trường `T2_venv`

```bash
cd /home/vinh_shindo/AIoT/Tuan2
python3 -m venv T2_venv
source T2_venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

## 4. Chạy notebook

```bash
source T2_venv/bin/activate
jupyter lab
```

Mở file:

```text
notebooks/01_data_prep_baseline_deploy_ready.ipynb
```

Chọn **Run → Run All Cells**.

Sau khi chạy xong, phải có các file:

```text
data/telemetry_clean.csv
data/feature_dataset.csv
models/air_quality_model.joblib
outputs/metrics.json
outputs/decision_log.csv
outputs/figures/01_co_predictions.png
outputs/figures/02_residual_plot.png
outputs/figures/03_feature_importance.png
```

## 5. Chạy nhanh không cần notebook

```bash
source T2_venv/bin/activate
python src/run_training_pipeline.py
python src/check_outputs.py
```

## 6. Deploy model bằng FastAPI với Interactive Dashboard

```bash
source T2_venv/bin/activate
uvicorn src.app:app --reload --host 127.0.0.1 --port 8000
```

Truy cập ứng dụng:

- **Dashboard chính**: http://127.0.0.1:8000/dashboard
- **Dữ liệu trực quan**: http://127.0.0.1:8000/data-viz
- **Đánh giá mô hình**: http://127.0.0.1:8000/metrics-viz
- **Công cụ dự đoán** (interactive): http://127.0.0.1:8000/predict-viz
- **API Documentation**: http://127.0.0.1:8000/docs

### Dashboard Features:

✨ **Giao diện trực quan**:
- 🎨 Thiết kế gradient đẹp mắt
- 📊 Biểu đồ Plotly interactive (zoom, pan, hover)
- ⚡ Animation khi hiển thị kết quả

📊 **Dashboard chính**:
- Metrics chính (R², RMSE, MAE, Test samples)
- Navigation đến các phần khác

📈 **Data Analysis**:
- Phân bố CO concentration
- Phân bố nhiệt độ
- Phân bố quyết định air quality

📋 **Model Evaluation**:
- Hiển thị 4 metrics chính (MSE, RMSE, MAE, R²)
- Biểu đồ cột metrics
- So sánh predictions vs actual (100 mẫu gần nhất)

🔮 **Prediction Tool** (Interactive):
- Slider để điều chỉnh tất cả cảm biến real-time
- Hiển thị giá trị khi kéo slider
- Button "Predict"
- Kết quả dự đoán với:
  - Giá trị CO predict (mg/m³)
  - Gauge chart với zones (Good/Moderate/Poor/Hazardous)
  - Quyết định air quality với animation
  - Safety recommendation

Test qua API:

```bash
python src/test_api.py
```

## 7. Tiêu chí hoàn thành

Sinh viên hoàn thành khi:

1. Notebook chạy trọn vẹn không lỗi.
2. Có file model `models/air_quality_model.joblib`.
3. Có `outputs/metrics.json` với các chỉ số regression.
4. Có `outputs/decision_log.csv` với các trường: `timestamp`, `co_prediction`, `actual_co`, `anomaly_score`, `decision`, `command_hint`, `safety_note`, `air_quality_level`.
5. Chạy được FastAPI và truy cập `/docs`.
6. Chạy `python src/test_api.py` thành công.
7. Giải thích được luồng: telemetry → feature → model → decision.

## 8. Lưu ý

- Dự án hiện tại xử lý dữ liệu chất lượng không khí (Air Quality) với mục tiêu dự đoán CO và sinh cảnh báo.
- `src/data_utils.py` chứa logic dataset, clean, feature engineering, training, anomaly score và decision rule.
- `src/app.py` deploy API inference cho CO prediction.
- Không cần sử dụng Occupancy Detection trong phiên bản hiện tại này.
