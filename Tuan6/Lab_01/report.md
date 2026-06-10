# BÁO CÁO LAB 6 – COMPUTER VISION AS IoT SENSOR

## 1. Thông tin sinh viên

* Họ và tên: Nguyễn Quang Vinh
* Môn học: Triển khai, phát triển ứng dụng AI và IoT
* Lab: Lab 6 – Computer Vision as IoT Sensor
* Ngày thực hiện: 10/06/2026

---

# 2. Mục tiêu bài lab

Trong bài lab này, em thực hiện xây dựng pipeline xử lý ảnh trong hệ thống AIoT bằng cách xem camera như một cảm biến IoT trực quan.

Các chức năng chính gồm:

* Camera stream từ webcam/IP camera hoặc stream mô phỏng
* Chụp snapshot
* Xử lý ảnh qua các bước:

  * Resize
  * Grayscale
  * Threshold
  * Edge Detection
* Ghi metadata ảnh
* Sinh visual event
* Motion capture
* Dashboard quan sát hệ thống

---

# 3. Môi trường thực hiện

## 3.1 Phần cứng

* Laptop có webcam
* Hoặc IP camera (nếu có)

## 3.2 Phần mềm

* Python 3.x
* FastAPI
* OpenCV (cv2)
* Pillow (PIL)
* Uvicorn

## 3.3 Cấu trúc project

lab6_cv_as_iot_sensor/

* app.py
* index.html
* run_lab6_demo.py
* data/

  * raw_images/
  * processed_images/
  * videos/
* outputs/

  * image_metadata.csv
  * image_event_log.csv

---

# 4. Các bước thực hiện

## 4.1 Tạo môi trường và cài thư viện

Lệnh thực hiện:

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
```

Kết quả:

* Không xuất hiện lỗi import
* Cài đặt thành công fastapi, cv2 và PIL

---

## 4.2 Chạy thử pipeline không cần camera

Lệnh thực hiện:

```bash
python run_lab6_demo.py
```

Kết quả quan sát:

* Sinh dữ liệu mẫu
* Có file trong:

  * data/raw_images/
  * data/processed_images/
  * data/videos/
  * outputs/

---

## 4.3 Chạy dashboard

Lệnh thực hiện:

```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Mở trình duyệt:

```text
http://127.0.0.1:8000/
```

Kết quả:

* Dashboard hiển thị thành công
* Có giao diện camera stream
* Có các nút snapshot, upload ảnh, motion capture và ghi video
![Dashboard Stream](outputs/images/dashboard.jpg)
---

# 5. Kết quả thực hiện

## 5.1 Camera Stream

Mô tả:

* Dashboard hiển thị live stream từ webcam hoặc stream mô phỏng.

Kết quả đạt được:

* Stream hoạt động ổn định
* Frame hiển thị liên tục
![Camera Stream](outputs/images/camera_stream.jpg)
---

## 5.2 Snapshot

Mô tả:

* Chụp ảnh từ camera.

Kết quả:

* Ảnh gốc được lưu trong:
  data/raw_images/
![Raw image snapshot](data/raw_images/img_9cf33c99e3.jpg)
* Ảnh xuất hiện trên dashboard
![Snapshot](outputs/images/snap_shot.jpg)
---

## 5.3 Xử lý ảnh

Pipeline xử lý gồm:

1. Resize
2. Grayscale
3. Threshold
4. Edge Detection

Kết quả:

* Ảnh xử lý được lưu trong:
  data/processed_images/
![Processed Image](data/processed_images/img_9cf33c99e3_processed_steps.jpg)
Ý nghĩa:

* Resize giảm kích thước ảnh
* Grayscale chuyển ảnh sang mức xám
* Threshold phân tách vùng sáng/tối
* Edge phát hiện biên vật thể

---

## 5.4 Metadata

File:

```text
outputs/image_metadata.csv
```
![alt text](outputs/images/ab.jpg)
Thông tin metadata gồm:

* Tên ảnh
* Timestamp
* Kích thước ảnh
* Đường dẫn file
* Thông tin xử lý

Vai trò:

Metadata giúp hệ thống quản lý và truy vết dữ liệu ảnh.

---

## 5.5 Event Log

File:

```text
outputs/image_event_log.csv
```
![alt text](outputs/images/ac.jpg)
Các event quan sát được:

* SNAPSHOT_CAPTURED
* IMAGE_UPLOADED
* VIDEO_RECORDED
* MOTION_DETECTED
* NO_SIGNIFICANT_MOTION

Vai trò:

Event dùng để mô tả các hành động hoặc sự kiện có ý nghĩa vận hành trong hệ thống AIoT.

---

## 5.6 Motion Capture

Mô tả:

* Hệ thống so sánh frame liên tiếp để phát hiện chuyển động.

Kết quả:

* Khi có thay đổi lớn giữa các frame:

  * Sinh event MOTION_DETECTED
  * Chụp ảnh lưu lại

