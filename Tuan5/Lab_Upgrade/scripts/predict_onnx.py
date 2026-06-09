# scripts/predict_onnx.py

import onnxruntime as ort
from PIL import Image
from torchvision import transforms
import numpy as np
import os

# Load ONNX model from specific path
onnx_path = "/home/vinh_shindo/AIoT/Tuan5/Lab_Upgrade/models/exported_ca_nhan/resnet18.onnx"

if not os.path.exists(onnx_path):
    print(f"✗ ONNX model not found at: {onnx_path}")
    exit(1)

# Create ONNX session
session = ort.InferenceSession(onnx_path)
print(f"✓ Loaded ONNX model from: {onnx_path}")

# Get input name (usually 'input')
input_name = session.get_inputs()[0].name
print(f"Input name: {input_name}")

transform = transforms.Compose([
    transforms.Resize((224,224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])  # Same normalization as PyTorch
])

# Load and preprocess image
img_path = "image_01.jpg"
if not os.path.exists(img_path):
    print(f"✗ Image not found: {img_path}")
    exit(1)

img = Image.open(img_path).convert("RGB")
x = transform(img).unsqueeze(0)

# Run inference
outputs = session.run(None, {input_name: x.numpy()})

# Get prediction (outputs[0] is the logits)
logits = outputs[0]
probabilities = np.exp(logits) / np.sum(np.exp(logits))  # Softmax
pred_class = np.argmax(logits)
confidence = probabilities[0][pred_class]

print(f"Predicted class: {pred_class}")
print(f"Confidence: {confidence:.4f}")
print(pred_class)