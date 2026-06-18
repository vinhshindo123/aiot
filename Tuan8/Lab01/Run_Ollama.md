# OLLAMA + QWEN3 TRÊN DELL INSPIRON 7490 (i7-10510U, RAM 16GB)

## 1. Cấu hình máy hiện tại

### Kiểm tra CPU

```powershell
Get-CimInstance Win32_Processor | Select Name,NumberOfCores,NumberOfLogicalProcessors
```

Kết quả cần đạt:

```text
Intel(R) Core(TM) i7-10510U
4 Cores
8 Logical Processors
```

---

### Kiểm tra RAM

```powershell
Get-CimInstance Win32_ComputerSystem | Select TotalPhysicalMemory
```

Kết quả cần đạt:

```text
16951169024
```

≈ 16GB RAM

---

### Kiểm tra GPU

```powershell
wmic path win32_VideoController get name
```

Kết quả cần đạt:

```text
Intel UHD Graphics
NVIDIA GeForce MX250
```

---

### Kiểm tra dung lượng ổ đĩa

```powershell
wmic logicaldisk get size,freespace,caption
```

Kết quả nên có:

```text
FreeSpace > 20GB
```

Máy hiện tại:

```text
~54GB trống
```

Đạt yêu cầu.

---

# 2. Bảng chọn model phù hợp

| Model       | RAM khuyến nghị | Đánh giá trên máy này |
| ----------- | --------------- | --------------------- |
| qwen3:0.6b  | 4GB+            | Rất mượt              |
| qwen3:1.7b  | 8GB+            | Tối ưu nhất           |
| qwen3:4b    | 16GB+           | Chạy được             |
| gemma3:1b   | 8GB+            | Chạy tốt              |
| gemma3:4b   | 16GB+           | Khá chậm              |
| llama3.2:3b | 12GB+           | Chạy tốt              |

Khuyến nghị:

```text
qwen3:1.7b
```

---

# 3. Cài Ollama

Tải:

https://ollama.com/download

Kiểm tra:

```powershell
ollama --version
```

Kết quả cần đạt:

```text
ollama version x.x.x
```

---

# 4. Tải model Qwen3

```powershell
ollama pull qwen3:1.7b
```

Kết quả cần đạt:

```text
success
```

Kiểm tra:

```powershell
ollama list
```

Ví dụ:

```text
NAME
qwen3:1.7b
```

---

# 5. Chạy model

```powershell
ollama run qwen3:1.7b
```

Ví dụ:

```text
>>> Xin chào
```

Kết quả cần đạt:

```text
Xin chào! Tôi có thể giúp gì?
```

---

# 6. Kiểm tra Ollama Server

```powershell
curl http://localhost:11434/api/tags
```

Kết quả cần đạt:

```json
{
  "models":[...]
}
```

---

# 7. Bật / Tắt Thinking

## Trong Terminal

### Tắt

```text
/set nothink
```

Kết quả:

```text
Set 'nothink' mode.
```

---

### Bật lại

```text
/set think
```

---

## Chạy trực tiếp không thinking

```powershell
ollama run qwen3:1.7b --think=false
```

---

# 8. Gọi API không Thinking

```python
import requests

r = requests.post(
    "http://localhost:11434/api/chat",
    json={
        "model":"qwen3:1.7b",
        "think":False,
        "messages":[
            {
                "role":"user",
                "content":"Giải thích anomaly detection"
            }
        ]
    }
)

print(r.json())
```

Kết quả:

```json
{
  "message": {...}
}
```

Không xuất hiện Thinking.

---

# 9. Tạo model riêng

Tạo file:

```text
Modelfile
```

Nội dung:

```text
FROM qwen3:1.7b

SYSTEM """
You are an AIoT assistant.

Return concise answers.

Never output chain of thought.

Never output reasoning.
"""
```

Tạo model:

```powershell
ollama create qwen3-fast -f Modelfile
```

Kết quả cần đạt:

```text
success
```

---

# 10. Gọi model riêng

```powershell
ollama run qwen3-fast
```

Hoặc API:

```json
{
  "model":"qwen3-fast"
}
```

---

# 11. Theo dõi CPU realtime

### CMD

```powershell
typeperf "\Processor(_Total)\% Processor Time"
```

---

### Realtime

```powershell
Get-Counter '\Processor(_Total)\% Processor Time' -Continuous
```

Kết quả:

```text
CPU %
```

cập nhật liên tục.

---

# 12. Theo dõi RAM realtime

```powershell
Get-Counter '\Memory\Available MBytes' -Continuous
```

---

# 13. Theo dõi tiến trình Ollama realtime

### Xem Ollama đang chạy

```powershell
Get-Process ollama
```

---

### CPU + RAM của Ollama

```powershell
Get-Process ollama | Select ProcessName,CPU,WS
```

---

### Realtime

```powershell
while ($true)
{
    Get-Process ollama |
    Select ProcessName,CPU,WS

    Start-Sleep 2
}
```

---

# 14. Xem model đang chiếm RAM bao nhiêu

```powershell
Get-Process ollama |
Format-Table Name,CPU,PM,WS
```

WS = Working Set (RAM thực dùng)

---

# 15. Xóa model

Xem model:

```powershell
ollama list
```

Xóa:

```powershell
ollama rm qwen3:1.7b
```

Kết quả:

```text
deleted
```

---

# 16. Xóa nhiều model

```powershell
ollama rm qwen3:1.7b
ollama rm qwen3-fast
ollama rm gemma3:1b
```

---

# 17. Dọn sạch cache model

Thư mục:

```text
C:\Users\<user>\.ollama\models
```

Xóa toàn bộ:

```powershell
Remove-Item "$env:USERPROFILE\.ollama\models" -Recurse -Force
```

---

# 18. Gỡ Ollama sạch

## Dừng service

```powershell
taskkill /F /IM ollama.exe
```

---

## Gỡ ứng dụng

```powershell
winget uninstall Ollama.Ollama
```

Hoặc:

```text
Settings
→ Apps
→ Ollama
→ Uninstall
```

---

## Xóa dữ liệu còn sót

```powershell
Remove-Item "$env:USERPROFILE\.ollama" -Recurse -Force
```

---

# 19. Kiểm tra đã gỡ sạch

```powershell
ollama --version
```

Kết quả:

```text
'ollama' is not recognized
```

và:

```powershell
Test-Path "$env:USERPROFILE\.ollama"
```

Kết quả:

```text
False
```

Hoàn tất gỡ sạch.
