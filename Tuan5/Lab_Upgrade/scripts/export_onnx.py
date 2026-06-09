import torch
from torchvision.models import resnet18, ResNet18_Weights
import time
import onnx
import os
from datetime import datetime

# Cấu hình
MODEL_PATH = "Lab_Upgrade/models/exported_ca_nhan/resnet18.onnx"
LOG_FILE = "export_log.txt"

def write_log(message, level="INFO"):
    """Ghi log ra file và console"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] [{level}] {message}"
    print(log_line)
    
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_line + "\n")

def main():
    # Bắt đầu log
    write_log("="*60)
    write_log("STARTING ONNX EXPORT")
    write_log("="*60)
    
    # Tạo thư mục
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    
    # Tải model
    write_log("Loading ResNet18 model...")
    model = resnet18(weights=ResNet18_Weights.DEFAULT)
    model.eval()
    write_log("Model loaded successfully")
    
    # Tạo input
    dummy_input = torch.randn(1, 3, 224, 224)
    write_log(f"Input shape: 1x3x224x224")
    
    # Export
    write_log("Starting ONNX export...")
    start_time = time.time()
    
    torch.onnx.export(
        model,
        dummy_input,
        MODEL_PATH,
        opset_version=17,
        input_names=["input"],
        output_names=["output"],
        dynamic_axes={
            'input': {0: 'batch_size'},
            'output': {0: 'batch_size'}
        }
    )
    
    export_time = time.time() - start_time
    write_log(f"Export completed in {export_time:.2f} seconds", "SUCCESS")
    
    # Verify
    write_log("Verifying ONNX model...")
    onnx_model = onnx.load(MODEL_PATH)
    onnx.checker.check_model(onnx_model)
    write_log("ONNX validation passed!", "SUCCESS")
    
    # File size
    file_size = os.path.getsize(MODEL_PATH) / (1024 * 1024)
    write_log(f"Model size: {file_size:.2f} MB")
    
    # Ghi summary
    summary = f"""
{'='*60}
EXPORT SUMMARY
{'='*60}
Export Date: {datetime.now().strftime("%Y-%m-%d")}
PyTorch: {torch.__version__}
ONNX: {onnx.__version__}
Input Shape: 1x3x224x224
Command: python export_onnx.py
Output: {os.path.basename(MODEL_PATH)}
Export Time: {export_time:.2f} sec
Status: SUCCESS
Warning: None
{'='*60}
"""
    print(summary)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(summary)
    
    print(f"\n✅ Export successful!")
    print(f"📄 Log saved to: {LOG_FILE}")
    print(f"📦 Model saved to: {MODEL_PATH}")

if __name__ == "__main__":
    main()