"""
Lab 6 - Computer Vision as IoT Sensor - FASTER R-CNN VERSION
Features: Object detection with bounding box, Person vs Animal classification
Async processing to avoid stream freezing
"""

from __future__ import annotations

import csv
import json
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
from threading import Lock, Thread
from queue import Queue

import cv2
import numpy as np
from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image

# ==================== AI MODEL IMPORT ====================
try:
    import torch
    import torchvision
    from torchvision.models.detection import fasterrcnn_resnet50_fpn
    from torchvision.models.detection import FasterRCNN_ResNet50_FPN_Weights
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("⚠️ PyTorch not installed. Install with: pip install torch torchvision")

# ==================== PATH CONFIGURATION ====================
ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
SNAPSHOTS_DIR = DATA_DIR / "snapshots"
OUTPUT_DIR = ROOT / "outputs"
EVENT_CSV = OUTPUT_DIR / "image_event_log.csv"
AI_DETECTION_CSV = OUTPUT_DIR / "ai_detection_log.csv"
INDEX_HTML = ROOT / "index.html"

for folder in [SNAPSHOTS_DIR, OUTPUT_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

# ==================== CSV FIELD DEFINITIONS ====================
EVENT_FIELDS = [
    "event_id", "image_id", "timestamp", "event_type", "score", "severity", 
    "explanation", "action_hint", "rule_used"
]

AI_DETECTION_FIELDS = [
    "detection_id", "image_id", "timestamp", "detection_type", 
    "confidence", "classification", "bbox", "image_path"
]

# ==================== GLOBAL STATE ====================
motion_detection_state = {
    "motion_detected": False,
    "current_motion_score": 0,
    "alert_message": "",
    "last_detection": None,
    "current_bbox": None
}
motion_lock = Lock()

# Queue cho AI processing
ai_queue = Queue(maxsize=5)
ai_result_cache = {
    "latest": None,
    "timestamp": 0,
    "snapshot_url": None
}
ai_cache_lock = Lock()

# ==================== COCO CLASS MAPPING ====================
COCO_CLASSES = {
    1: "person",
    16: "bird", 17: "cat", 18: "dog", 19: "horse", 20: "sheep", 21: "cow",
    22: "elephant", 23: "bear", 24: "zebra", 25: "giraffe"
}

PERSON_CLASS_IDS = {1}
ANIMAL_CLASS_IDS = {16, 17, 18, 19, 20, 21, 22, 23, 24, 25}


# ==================== AI PROCESSING THREAD ====================
class FasterRCNNProcessor:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.is_loaded = False
        self.confidence_threshold = 0.6
        self.processing = True
        self.load_model()
        self.start_worker()
    
    def load_model(self):
        if not TORCH_AVAILABLE:
            print("⚠️ PyTorch not available.")
            return
        
        try:
            print(f"\n🔄 Loading Faster R-CNN on {self.device}...")
            weights = FasterRCNN_ResNet50_FPN_Weights.DEFAULT
            self.model = fasterrcnn_resnet50_fpn(weights=weights)
            self.model.eval()
            self.model.to(self.device)
            self.transform = weights.transforms()
            self.is_loaded = True
            print(f"✅ Faster R-CNN loaded successfully\n")
        except Exception as e:
            print(f"❌ Failed to load model: {e}")
            self.is_loaded = False
    
    def start_worker(self):
        """Khởi động worker thread xử lý AI"""
        def worker():
            while self.processing:
                try:
                    # Lấy frame từ queue (timeout để không block mãi)
                    frame_data = ai_queue.get(timeout=0.1)
                    if frame_data is None:
                        continue
                    
                    frame, bbox, motion_score, request_id = frame_data
                    
                    # Chạy detection
                    result = self.detect_objects(frame)
                    
                    # Lưu kết quả vào cache
                    if result:
                        snapshot_result = self.save_detection(frame, result, motion_score)
                        with ai_cache_lock:
                            ai_result_cache["latest"] = snapshot_result
                            ai_result_cache["timestamp"] = time.time()
                            ai_result_cache["snapshot_url"] = snapshot_result.get("snapshot_url")
                    
                except Exception as e:
                    pass
        
        self.worker_thread = Thread(target=worker, daemon=True)
        self.worker_thread.start()
    
    def detect_objects(self, frame_bgr: np.ndarray) -> Optional[Dict[str, Any]]:
        if not self.is_loaded:
            return None
        
        try:
            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(frame_rgb)
            input_tensor = self.transform(pil_image).unsqueeze(0).to(self.device)
            
            with torch.no_grad():
                predictions = self.model(input_tensor)
            
            boxes = predictions[0]['boxes'].cpu().numpy()
            labels = predictions[0]['labels'].cpu().numpy()
            scores = predictions[0]['scores'].cpu().numpy()
            
            best_detection = None
            best_score = 0
            
            for box, label, score in zip(boxes, labels, scores):
                if score >= self.confidence_threshold:
                    if label in PERSON_CLASS_IDS:
                        classification = "person"
                        class_name = "person"
                    elif label in ANIMAL_CLASS_IDS:
                        classification = "animal"
                        class_name = COCO_CLASSES.get(label, "animal")
                    else:
                        continue
                    
                    if score > best_score:
                        x1, y1, x2, y2 = box.astype(int)
                        best_detection = {
                            "bbox": (int(x1), int(y1), int(x2 - x1), int(y2 - y1)),
                            "classification": classification,
                            "class_name": class_name,
                            "confidence": float(score)
                        }
                        best_score = score
            
            return best_detection
            
        except Exception as e:
            print(f"Detection error: {e}")
            return None
    
    def save_detection(self, frame: np.ndarray, detection: Dict, motion_score: float) -> Dict:
        image_id = f"detect_{uuid.uuid4().hex[:8]}"
        timestamp = now_iso()
        x, y, w, h = detection["bbox"]
        class_type = detection["classification"]
        confidence = detection["confidence"]
        class_name = detection["class_name"]
        
        # Vẽ kết quả
        annotated = frame.copy()
        cv2.rectangle(annotated, (x, y), (x + w, y + h), (0, 255, 0), 3)
        
        if class_type == "person":
            color = (0, 0, 255)
            label = f"PERSON: {confidence:.1%}"
        else:
            color = (0, 165, 255)
            label = f"ANIMAL ({class_name}): {confidence:.1%}"
        
        (text_w, text_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
        cv2.rectangle(annotated, (x, y - text_h - 10), (x + text_w + 10, y - 5), color, -1)
        cv2.putText(annotated, label, (x + 5, y - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        snapshot_path = SNAPSHOTS_DIR / f"{image_id}.jpg"
        cv2.imwrite(str(snapshot_path), annotated, [cv2.IMWRITE_JPEG_QUALITY, 95])
        
        # Ghi log
        detection_row = {
            "detection_id": f"det_{uuid.uuid4().hex[:8]}",
            "image_id": image_id,
            "timestamp": timestamp,
            "detection_type": f"fasterrcnn_{class_type}",
            "confidence": confidence,
            "classification": class_type,
            "bbox": f"{x},{y},{w},{h}",
            "image_path": str(snapshot_path.relative_to(ROOT))
        }
        append_csv(AI_DETECTION_CSV, AI_DETECTION_FIELDS, detection_row)
        
        # Ghi event
        severity = "CRITICAL" if class_type == "person" else "WARNING"
        explanation = f"🚨 PERSON DETECTED! Conf: {confidence:.1%}" if class_type == "person" else f"🐾 ANIMAL: {class_name} (Conf: {confidence:.1%})"
        
        event_row = {
            "event_id": f"evt_{uuid.uuid4().hex[:8]}",
            "image_id": image_id,
            "timestamp": timestamp,
            "event_type": f"AI_{class_type.upper()}",
            "score": motion_score,
            "severity": severity,
            "explanation": explanation,
            "action_hint": "Check snapshot",
            "rule_used": "faster_rcnn"
        }
        append_csv(EVENT_CSV, EVENT_FIELDS, event_row)
        
        return {
            "image_id": image_id,
            "snapshot_url": relative_url(snapshot_path),
            "classification": class_type,
            "confidence": confidence,
            "class_name": class_name,
            "message": explanation,
            "bbox": (x, y, w, h)
        }
    
    def queue_frame(self, frame: np.ndarray, bbox: Tuple, motion_score: float):
        """Đưa frame vào queue xử lý (bất đồng bộ)"""
        if not self.is_loaded:
            return
        try:
            request_id = uuid.uuid4().hex
            ai_queue.put((frame.copy(), bbox, motion_score, request_id), block=False)
        except:
            pass


# ==================== HELPER FUNCTIONS ====================
def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def append_csv(path: Path, fieldnames: List[str], row: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    file_exists = path.exists() and path.stat().st_size > 0
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow({key: row.get(key, "") for key in fieldnames})


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def relative_url(path: Optional[Path]) -> Optional[str]:
    if not path or not path.exists():
        return None
    try:
        rel = path.resolve().relative_to(ROOT.resolve())
        return f"/files/{rel.as_posix()}"
    except Exception:
        return None


def frame_to_jpeg_bytes(frame_bgr: np.ndarray, quality: int = 85) -> bytes:
    _, buffer = cv2.imencode(".jpg", frame_bgr, [cv2.IMWRITE_JPEG_QUALITY, quality])
    return buffer.tobytes()


def find_motion_bbox(prev_gray, current_gray, diff_threshold=20, min_area=400):
    """Tìm bounding box của vùng chuyển động - NHANH HƠN"""
    if prev_gray is None:
        return None, 0, False
    
    diff = cv2.absdiff(prev_gray, current_gray)
    diff = cv2.GaussianBlur(diff, (3, 3), 0)
    _, thresh = cv2.threshold(diff, diff_threshold, 255, cv2.THRESH_BINARY)
    
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if contours:
        valid_contours = [c for c in contours if cv2.contourArea(c) >= min_area]
        if valid_contours:
            all_points = np.vstack(valid_contours)
            x, y, w, h = cv2.boundingRect(all_points)
            
            # Mở rộng một chút
            expand = 10
            x = max(0, x - expand)
            y = max(0, y - expand)
            w = min(current_gray.shape[1] - x, w + 2 * expand)
            h = min(current_gray.shape[0] - y, h + 2 * expand)
            
            total_area = sum(cv2.contourArea(c) for c in valid_contours)
            return (x, y, w, h), total_area, True
    
    return None, 0, False


# ==================== CAMERA FUNCTIONS ====================
def simulated_frame(width: int = 640, height: int = 360) -> np.ndarray:
    frame = np.full((height, width, 3), 245, dtype=np.uint8)
    cv2.putText(frame, "NO CAMERA - ENTER '0' FOR LAPTOP CAMERA", (50, height//2), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    return frame


def open_capture(source: str) -> Optional[cv2.VideoCapture]:
    try:
        src = int(source) if source.isdigit() else source
        if isinstance(src, int):
            cap = cv2.VideoCapture(src, cv2.CAP_DSHOW)
        else:
            cap = cv2.VideoCapture(src)
        
        if cap.isOpened():
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            cap.set(cv2.CAP_PROP_FPS, 30)
            ret, test_frame = cap.read()
            if ret and test_frame is not None:
                print(f"✅ Camera opened: {source}")
                return cap
            cap.release()
        return None
    except Exception as e:
        print(f"Error opening camera {source}: {e}")
        return None


# Khởi tạo AI processor
print("\n" + "="*60)
print("🤖 Initializing Faster R-CNN (Async Mode)...")
print("="*60)
ai_processor = FasterRCNNProcessor() if TORCH_AVAILABLE else None


def stream_frames_with_detection(
    source: str = "0", 
    diff_threshold: int = 20, 
    min_area: int = 400,
    cooldown: int = 2
) -> Iterable[bytes]:
    """Stream với phát hiện chuyển động - AI xử lý bất đồng bộ"""
    cap = open_capture(source)
    counter = 0
    prev_gray = None
    last_motion_time = 0
    last_ai_queue_time = 0
    current_bbox = None
    motion_score = 0
    motion_detected = False
    
    while True:
        try:
            # Đọc frame
            if cap is None:
                frame = simulated_frame()
                source_label = "NO CAM"
            else:
                ok, frame = cap.read()
                if not ok or frame is None:
                    frame = simulated_frame()
                    source_label = "NO CAM"
                else:
                    source_label = "LIVE"
            
            # Motion detection trên frame nhỏ
            small_frame = cv2.resize(frame, (320, 240))
            gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)
            
            bbox, motion_score, has_motion = find_motion_bbox(
                prev_gray, gray, diff_threshold, min_area
            )
            
            current_time = time.time()
            
            # Cập nhật state
            if has_motion:
                motion_detected = True
                current_bbox = bbox
                last_motion_time = current_time
                
                # Gửi frame đi xử lý AI (bất đồng bộ, không block)
                if ai_processor and (current_time - last_ai_queue_time) >= cooldown:
                    last_ai_queue_time = current_time
                    # Scale bbox về kích thước gốc
                    if bbox:
                        scale_x = frame.shape[1] / 320
                        scale_y = frame.shape[0] / 240
                        orig_bbox = (
                            int(bbox[0] * scale_x),
                            int(bbox[1] * scale_y),
                            int(bbox[2] * scale_x),
                            int(bbox[3] * scale_y)
                        )
                        ai_processor.queue_frame(frame, orig_bbox, motion_score)
                
                with motion_lock:
                    motion_detection_state["motion_detected"] = True
                    motion_detection_state["current_motion_score"] = motion_score
                    motion_detection_state["current_bbox"] = bbox
                    motion_detection_state["alert_message"] = "⚠️ MOTION DETECTED - AI PROCESSING..."
            else:
                if (current_time - last_motion_time) > 0.5:
                    motion_detected = False
                    current_bbox = None
                with motion_lock:
                    motion_detection_state["motion_detected"] = motion_detected
                    if not motion_detected:
                        motion_detection_state["alert_message"] = ""
            
            prev_gray = gray
            
            # Lấy kết quả AI mới nhất từ cache
            latest_ai_result = None
            with ai_cache_lock:
                if ai_result_cache["latest"] and (current_time - ai_result_cache["timestamp"]) < 5:
                    latest_ai_result = ai_result_cache["latest"]
                    with motion_lock:
                        motion_detection_state["last_detection"] = latest_ai_result
                        motion_detection_state["alert_message"] = latest_ai_result.get("message", "")
            
            # Vẽ frame hiển thị
            display_frame = frame.copy()
            
            # Vẽ motion bounding box
            if current_bbox and motion_detected:
                scale_x = display_frame.shape[1] / 320
                scale_y = display_frame.shape[0] / 240
                x = int(current_bbox[0] * scale_x)
                y = int(current_bbox[1] * scale_y)
                w = int(current_bbox[2] * scale_x)
                h = int(current_bbox[3] * scale_y)
                cv2.rectangle(display_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            # Vẽ AI detection result
            if latest_ai_result and (current_time - ai_result_cache["timestamp"]) < 3:
                x, y, w, h = latest_ai_result.get("bbox", (0, 0, 0, 0))
                class_type = latest_ai_result.get("classification", "")
                confidence = latest_ai_result.get("confidence", 0)
                color = (0, 0, 255) if class_type == "person" else (0, 165, 255)
                cv2.rectangle(display_frame, (x, y), (x + w, y + h), color, 3)
                label = f"{class_type.upper()}: {confidence:.1%}"
                cv2.putText(display_frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            
            # Info panel
            info_h = 60
            overlay = display_frame.copy()
            cv2.rectangle(overlay, (0, 0), (display_frame.shape[1], info_h), (0, 0, 0), -1)
            display_frame = cv2.addWeighted(overlay, 0.6, display_frame, 0.4, 0)
            
            status = "🔴 MOTION" if motion_detected else "🟢 IDLE"
            cv2.putText(display_frame, f"{source_label} | {status} | Motion: {motion_score:.0f}", (10, 25), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            ai_status = "🤖 AI READY" if ai_processor and ai_processor.is_loaded else "⚠️ AI OFF"
            cv2.putText(display_frame, ai_status, (10, 48), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0) if ai_processor and ai_processor.is_loaded else (255, 255, 0), 1)
            
            # Stream
            jpg = frame_to_jpeg_bytes(display_frame)
            yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + jpg + b"\r\n"
            counter += 1
            time.sleep(0.033)
            
        except Exception as e:
            print(f"Stream error: {e}")
            time.sleep(0.05)


# ==================== FASTAPI APP ====================
app = FastAPI(title="AI Computer Vision - Faster R-CNN", 
              description="Async object detection with Faster R-CNN")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/files", StaticFiles(directory=str(ROOT)), name="files")


@app.get("/")
def home() -> FileResponse:
    return FileResponse(INDEX_HTML)


@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "status": "ok", 
        "ai_available": ai_processor is not None and ai_processor.is_loaded,
        "model_type": "Faster R-CNN (Async)"
    }


@app.get("/motion-status")
def motion_status() -> Dict[str, Any]:
    with motion_lock:
        latest_detection = motion_detection_state.get("last_detection")
        if latest_detection:
            latest_detection["snapshot_url"] = latest_detection.get("snapshot_url")
        return {
            "motion_detected": motion_detection_state["motion_detected"],
            "current_score": motion_detection_state["current_motion_score"],
            "alert_message": motion_detection_state["alert_message"],
            "last_detection": latest_detection
        }


@app.get("/video_feed")
def video_feed(
    source: str = Query("0"),
    diff_threshold: int = Query(20, ge=1, le=255),
    min_area: int = Query(400, ge=100, le=20000),
    cooldown: int = Query(2, ge=1, le=5)
) -> StreamingResponse:
    return StreamingResponse(
        stream_frames_with_detection(source, diff_threshold, min_area, cooldown), 
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


@app.get("/detections")
def detections(limit: int = 20) -> Dict[str, Any]:
    rows = read_csv(AI_DETECTION_CSV)
    valid_rows = []
    for row in rows[-limit:]:
        if row.get("image_path"):
            img_path = ROOT / row["image_path"]
            if img_path.exists():
                row["image_url"] = relative_url(img_path)
            valid_rows.append(row)
    return {"count": len(valid_rows), "items": valid_rows}


@app.get("/events")
def events(limit: int = 30) -> Dict[str, Any]:
    rows = read_csv(EVENT_CSV)
    return {"count": len(rows), "items": rows[-limit:]}


@app.get("/latest-snapshot")
def latest_snapshot() -> Dict[str, Any]:
    with ai_cache_lock:
        if ai_result_cache["snapshot_url"]:
            return {"snapshot_url": ai_result_cache["snapshot_url"]}
    
    rows = read_csv(AI_DETECTION_CSV)
    if rows:
        latest = rows[-1]
        img_path = ROOT / latest.get("image_path", "")
        if img_path.exists():
            return {
                "snapshot_url": relative_url(img_path),
                "classification": latest.get("classification", ""),
                "confidence": latest.get("confidence", ""),
                "timestamp": latest.get("timestamp", "")
            }
    return {"snapshot_url": None}


@app.get("/test-camera")
def test_camera(source: str = Query("0")) -> Dict[str, Any]:
    cap = open_capture(source)
    if cap is None:
        return {"status": "failed", "message": "Cannot open camera"}
    ret, frame = cap.read()
    cap.release()
    if ret and frame is not None:
        return {"status": "ok", "message": "Camera working"}
    return {"status": "failed", "message": "Cannot read frame"}


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🔍 AI Computer Vision - Faster R-CNN (Async Mode)")
    print("="*60)
    print(f"✅ Model: Faster R-CNN")
    print(f"   - Async processing (no stream blocking)")
    print(f"   - Person + Animal detection")
    print(f"📹 Open http://127.0.0.1:8000")
    print("="*60)