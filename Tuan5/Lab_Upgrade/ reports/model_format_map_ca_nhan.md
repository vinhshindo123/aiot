# MODEL FORMAT MAP CÁ NHÂN

## Lab 5 Nâng cao - Model Format, Runtime và Deployment Trade-off trong AIoT

### Thông tin sinh viên

* Họ tên: Nguyễn Quang Vinh
* MSSV: 1771020760
* Môn học: Triển khai, phát triển ứng dụng AI và IoT
* Bài tập: Nhiệm vụ A – Lập bản đồ định dạng model cá nhân

---

# 1. Mục tiêu

Trong quá trình triển khai hệ thống AIoT, model sau khi huấn luyện không phải lúc nào cũng được sử dụng trực tiếp. Tùy theo nền tảng triển khai, phần cứng đích và yêu cầu về hiệu năng, model có thể được chuyển đổi sang các định dạng khác nhau nhằm tối ưu kích thước, tốc độ suy luận (inference) hoặc khả năng tương thích.

Mục tiêu của tài liệu này là khảo sát các định dạng model phổ biến hiện nay, phân tích runtime tương ứng, ưu điểm, hạn chế và khả năng ứng dụng trong các hệ thống AIoT thực tế.

---

# 2. Bản đồ định dạng model

| Format                    | Framework nguồn           | Runtime            | Thiết bị phù hợp    | Lợi ích chính                               | Đánh đổi chính                           |
| ------------------------- | ------------------------- | ------------------ | ------------------- | ------------------------------------------- | ---------------------------------------- |
| .pkl / .joblib            | Scikit-learn              | Python Runtime     | Server CPU          | Dễ sử dụng, lưu trực tiếp model             | Phụ thuộc Python và phiên bản thư viện   |
| .pt / .pth                | PyTorch                   | PyTorch Runtime    | CPU, GPU, Server    | Giữ nguyên model gốc, thuận tiện huấn luyện | Khó triển khai trên mobile/edge          |
| .keras / SavedModel       | TensorFlow/Keras          | TensorFlow Runtime | CPU, GPU, Cloud     | Chuẩn TensorFlow, dễ chuyển đổi             | Kích thước thường lớn                    |
| .onnx                     | Nhiều framework           | ONNX Runtime       | Server, Edge, Cloud | Portable, đa nền tảng                       | Một số operator có thể không tương thích |
| .tflite                   | TensorFlow Lite           | TFLite Runtime     | Mobile, IoT Gateway | Nhẹ, tối ưu thiết bị biên                   | Có thể giảm độ chính xác                 |
| OpenVINO IR (.xml/.bin)   | ONNX, TensorFlow, PyTorch | OpenVINO Runtime   | Intel CPU/GPU/NPU   | Tăng tốc phần cứng Intel                    | Ít phù hợp với phần cứng khác            |
| TensorRT Engine (.engine) | ONNX, PyTorch             | TensorRT Runtime   | NVIDIA GPU, Jetson  | Hiệu năng inference rất cao                 | Không portable giữa các GPU              |
| .pte (ExecuTorch)         | PyTorch                   | ExecuTorch Runtime | Mobile, Embedded    | Tối ưu on-device inference                  | Hệ sinh thái còn mới                     |

---

# 3. Phân tích chi tiết từng định dạng

## 3.1 Scikit-learn (.pkl, .joblib)

### Nguồn gốc

Được sử dụng trong hệ sinh thái Scikit-learn để lưu các model Machine Learning truyền thống như:

* Linear Regression
* Random Forest
* Isolation Forest
* XGBoost Wrapper
* Forecasting Models

### Runtime

* Python Runtime
* Scikit-learn Runtime

### Thiết bị phù hợp

* Server CPU
* Cloud Service
* API Backend

### Ưu điểm

* Dễ lưu và tải model.
* Triển khai nhanh trong môi trường Python.
* Phù hợp với dữ liệu bảng (tabular data).

### Nhược điểm

* Không portable.
* Phụ thuộc phiên bản Python.
* Khó triển khai trực tiếp trên mobile hoặc edge device.

### Đánh giá AIoT

Phù hợp với các AI Service xử lý dữ liệu cảm biến hoặc dự báo trên server.

---

## 3.2 PyTorch (.pt, .pth)

### Nguồn gốc

Định dạng mặc định của PyTorch.

### Runtime

* PyTorch Runtime
* TorchServe

### Thiết bị phù hợp

* CPU
* GPU
* Cloud
* Research Server

### Ưu điểm

* Lưu đầy đủ trọng số model.
* Dễ huấn luyện và debug.
* Hệ sinh thái mạnh.

### Nhược điểm

* Kích thước thường lớn.
* Cần cài PyTorch Runtime.
* Không tối ưu cho thiết bị biên.

### Đánh giá AIoT

Rất tốt cho giai đoạn nghiên cứu và huấn luyện nhưng thường cần chuyển đổi trước khi triển khai thực tế.

---

## 3.3 TensorFlow SavedModel / .keras

### Nguồn gốc

Định dạng chính thức của TensorFlow và Keras.

### Runtime

* TensorFlow Runtime
* TensorFlow Serving

### Thiết bị phù hợp

* Server
* Cloud
* GPU

### Ưu điểm

* Chuẩn chính thức TensorFlow.
* Hỗ trợ deployment tốt.
* Dễ chuyển sang TFLite.

### Nhược điểm

* Runtime khá nặng.
* Kích thước model lớn.

### Đánh giá AIoT

Phù hợp với các hệ thống AI quy mô lớn trên cloud hoặc server.

---

## 3.4 ONNX (.onnx)

### Nguồn gốc

Open Neural Network Exchange.

Là định dạng trung gian cho phép chuyển model giữa nhiều framework.

### Runtime

