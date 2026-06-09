# scripts/predict_pytorch.py

import torch
from torchvision.models import resnet18
from torchvision import transforms
from PIL import Image
import os

# Load model from specific path
model_path = "/home/vinh_shindo/AIoT/Tuan5/Lab_Upgrade/models/exported_ca_nhan/resnet18.pth"

# Initialize model architecture
model = resnet18(weights=None)  # Don't load default weights
model.eval()

# Load your saved weights
if os.path.exists(model_path):
    model.load_state_dict(torch.load(model_path, map_location='cpu'))
    print(f"✓ Loaded PyTorch model from: {model_path}")
else:
    print(f"✗ Model not found at: {model_path}")
    exit(1)

transform = transforms.Compose([
    transforms.Resize((224,224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])  # Add normalization for better accuracy
])

# Load and preprocess image
img_path = "image_01.jpg"
if not os.path.exists(img_path):
    print(f"✗ Image not found: {img_path}")
    exit(1)

img = Image.open(img_path).convert("RGB")
x = transform(img).unsqueeze(0)

with torch.no_grad():
    output = model(x)
    # Get probabilities
    probabilities = torch.nn.functional.softmax(output[0], dim=0)
    pred_class = output.argmax(1).item()
    confidence = probabilities[pred_class].item()

print(f"Predicted class: {pred_class}")
print(f"Confidence: {confidence:.4f}")
print(pred_class)