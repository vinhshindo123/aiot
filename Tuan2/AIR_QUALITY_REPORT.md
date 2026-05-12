# Air Quality Project Report

## 1. Overview

Project này xử lý dữ liệu chất lượng không khí IoT, từ việc tải/nạp data, kiểm tra schema, làm sạch, tạo feature, train baseline model, đến deploy API inference.

- Dataset chính: UCI Air Quality Dataset
- Task: dự đoán nồng độ CO (`CO_GT`) bằng Linear Regression
- Output chính: model artifact, metrics, decision log, biểu đồ kiểm tra
- Môi trường Python: `T2_venv`

## 2. Dataset

Nguồn dữ liệu:

- `data/air_quality/AirQualityUCI.csv`
- Dữ liệu mô tả cảm biến chất lượng không khí: CO sensor, NMHC sensor, NOx, NO2, O3 và các biến nhiệt độ/độ ẩm
- Nếu không tải được dataset, project vẫn có fallback data sinh giả lập cùng cấu trúc.

Các cột quan trọng:

- `DateTime`
- `PT08.S1(CO)`, `PT08.S2(NMHC)`, `PT08.S3(NOx)`, `PT08.S4(NO2)`, `PT08.S5(O3)`
- `Temperature`, `Relative_Humidity`, `Absolute_Humidity`
- `CO_GT` (target)

## 3. Schema

Project kiểm tra schema dữ liệu đầu vào trước khi xử lý.

Yêu cầu schema:

- phải có `DateTime`
- phải có 5 sensor khí và 3 biến môi trường
- phải có target `CO_GT`

Kết quả schema:

- Dataset hiện tại đáp ứng schema UCI Air Quality sau khi mapping đúng cột.
- `check_schema()` kiểm tra thiếu cột, số columns, duplicate, và trả về báo cáo.

## 4. Data Cleaning

Các bước làm sạch chính:

- parse `DateTime` thành `timestamp`
- loại bỏ dòng duplicate
- xử lý outlier sensor bằng ngưỡng vật lý
- chuyển giá trị số về numeric và nội suy tuyến tính theo thời gian
- fill missing target bằng median

Sau làm sạch, dữ liệu vẫn giữ nguyên số dòng nhưng bổ sung `timestamp` và loại bỏ dữ liệu sai định dạng.

## 5. Feature Engineering

Các feature chính được tạo từ dữ liệu sạch:

- 5 sensor cảm biến: `PT08.S1(CO)`, `PT08.S2(NMHC)`, `PT08.S3(NOx)`, `PT08.S4(NO2)`, `PT08.S5(O3)`
- Thông số môi trường: `Temperature`, `Relative_Humidity`, `Absolute_Humidity`
- Feature thời gian: `hour`, `dayofweek`
- Rolling mean 6h cho các sensor chính

## 6. Model

Baseline model:

- `sklearn.pipeline.Pipeline`
- `StandardScaler` + `LinearRegression`

Model được lưu tại:

- `models/air_quality_model.joblib`

## 7. Metrics

Kết quả đánh giá regression trên tập test:

- MSE: `0.4988`
- RMSE: `0.7062`
- MAE: `0.5122`
- R²: `0.7089`

File metrics:

- `outputs/metrics.json`

## 8. Decision Rule

Decision logic dựa trên:

- `co_prediction`
- `anomaly_score` từ Z-score sensor
- Độ an toàn dựa trên ngưỡng CO theo WHO

Các nhãn decision:

- `CHECK_SENSOR_CALIBRATION`
- `AIR_QUALITY_HAZARDOUS`
- `AIR_QUALITY_POOR`
- `AIR_QUALITY_MODERATE`
- `AIR_QUALITY_GOOD`

Output decision log:

- `outputs/decision_log.csv`
- Bao gồm `co_prediction`, `actual_co`, `anomaly_score`, `is_anomaly`, `decision`, `command_hint`, `safety_note`, `air_quality_level`

## 9. Data Risks & Sai số dữ liệu

Các rủi ro dữ liệu thường gặp:

- Dữ liệu sensor bị missing hoặc giá trị `-200` trong UCI dataset
- Timestamp sai định dạng hoặc bị thiếu
- Dữ liệu duplicate gây nhiễu model
- Outlier cảm biến vượt giới hạn vật lý
- Thay đổi schema giữa dataset thật và fallback data

Để giảm rủi ro:

- kiểm tra schema đầu vào trước khi train
- chuẩn hoá và nội suy missing values
- áp dụng anomaly score để phát hiện sensor bất thường
- dùng `command_hint` cảnh báo khi dữ liệu không đáng tin cậy

## 10. Visualizations

### 10.1 CO predictions vs actual

![](outputs/figures/01_co_predictions.png)

### 10.2 Residual plot

![](outputs/figures/02_residual_plot.png)

### 10.3 Feature importance

![](outputs/figures/03_feature_importance.png)

---

File report này cung cấp tổng quan dataset, schema, làm sạch, mô hình, chỉ số, quyết định và rủi ro dữ liệu của project Air Quality.