Nhận xét:

Motion detection chỉ phát hiện sự thay đổi hình ảnh, chưa phải object detection.

---

# 6. Phân tích code

## 6.1 app.py

Vai trò:

* Backend FastAPI
* Xử lý stream camera
* Snapshot
* Video recording
* Motion capture
* Xử lý ảnh
* Ghi metadata và event

Các hàm quan trọng:

### log_image_pipeline()

* Lưu ảnh gốc
* Tạo ảnh xử lý
* Ghi metadata
* Sinh event

### create_processed_contact_sheet()

* Tạo ảnh gồm:

  * Resize
  * Grayscale
  * Threshold
  * Edge

### motion_capture()

* So sánh frame
* Phát hiện chuyển động

---

## 6.2 index.html

Vai trò:

* Dashboard giao diện người dùng
* Hiển thị stream
* Gọi API backend
* Quan sát pipeline ảnh

---

# 7. Trả lời câu hỏi phân tích

## Câu 1

Camera được xem là cảm biến thị giác (visual sensor) vì nó thực hiện nhiệm vụ thu nhận dữ liệu hình ảnh từ môi trường vật lý, tương tự như cách các cảm biến truyền thống thu thập dữ liệu telemetry (nhiệt độ, độ ẩm)
. Trong hệ thống AIoT, camera đóng vai trò là "mắt thần" giúp hệ thống trích xuất thông tin trực quan để đưa ra các quyết định vận hành

## Câu 2

Dữ liệu ảnh có dung lượng lớn, độ phức tạp cao và chứa nhiều ngữ cảnh hơn hẳn telemetry số
. Trong khi telemetry số thường là các giá trị đơn lẻ dễ lưu trữ và xử lý, thì dữ liệu ảnh đòi hỏi một pipeline xử lý phức tạp (tiền xử lý, trích xuất đặc trưng) để hiểu được nội dung bên trong

## Câu 3

Metadata đóng vai trò là "nhãn thông tin" mô tả các thuộc tính của ảnh như: thời gian chụp (timestamp), thiết bị nguồn (device_id), độ phân giải và độ sáng. Điều này giúp hệ thống quản lý, tra cứu và phân loại dữ liệu hiệu quả trong các kho lưu trữ lớn

## Câu 4

Việc chỉ lưu ảnh mà thiếu device_id và timestamp sẽ khiến dữ liệu trở nên vô chủ và mất tính thời điểm, gây khó khăn cho việc truy vết sự kiện khi có sự cố. Metadata đi kèm giúp định vị chính xác ảnh đó thuộc về cảm biến nào và xảy ra vào lúc nào trong dòng thời gian vận hành

## Câu 5

* Resize: giảm kích thước ảnh
* Grayscale: chuyển sang ảnh xám
* Threshold: tách vùng sáng tối
* Edge: phát hiện biên

## Câu 6

Không. Motion capture (phát hiện chuyển động) chỉ dựa trên sự thay đổi cường độ pixel giữa các khung hình (frame difference) để nhận biết có sự xê dịch. Nó chưa thể định danh hoặc phân loại đó là vật thể gì (người, xe, hay con vật) như các mô hình AI Object Detection

## Câu 7

Hệ thống nên sinh event như:

* LOW_LIGHT
* BLUR_IMAGE
* CAMERA_QUALITY_WARNING

## Câu 8

Hệ thống cần có cơ chế Stream mô phỏng (Simulated Stream). Cơ chế dự phòng này giúp pipeline xử lý của hệ thống AIoT không bị ngắt quãng, cho phép tiếp tục kiểm tra các chức năng khác ngay cả khi phần cứng camera gặp lỗi.

## Câu 9

Dashboard cho phép quan sát trực quan và tương tác thời gian thực. Thay vì đọc các dòng text khô khan trong CSV, dashboard hiển thị trực tiếp luồng stream, các bước biến đổi ảnh qua 4 giai đoạn và dòng thời gian (timeline) sự kiện, giúp người vận hành nhận diện lỗi nhanh chóng.

## Câu 10

Lab 6 đóng vai trò xây dựng hạ tầng dữ liệu sạch bao gồm: luồng ảnh đã tiền xử lý, danh sách metadata và nhật ký sự kiện. Đây là nền tảng để Lab 7 tích hợp các mô hình AI (như YOLO) nhằm thực hiện nhận diện vật thể và vẽ bounding box lên các ảnh đã được chuẩn bị này.
---

# 8. Kết luận

Qua bài lab này, em đã hiểu cách tích hợp camera như một cảm biến AIoT trong hệ thống xử lý ảnh. Em đã thực hiện được:

* Stream camera
* Snapshot
* Xử lý ảnh
* Ghi metadata
* Sinh event
* Motion detection
* Dashboard giám sát

Bài lab giúp làm nền tảng cho Object Detection ở Lab 7.
