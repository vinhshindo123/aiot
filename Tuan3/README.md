# AIoT Event Intelligence

## Mục tiêu dự án
Dự án này chuyển bài Lab anomaly detection sang hệ thống AIoT tổng hợp dữ liệu node, thiết bị và measurement time-series. Dữ liệu mẫu được sinh tự động theo schema IoT và pipeline chuyển thẳng thành báo động, event, severity, decision cùng dashboard trực quan.

## Schema dữ liệu
Project hiện hỗ trợ dạng bảng sau:

- `devices` - node IoT và thông tin cơ bản.
- `node_status` - trạng thái hiện tại của node.
- `node_status_history` - lịch sử trạng thái node.
- `device_status` - trạng thái hiện tại của thiết bị thành phần.
- `device_status_history` - lịch sử bật/tắt thiết bị.
- `measurements` - time-series sensor data với `temp`, `humi`, `soil`, `light`.
- `command_history` - lịch sử lệnh điều khiển.

## File chính

- `src/download_data.py`: sinh dữ liệu mẫu IoT và tạo các CSV tương ứng.
- `src/train_anomaly.py`: train Isolation Forest và autoencoder demo, tạo event log.
- `src/app.py`: FastAPI phục vụ API anomaly và dashboard.
- `src/plot_results.py`: vẽ biểu đồ sensor và anomaly score.
- `src/test_api_local.py`: test API logic không cần chạy server.
- `src/test_api.py`: test API qua HTTP nếu server đang chạy.
- `src/static/dashboard.html`: giao diện front-end trực quan.
- `report.md`: báo cáo tổng kết.

## Cài đặt

```bash
cd /home/vinh_shindo/AIoT/Tuan3
source T3_venv/bin/activate
pip install -r requirements.txt
```

## Chạy theo pipeline

```bash
# Option A: use a Kaggle hydroponics CSV you downloaded
# 1) Download the dataset from Kaggle: https://www.kaggle.com/datasets/itsmonir31/hydroponics-datasets
#    - with Kaggle CLI (requires Kaggle credentials):
#      kaggle datasets download -d itsmonir31/hydroponics-datasets -p data --unzip
#    - or download manually from the website and place the CSV in `data/`

# 2) Convert the Kaggle CSV to the project's measurements.csv (example):
python src/download_data.py --source data/hydroponics.csv

# Option B: generate synthetic demo data (default)
python src/download_data.py
python src/train_anomaly.py
python src/plot_results.py
python src/test_api_local.py
```

## Mở dashboard

Sau khi chạy `python src/train_anomaly.py`, khởi động server:

```bash
uvicorn src.app:app --reload
```

Mở trình duyệt tại:

```text
http://127.0.0.1:8000/
```

## Kiểm tra nhanh

- `outputs/iforest_metrics.json`
- `outputs/anomaly_event_log.csv`
- `outputs/api_test_result.json`
- `figures/anomaly_detection_result.png`
- `figures/anomaly_score_over_time.png`

## Ghi chú

- Đây là một project demo AIoT event intelligence, không phải sản phẩm sản xuất.
- Anomaly score được tính từ mô hình Isolation Forest, event được sinh theo severity và rule decision.
- Dashboard hiện đại giúp quan sát dữ liệu cảm biến và sự kiện anomaly gần nhất.
