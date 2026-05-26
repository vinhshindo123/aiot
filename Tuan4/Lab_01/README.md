# LAB 4: Forecasting NODE_03 Temperature

## 1. Mục tiêu bài toán
Lab 4 hiện tại sử dụng dữ liệu `lab4_forecast_NODE03_augmented.csv` để xây dựng pipeline dự báo nhiệt độ của `NODE_03`.
Mục tiêu chính là dự báo nhiệt độ sau 5 phút và chuyển giá trị đó thành độ rủi ro vận hành.

## 2. Dataset chính
| Thông tin | Giá trị |
|-----------|---------|
| **Tên file** | `data/lab4_forecast_NODE03_augmented.csv` |
| **Số lượng mẫu** | 4,478 rows |
| **Số features** | 41 |
| **Số targets** | 4 (dự báo 5, 10, 15, 25 phút) |
| **Thời gian** | 16 ngày (16/03 → 02/04/2026) |
| **Node ID** | NODE_03 |

## 3. Các nhóm feature
| Nhóm feature | Các cột | Mô tả |
|--------------|---------|-------|
| **Sensor hiện tại** | `temp`, `humi`, `soil`, `light` | Nhiệt độ, độ ẩm, độ ẩm đất, ánh sáng |
| **Lag features** | `temp_lag_1/2/3`, `humi_lag_1/2`, `soil_lag_1/2`, `light_lag_1` | Giá trị quá khứ từ 5-15 phút trước |
| **Rolling stats** | `temp_rolling_mean_3/5`, `temp_rolling_std_3/5`, `soil_rolling_mean_3/5`, `soil_rolling_min_3`, `soil_rolling_max_3`, `humi_rolling_mean_3` | Trung bình và độ lệch chuẩn cửa sổ |
| **Time features** | `hour`, `minute`, `day_of_week`, `is_weekend`, `hour_sin`, `hour_cos` | Thông tin thời gian dạng chu kỳ |
| **Delta features** | `temp_delta_1/3`, `humi_delta_1`, `soil_delta_1` | Tốc độ thay đổi |
| **Interaction** | `temp_humi_product`, `temp_soil_ratio`, `humi_soil_product`, `temp_light_ratio` | Kết hợp đa cảm biến |
| **Operational** | `cmd_count`, `cmd_failure_rate`, `cmd_timeout_count`, `rssi_mean`, `rssi_min`, `rssi_std` | Lệnh điều khiển và chất lượng mạng |

## 4. Targets dự báo
| Target | Ý nghĩa |
|--------|---------|
| `target_temp_next_1` | Nhiệt độ sau **5 phút** |
| `target_temp_next_2` | Nhiệt độ sau **10 phút** |
| `target_temp_next_3` | Nhiệt độ sau **15 phút** |
| `target_temp_next_5` | Nhiệt độ sau **25 phút** |

## 5. Thống kê nhanh
| Feature | Min | Max | Mean |
|---------|-----|-----|------|
| Temp (°C) | 26.8 | 30.8 | 28.6 |
| Humidity (%) | 63.0 | 70.3 | 67.0 |
| Soil (%) | 3.0 | 4.0 | 3.0 |
| Light (%) | 0 | 100 | ~15 |
| RSSI (dBm) | -85 | -40 | -68 |

## 6. Kết quả kỹ thuật
Pipeline `src/train_forecast.py` đã được điều chỉnh để:
- dùng dataset `data/lab4_forecast_NODE03_augmented.csv`
- dự báo giá trị `target_temp_next_1` = 5 phút
- so sánh với baseline persistence và moving average
- train các mô hình Linear Regression, Random Forest, Gradient Boosting
- lưu `outputs/forecast_metrics.json`, `outputs/forecast_test_predictions.csv`, `outputs/forecast_log.csv`

## 7. Visualizations
Những biểu đồ đã tạo:
- `figures/forecast_vs_actual.png`
- `figures/forecast_error_over_time.png`
- `figures/model_comparison_mae.png`
- `figures/model_comparison_all_metrics.png`
- `figures/target_distribution.png`
- `figures/eda_sensor_trends.png`
- `figures/eda_distribution.png`
- `figures/eda_correlation_matrix.png`

## 8. Output files
- `models/forecast_model_bundle_v1.joblib`
- `outputs/forecast_metrics.json`
- `outputs/forecast_test_predictions.csv`
- `outputs/forecast_log.csv`
- `outputs/api_test_result.json`
- `figures/forecast_vs_actual.png`
- `figures/forecast_error_over_time.png`
- `figures/model_comparison_mae.png`
- `figures/model_comparison_all_metrics.png`
- `figures/target_distribution.png`
- `figures/eda_sensor_trends.png`
- `figures/eda_distribution.png`
- `figures/eda_correlation_matrix.png`

## 9. Cách chạy
1. Chạy training và ghi kết quả:
```bash
python src/train_forecast.py
```
2. Vẽ biểu đồ kết quả:
```bash
python src/plot_results.py
```
3. Kiểm tra API logic local:
```bash
python src/test_api_local.py
```

## 9. API deploy
Sau khi train xong, chạy:
```bash
uvicorn src.app:app --reload
```
Mở:
```text
http://127.0.0.1:8000/docs
```

## 10. Lưu ý
- Forecast ở đây là dự báo nhiệt độ, không phải lệnh tác động trực tiếp.
- MAE/RMSE/MAPE dùng để đánh giá chất lượng dự báo, không dùng Precision/Recall/F1.
- Quy trình đúng là: forecast → risk level → recommendation → kiểm duyệt/safety.
