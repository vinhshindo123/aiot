# AIoT Deployment Pipeline

---

# 1. Luồng triển khai tổng quát

```text
┌─────────────────┐
│ Training Server │
│ PyTorch / TF    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Native Model    │
│ .pt / .keras    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Model Conversion│
│ Export / Convert│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Portable Format │
│ ONNX            │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Edge Gateway    │
│ OpenVINO / TRT  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Edge Node       │
│ TFLite / ET     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Device Action   │
│ Alert / Control │
└─────────────────┘
```

## Mô tả

| Thành phần       | Vai trò                                       |
| ---------------- | --------------------------------------------- |
| Training Server  | Huấn luyện model bằng PyTorch hoặc TensorFlow |
| Native Model     | Lưu model gốc phục vụ training và debug       |
| Model Conversion | Chuyển đổi model sang định dạng triển khai    |
| Portable Format  | ONNX đóng vai trò định dạng trung gian        |
| Edge Gateway     | Chạy inference tối ưu trên gateway            |
| Edge Node        | Chạy model nhẹ trên thiết bị biên             |
| Device Action    | Thực hiện cảnh báo hoặc điều khiển thiết bị   |

---

# 2. Ví dụ triển khai: Phát hiện lỗi máy công nghiệp bằng camera

## Bài toán

Camera quan sát dây chuyền sản xuất và tự động phát hiện sản phẩm lỗi.

---

## Pipeline triển khai

```text
┌──────────────┐
│ Camera Image │
└──────┬───────┘
       │
       ▼
┌─────────────────┐
│ Train ResNet18  │
│ PyTorch         │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ fault_model.pth │
│ Native Format   │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Export to ONNX  │
│ fault_model.onnx│
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ OpenVINO        │
│ Intel Gateway   │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ TFLite Runtime  │
│ Raspberry Pi    │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Send Alert      │
│ MQTT / REST API │
└─────────────────┘
```

---

## Các bước thực hiện

### Bước 1: Thu thập dữ liệu

* Camera chụp ảnh sản phẩm.
* Gắn nhãn Normal hoặc Defect.

### Bước 2: Huấn luyện model

* Sử dụng PyTorch.
* Huấn luyện ResNet18 để phân loại ảnh lỗi.

Output:

```text
fault_model.pth
```

---

### Bước 3: Chuyển đổi model

Export sang ONNX:

```text
fault_model.onnx
```

Mục đích:

* Giảm phụ thuộc PyTorch.
* Dễ triển khai trên nhiều runtime.

---

### Bước 4: Triển khai Gateway

Gateway sử dụng:

```text
Intel NUC
```

Runtime:

```text
OpenVINO Runtime
```

Chức năng:

* Nhận ảnh từ camera.
* Thực hiện inference.
* Trả kết quả lỗi hoặc bình thường.

---

### Bước 5: Triển khai Node

Thiết bị:

```text
Raspberry Pi
```

Runtime:

```text
TensorFlow Lite
```

Chức năng:

* Chạy model nhẹ tại thiết bị.
* Giảm phụ thuộc vào server trung tâm.

---

### Bước 6: Gửi cảnh báo

Nếu phát hiện lỗi:

```text
Defect Detected
```

Node sẽ:

* Gửi MQTT message.
* Gọi REST API.
* Kích hoạt còi hoặc đèn cảnh báo.

---

# 3. Kiến trúc triển khai cuối cùng

```text
Training Server
(PyTorch)

        │

        ▼

fault_model.pth

        │

        ▼

fault_model.onnx

        │

        ▼

Intel Gateway
(OpenVINO)

        │

        ▼

Raspberry Pi
(TFLite)

        │

        ▼

MQTT / REST API

        │

        ▼

Alarm / Dashboard
```

---

# 4. Kết luận

* Định dạng gốc (.pth) phù hợp cho huấn luyện và nghiên cứu.
* ONNX là định dạng trung gian giúp triển khai đa nền tảng.
* OpenVINO phù hợp với gateway Intel cần tối ưu hiệu năng.
* TFLite phù hợp với thiết bị biên có tài nguyên hạn chế.
* Pipeline Server → ONNX → Gateway → Edge Node là mô hình triển khai AIoT phổ biến trong thực tế.
