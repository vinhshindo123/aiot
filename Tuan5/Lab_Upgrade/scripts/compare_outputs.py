# scripts/compare_outputs.py

import torch
from torchvision.models import resnet18
from torchvision import transforms
from PIL import Image
import onnxruntime as ort
import numpy as np
import pandas as pd
import os
from pathlib import Path

# Model paths
PYTORCH_MODEL_PATH = "/home/vinh_shindo/AIoT/Tuan5/Lab_Upgrade/models/exported_ca_nhan/resnet18.pth"
ONNX_MODEL_PATH = "/home/vinh_shindo/AIoT/Tuan5/Lab_Upgrade/models/exported_ca_nhan/resnet18.onnx"

# Load ImageNet class labels
def load_imagenet_labels():
    """Load ImageNet class labels (1000 classes)"""
    labels_path = Path("data/imagenet_classes.txt")
    
    if not labels_path.exists():
        import urllib.request
        labels_path.parent.mkdir(exist_ok=True)
        labels_url = "https://raw.githubusercontent.com/pytorch/hub/master/imagenet_classes.txt"
        urllib.request.urlretrieve(labels_url, labels_path)
        print(f"✓ Downloaded ImageNet labels to {labels_path}")
    
    with open(labels_path, "r") as f:
        return [line.strip() for line in f.readlines()]

# Load models
def load_models():
    """Load PyTorch and ONNX models from specified paths"""
    
    # Load PyTorch model
    print(f"Loading PyTorch model from: {PYTORCH_MODEL_PATH}")
    if not os.path.exists(PYTORCH_MODEL_PATH):
        raise FileNotFoundError(f"PyTorch model not found at {PYTORCH_MODEL_PATH}")
    
    pytorch_model = resnet18(weights=None)
    pytorch_model.load_state_dict(torch.load(PYTORCH_MODEL_PATH, map_location='cpu'))
    pytorch_model.eval()
    print("✓ PyTorch model loaded")
    
    # Load ONNX model
    print(f"Loading ONNX model from: {ONNX_MODEL_PATH}")
    if not os.path.exists(ONNX_MODEL_PATH):
        raise FileNotFoundError(f"ONNX model not found at {ONNX_MODEL_PATH}")
    
    onnx_session = ort.InferenceSession(ONNX_MODEL_PATH)
    print("✓ ONNX model loaded")
    
    return pytorch_model, onnx_session

# Image preprocessing (with normalization for pretrained models)
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

def predict_pytorch(model, image_tensor):
    """Run PyTorch inference"""
    with torch.no_grad():
        output = model(image_tensor)
        probabilities = torch.nn.functional.softmax(output[0], dim=0)
        top_prob, top_class = torch.max(probabilities, 0)
        return top_class.item(), top_prob.item()

def predict_onnx(session, image_tensor):
    """Run ONNX inference"""
    input_name = session.get_inputs()[0].name
    outputs = session.run(None, {input_name: image_tensor.numpy()})
    logits = outputs[0]
    probabilities = np.exp(logits) / np.sum(np.exp(logits))
    top_class = np.argmax(probabilities[0])
    top_prob = probabilities[0][top_class]
    return int(top_class), float(top_prob)

def get_class_name(class_id, labels):
    """Get class name from ID"""
    return labels[class_id] if 0 <= class_id < len(labels) else f"class_{class_id}"

def compare_predictions(image_paths, pytorch_model, onnx_session, labels):
    """Compare predictions for multiple images"""
    results = []
    
    for img_path in image_paths:
        try:
            # Load and preprocess image
            img = Image.open(img_path).convert("RGB")
            image_tensor = transform(img).unsqueeze(0)
            
            # Get predictions
            pytorch_class, pytorch_conf = predict_pytorch(pytorch_model, image_tensor)
            onnx_class, onnx_conf = predict_onnx(onnx_session, image_tensor)
            
            # Get class names
            pytorch_label = get_class_name(pytorch_class, labels)
            onnx_label = get_class_name(onnx_class, labels)
            
            # Check if predictions match
            match = pytorch_label == onnx_label
            diff_note = None
            
            if not match:
                diff_note = f"Disagreement: {pytorch_label} vs {onnx_label}"
            elif pytorch_conf < 0.5 or onnx_conf < 0.5:
                diff_note = "Low confidence prediction"
            
            results.append({
                "input_name": Path(img_path).stem,
                "original_prediction": pytorch_label,
                "converted_prediction": onnx_label,
                "original_confidence_or_value": round(pytorch_conf, 4),
                "converted_confidence_or_value": round(onnx_conf, 4),
                "match": "Yes" if match else "No",
                "difference_note": diff_note if diff_note else "None"
            })
            
            print(f"✓ {Path(img_path).name}: {pytorch_label} ({pytorch_conf:.4f}) vs {onnx_label} ({onnx_conf:.4f}) - {'Match' if match else 'Mismatch'}")
            
        except Exception as e:
            print(f"✗ Error processing {img_path}: {e}")
            results.append({
                "input_name": Path(img_path).stem,
                "original_prediction": "ERROR",
                "converted_prediction": "ERROR",
                "original_confidence_or_value": 0.0,
                "converted_confidence_or_value": 0.0,
                "match": "No",
                "difference_note": str(e)
            })
    
    return results