* ONNX Runtime
* OpenVINO
* TensorRT
* DirectML

### Thiết bị phù hợp

* Server
* Edge Gateway
* Cloud

### Ưu điểm

* Độc lập framework.
* Hỗ trợ nhiều runtime.
* Dễ triển khai đa nền tảng.

### Nhược điểm

* Không phải operator nào cũng convert hoàn hảo.
* Có thể xuất hiện sai khác nhỏ sau chuyển đổi.

### Đánh giá AIoT

Đây là định dạng phù hợp nhất cho deployment đa nền tảng trong AIoT.

---

## 3.5 TensorFlow Lite (.tflite)

### Nguồn gốc

Được phát triển từ TensorFlow để tối ưu thiết bị biên.

### Runtime

* TensorFlow Lite Runtime

### Thiết bị phù hợp

* Android
* Raspberry Pi
* IoT Gateway
* Embedded Device

### Ưu điểm

* Kích thước nhỏ.
* Tiêu thụ bộ nhớ thấp.
* Inference nhanh.

### Nhược điểm

* Một số layer không hỗ trợ.
* Có thể giảm accuracy khi quantization.

### Đánh giá AIoT

Là một trong những lựa chọn tốt nhất cho mobile và edge device.

---

## 3.6 OpenVINO IR (.xml/.bin)

### Nguồn gốc

Bộ công cụ triển khai AI của Intel.

### Runtime

* OpenVINO Runtime

### Thiết bị phù hợp

* Intel CPU
* Intel GPU
* Intel NPU
* Industrial Gateway

### Ưu điểm

* Tăng tốc mạnh trên phần cứng Intel.
* Giảm latency.
* Tối ưu edge computing.

### Nhược điểm

* Lợi ích giảm khi không dùng phần cứng Intel.
* Hệ sinh thái hẹp hơn ONNX.

### Đánh giá AIoT

Rất phù hợp cho gateway công nghiệp sử dụng Intel CPU.

---

## 3.7 TensorRT Engine (.engine)

### Nguồn gốc

NVIDIA TensorRT.

### Runtime

* TensorRT Runtime

### Thiết bị phù hợp

* NVIDIA GPU
* NVIDIA Jetson

### Ưu điểm

* Tốc độ inference rất cao.
* Tận dụng tối đa GPU NVIDIA.
* Tối ưu latency.

### Nhược điểm

* Không portable.
* Engine phụ thuộc GPU và phiên bản CUDA.

### Đánh giá AIoT

Phù hợp với hệ thống AI thời gian thực sử dụng NVIDIA Jetson hoặc server GPU.

---

## 3.8 ExecuTorch (.pte)

### Nguồn gốc

Nền tảng PyTorch Edge mới.

### Runtime

* ExecuTorch Runtime

### Thiết bị phù hợp

* Smartphone
* Edge Device
* Embedded AI

### Ưu điểm

* Tối ưu suy luận on-device.
* Giảm tiêu thụ tài nguyên.
* Hỗ trợ triển khai PyTorch trên mobile.

### Nhược điểm

* Hệ sinh thái đang phát triển.
* Tài liệu và cộng đồng còn hạn chế.

### Đánh giá AIoT

Là hướng triển khai tiềm năng cho các ứng dụng AI trên thiết bị biên trong tương lai.

---

# 4. So sánh theo nhóm triển khai

## Nhóm Server Python

| Format       | Mức độ phù hợp |
| ------------ | -------------- |
| .pkl/.joblib | Cao            |
| .pt/.pth     | Cao            |
| SavedModel   | Cao            |

---

## Nhóm Portable

| Format | Mức độ phù hợp |
| ------ | -------------- |
| ONNX   | Rất cao        |

ONNX là định dạng trung gian có khả năng chuyển đổi và triển khai trên nhiều runtime khác nhau.

---

## Nhóm Mobile / Edge

| Format              | Mức độ phù hợp |
| ------------------- | -------------- |
| TFLite              | Rất cao        |
| ExecuTorch          | Cao            |
| ONNX Runtime Mobile | Trung bình     |
| NCNN                | Cao            |

---

## Nhóm phụ thuộc phần cứng

| Format   | Phần cứng         |
| -------- | ----------------- |
| TensorRT | NVIDIA GPU        |
| OpenVINO | Intel CPU/GPU/NPU |
| CoreML   | Apple Silicon     |

---

# 5. Kết luận

Qua khảo sát các định dạng model và runtime phổ biến hiện nay có thể rút ra một số kết luận:

1. PyTorch và TensorFlow SavedModel phù hợp cho quá trình nghiên cứu và huấn luyện nhưng chưa phải lựa chọn tối ưu khi triển khai trực tiếp.

2. ONNX là định dạng trung gian có tính portable cao nhất, giúp giảm sự phụ thuộc vào framework ban đầu và hỗ trợ nhiều runtime khác nhau.

3. TensorFlow Lite và ExecuTorch phù hợp với các thiết bị mobile và edge nhờ kích thước nhỏ, tiêu thụ tài nguyên thấp và khả năng suy luận tại thiết bị.

4. OpenVINO là lựa chọn hiệu quả cho các hệ thống AIoT sử dụng phần cứng Intel.

5. TensorRT mang lại hiệu năng cao nhất trên GPU NVIDIA nhưng đánh đổi bằng tính portable thấp.

6. Đối với hệ thống AIoT trong Lab 5, ONNX được đánh giá là định dạng cân bằng nhất giữa khả năng triển khai, hiệu năng và tính tương thích đa nền tảng.

7. Trong các nhiệm vụ tiếp theo của Lab 5, tuyến chuyển đổi PyTorch → ONNX là lựa chọn phù hợp nhất để thực hiện benchmark và tích hợp vào AI Inference Service.