def main():
    """Main function to compare predictions"""
    print("=" * 60)
    print("PyTorch vs ONNX Model Comparison")
    print("=" * 60)
    
    # Define image paths (adjust these to your actual images)
    # You can change these paths to where your 5 images are located
    image_paths = [
        "Lab_Upgrade/test_images/image_01_golden.jpg",
        "Lab_Upgrade/test_images/image_02_dog.jpg", 
        "Lab_Upgrade/test_images/image_03_car.jpg",
        "Lab_Upgrade/test_images/image_04_keyboard.jpg",
        "Lab_Upgrade/test_images/image_05_random_art.png"
    ]
    
    # Alternative: use images in current directory
    # Check if images exist, if not try current directory
    existing_images = []
    for path in image_paths:
        if Path(path).exists():
            existing_images.append(path)
    
    # If no images found in data/images, try current directory
    if not existing_images:
        print("\n⚠️  No images found in data/images/")
        print("Looking for images in current directory...")
        for i in range(1, 6):
            potential_paths = [
                f"image_{i:02d}.jpg",
                f"image_{i}.jpg",
                f"test_image_{i}.jpg"
            ]
            for pot_path in potential_paths:
                if Path(pot_path).exists():
                    existing_images.append(pot_path)
                    break
    
    if not existing_images:
        print("\n❌ No images found! Please ensure you have 5 images to test.")
        print("You can:")
        print("  1. Place images in 'data/images/' directory")
        print("  2. Or update image_paths in the script with your actual image locations")
        print("\nExpected image names: image_01.jpg, image_02.jpg, etc.")
        return 1
    
    print(f"\n📸 Found {len(existing_images)} image(s) to process\n")
    
    try:
        # Load models
        print("🔄 Loading models...")
        pytorch_model, onnx_session = load_models()
        print("✓ Models loaded successfully\n")
        
        # Load ImageNet labels
        print("📋 Loading ImageNet labels...")
        labels = load_imagenet_labels()
        print(f"✓ Loaded {len(labels)} classes\n")
        
        # Compare predictions
        print("🔍 Running predictions...")
        print("-" * 60)
        results = compare_predictions(existing_images, pytorch_model, onnx_session, labels)
        print("-" * 60)
        
        # Create DataFrame and save to CSV
        df = pd.DataFrame(results)
        
        # Create output directory if it doesn't exist
        output_dir = Path("outputs")
        output_dir.mkdir(exist_ok=True)
        
        csv_path = output_dir / "model_output_comparison_ca_nhan.csv"
        df.to_csv(csv_path, index=False, encoding="utf-8")
        
        # Display summary
        print(f"\n📊 Summary:")
        print(f"  Total images: {len(results)}")
        print(f"  Matches: {sum(1 for r in results if r['match'] == 'Yes')}")
        print(f"  Mismatches: {sum(1 for r in results if r['match'] == 'No')}")
        
        # Display confidence comparison
        print(f"\n📈 Confidence Comparison:")
        for r in results:
            if r['match'] == 'Yes' and r['difference_note'] != "Low confidence prediction":
                diff = abs(r['original_confidence_or_value'] - r['converted_confidence_or_value'])
                print(f"  {r['input_name']}: diff = {diff:.6f}")
        
        print(f"\n✅ Results saved to: {csv_path}")
        
        # Display first few rows
        print(f"\n📄 Preview of CSV output:")
        print(df.to_string(index=False))
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())