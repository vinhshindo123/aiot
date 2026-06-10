"""
Lab 6 - Computer Vision as IoT Sensor - ADVANCED VERSION
Features: ROI selection, adjustable threshold/Canny parameters, motion detection tuning, parameter experiment logging
"""

from __future__ import annotations

import csv
import json
import time
import uuid
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import cv2
import numpy as np
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image

# ==================== PATH CONFIGURATION ====================
ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw_images"
PROCESSED_DIR = DATA_DIR / "processed_images"
VIDEO_DIR = DATA_DIR / "videos"
OUTPUT_DIR = ROOT / "outputs"
METADATA_CSV = OUTPUT_DIR / "image_metadata.csv"
EVENT_CSV = OUTPUT_DIR / "image_event_log.csv"
PARAMETER_EXPERIMENT_CSV = OUTPUT_DIR / "parameter_experiment_log.csv"
INDEX_HTML = ROOT / "index.html"

for folder in [RAW_DIR, PROCESSED_DIR, VIDEO_DIR, OUTPUT_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

# ==================== CSV FIELD DEFINITIONS ====================
METADATA_FIELDS = [
    "image_id", "device_id", "timestamp", "source_type", "image_path", "processed_path",
    "width", "height", "brightness", "blur_score", "processing_status", 
    "processing_time_ms", "roi_used", "note"
]

EVENT_FIELDS = [
    "event_id", "image_id", "timestamp", "event_type", "score", "severity", 
    "explanation", "action_hint", "rule_used"
]

PARAMETER_FIELDS = [
    "experiment_id", "timestamp", "param_group", "param_name", "param_value",
    "image_id", "observed_effect", "notes"
]


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
    if not path:
        return None
    try:
        rel = path.resolve().relative_to(ROOT.resolve())
        return f"/files/{rel.as_posix()}"
    except Exception:
        return None


def validate_image_bytes(data: bytes) -> Image.Image:
    try:
        return Image.open(BytesIO(data)).convert("RGB")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid image file: {exc}") from exc


def pil_to_bgr(img: Image.Image) -> np.ndarray:
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)


def frame_to_jpeg_bytes(frame_bgr: np.ndarray) -> bytes:
    ok, buffer = cv2.imencode(".jpg", frame_bgr)
    if not ok:
        raise RuntimeError("Could not encode frame as JPEG")
    return buffer.tobytes()


def compute_brightness(frame_bgr: np.ndarray, roi: Optional[Tuple[int, int, int, int]] = None) -> float:
    """Tính độ sáng trung bình, có thể chỉ trên ROI"""
    if roi is not None:
        x, y, w, h = roi
        frame_roi = frame_bgr[y:y+h, x:x+w]
    else:
        frame_roi = frame_bgr
    gray = cv2.cvtColor(frame_roi, cv2.COLOR_BGR2GRAY)
    return float(np.mean(gray))


def compute_blur_score(frame_bgr: np.ndarray, roi: Optional[Tuple[int, int, int, int]] = None) -> float:
    """Tính độ sắc nét bằng variance của Laplacian"""
    if roi is not None:
        x, y, w, h = roi
        frame_roi = frame_bgr[y:y+h, x:x+w]
    else:
        frame_roi = frame_bgr
    gray = cv2.cvtColor(frame_roi, cv2.COLOR_BGR2GRAY)
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    return float(laplacian.var())


def crop_roi(frame_bgr: np.ndarray, roi: Optional[Tuple[int, int, int, int]] = None) -> np.ndarray:
    """Cắt vùng quan tâm (ROI) nếu được chỉ định"""
    if roi is None:
        return frame_bgr
    x, y, w, h = roi
    # Đảm bảo ROI nằm trong khung hình
    x = max(0, min(x, frame_bgr.shape[1] - 1))
    y = max(0, min(y, frame_bgr.shape[0] - 1))
    w = min(w, frame_bgr.shape[1] - x)
    h = min(h, frame_bgr.shape[0] - y)
    return frame_bgr[y:y+h, x:x+w].copy()


def draw_roi_on_frame(frame_bgr: np.ndarray, roi: Optional[Tuple[int, int, int, int]] = None) -> np.ndarray:
    """Vẽ khung ROI lên ảnh để hiển thị"""
    result = frame_bgr.copy()
    if roi is not None:
        x, y, w, h = roi
        cv2.rectangle(result, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(result, "ROI", (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    return result


def event_from_quality(brightness: float, blur_score: float) -> Tuple[str, str, str, str]:
    """Tạo event dựa trên chất lượng ảnh"""
    if brightness < 70:
        return "LOW_LIGHT", "WARNING", f"Image brightness is low ({brightness:.1f}); AI inference may be less reliable.", "Improve lighting or use flash"
    elif brightness > 230:
        return "OVER_EXPOSED", "WARNING", f"Image is over-exposed ({brightness:.1f}); details may be lost.", "Reduce exposure or adjust lighting"
    elif blur_score < 100:
        return "BLURRY_IMAGE", "WARNING", f"Image blur score is low ({blur_score:.1f}); image may be out of focus.", "Check camera focus or stabilize camera"
    else:
        return "IMAGE_QUALITY_OK", "NORMAL", f"Image quality is good (brightness={brightness:.1f}, blur={blur_score:.1f}).", "Ready for object detection"


def log_parameter_experiment(param_group: str, param_name: str, param_value: Any, 
                              image_id: str, observed_effect: str, notes: str = "") -> None:
    """Ghi log thử nghiệm tham số"""
    experiment_id = f"exp_{uuid.uuid4().hex[:8]}"
    row = {
        "experiment_id": experiment_id,
        "timestamp": now_iso(),
        "param_group": param_group,
        "param_name": param_name,
        "param_value": str(param_value),
        "image_id": image_id,
        "observed_effect": observed_effect,
        "notes": notes,
    }
    append_csv(PARAMETER_EXPERIMENT_CSV, PARAMETER_FIELDS, row)


def create_advanced_processed_image(
    frame_bgr: np.ndarray, 
    image_id: str,
    roi: Optional[Tuple[int, int, int, int]] = None,
    threshold_value: int = 120,
    canny_low: int = 80,
    canny_high: int = 160
) -> Tuple[Path, float, Dict[str, Any]]:
    """
    Tạo ảnh xử lý nâng cao gồm:
    - Original with ROI
    - Grayscale
    - Threshold (có thể điều chỉnh)
    - Canny Edge (có thể điều chỉnh)
    """
    start = time.perf_counter()
    
    # Cắt ROI nếu có
    frame_roi = crop_roi(frame_bgr, roi)
    frame_with_roi_display = draw_roi_on_frame(frame_bgr, roi)
    
    # Resize để hiển thị đồng nhất
    h, w = frame_roi.shape[:2]
    display_size = (320, 240)
    
    # 1. Original with ROI
    original_resized = cv2.resize(frame_with_roi_display, display_size)
    
    # 2. Grayscale
    gray = cv2.cvtColor(cv2.resize(frame_roi, display_size), cv2.COLOR_BGR2GRAY)
    gray_bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    
    # 3. Threshold với tham số
    _, threshold = cv2.threshold(gray, threshold_value, 255, cv2.THRESH_BINARY)
    threshold_bgr = cv2.cvtColor(threshold, cv2.COLOR_GRAY2BGR)
    
    # 4. Canny Edge với tham số
    edges = cv2.Canny(gray, canny_low, canny_high)
    edge_bgr = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
    
    def label(tile: np.ndarray, text: str, sub_text: str = "") -> np.ndarray:
        canvas = tile.copy()
        cv2.rectangle(canvas, (0, 0), (display_size[0], 35), (255, 255, 255), -1)
        cv2.putText(canvas, text, (8, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        if sub_text:
            cv2.putText(canvas, sub_text, (8, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (100, 100, 100), 1)
        return canvas
    
    top = np.hstack([
        label(original_resized, "1. ORIGINAL", f"ROI: {roi if roi else 'FULL'}"),
        label(gray_bgr, "2. GRAYSCALE", "")
    ])
    bottom = np.hstack([
        label(threshold_bgr, f"3. THRESHOLD", f"val={threshold_value}"),
        label(edge_bgr, f"4. CANNY EDGE", f"low={canny_low}, high={canny_high}")
    ])
    sheet = np.vstack([top, bottom])
    
    out_path = PROCESSED_DIR / f"{image_id}_advanced_processing.jpg"
    cv2.imwrite(str(out_path), sheet)
    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
    
    brightness = compute_brightness(frame_bgr, roi)
    blur_score = compute_blur_score(frame_bgr, roi)
    
    stats = {
        "brightness": round(brightness, 2),
        "blur_score": round(blur_score, 2),
        "width": int(frame_bgr.shape[1]),
        "height": int(frame_bgr.shape[0]),
        "roi_used": str(roi) if roi else "FULL_FRAME"
    }
    return out_path, elapsed_ms, stats


def log_image_pipeline_advanced(
    frame_bgr: np.ndarray, 
    source_type: str, 
    device_id: str, 
    note: str = "",
    roi: Optional[Tuple[int, int, int, int]] = None,
    threshold_value: int = 120,
    canny_low: int = 80,
    canny_high: int = 160
) -> Dict[str, Any]:
    """Save raw image, preprocess image with advanced parameters, write metadata and events."""
    image_id = f"img_{uuid.uuid4().hex[:10]}"
    timestamp = now_iso()
    
    # Lưu ảnh gốc (có vẽ ROI để tham khảo)
    raw_with_roi = draw_roi_on_frame(frame_bgr, roi)
    raw_path = RAW_DIR / f"{image_id}.jpg"
    cv2.imwrite(str(raw_path), raw_with_roi)
    
    # Xử lý ảnh nâng cao
    processed_path, processing_time_ms, stats = create_advanced_processed_image(
        frame_bgr, image_id, roi, threshold_value, canny_low, canny_high
    )
    
    brightness = stats["brightness"]
    blur_score = stats["blur_score"]
    
    # Metadata
    metadata_row = {
        "image_id": image_id,
        "device_id": device_id,
        "timestamp": timestamp,
        "source_type": source_type,
        "image_path": str(raw_path.relative_to(ROOT)),
        "processed_path": str(processed_path.relative_to(ROOT)),
        "width": stats["width"],
        "height": stats["height"],
        "brightness": brightness,
        "blur_score": blur_score,
        "processing_status": "processed_advanced",
        "processing_time_ms": processing_time_ms,
        "roi_used": stats["roi_used"],
        "note": f"{note}, threshold={threshold_value}, canny=({canny_low},{canny_high})",
    }
    append_csv(METADATA_CSV, METADATA_FIELDS, metadata_row)
    
    # Event từ chất lượng ảnh
    event_type, severity, explanation, action_hint = event_from_quality(brightness, blur_score)
    event_row = {
        "event_id": f"evt_{uuid.uuid4().hex[:10]}",
        "image_id": image_id,
        "timestamp": timestamp,
        "event_type": event_type,
        "score": brightness if "LIGHT" in event_type else blur_score,
        "severity": severity,
        "explanation": explanation,
        "action_hint": action_hint,
        "rule_used": f"brightness_threshold=70, blur_threshold=100",
    }
    append_csv(EVENT_CSV, EVENT_FIELDS, event_row)
    
    # Ghi log tham số vào experiment log
    log_parameter_experiment("Threshold", "threshold_value", threshold_value, 
                              image_id, f"Binary threshold applied, result shows {threshold_value} separation", 
                              "Test effect on image segmentation")
    log_parameter_experiment("Canny Edge", "canny_low", canny_low, 
                              image_id, f"Low threshold for edge detection", "")
    log_parameter_experiment("Canny Edge", "canny_high", canny_high, 
                              image_id, f"High threshold for edge detection", "")
    if roi:
        log_parameter_experiment("ROI", "roi", str(roi), 
                                  image_id, f"Processing restricted to region {roi}", 
                                  "Reduced processing area for efficiency")
    
    return {
        "image_id": image_id,
        "metadata": metadata_row,
        "event": event_row,
        "raw_image_url": relative_url(raw_path),
        "processed_image_url": relative_url(processed_path),
        "brightness": brightness,
        "blur_score": blur_score,
    }


# ==================== CAMERA FUNCTIONS ====================
def parse_camera_source(source: str) -> Any:
    source = str(source).strip()
    return int(source) if source.isdigit() else source


def simulated_frame(counter: int = 0, width: int = 640, height: int = 360) -> np.ndarray:
    """Fallback stream when no laptop/IP camera is available."""
    frame = np.full((height, width, 3), 245, dtype=np.uint8)
    x = 30 + (counter * 12) % max(1, width - 180)
    y = 80 + (counter * 7) % max(1, height - 170)
    cv2.rectangle(frame, (x, 120), (x + 130, 240), (40, 140, 240), -1)
    cv2.circle(frame, (width - 110, y), 38, (80, 200, 120), -1)
    cv2.putText(frame, "SIMULATED CAMERA STREAM", (25, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    cv2.putText(frame, "Use source=0 for laptop camera or an IP camera URL", (25, height - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 1)
    return frame


def open_capture(source: str) -> Optional[cv2.VideoCapture]:
    try:
        src = parse_camera_source(source)
        cap = cv2.VideoCapture(src)
        if not cap.isOpened():
            return None
        return cap
    except Exception:
        return None


def read_one_frame(source: str = "0") -> Tuple[np.ndarray, str]:
    cap = open_capture(source)
    if cap is None:
        return simulated_frame(0), "simulated"
    ok, frame = cap.read()
    cap.release()
    if not ok or frame is None:
        return simulated_frame(0), "simulated"
    return frame, "camera"


def stream_frames(source: str = "0") -> Iterable[bytes]:
    cap = open_capture(source)
    counter = 0
    while True:
        if cap is None:
            frame = simulated_frame(counter)
            source_label = "SIMULATED"
        else:
            ok, frame = cap.read()
            if not ok or frame is None:
                frame = simulated_frame(counter)
                source_label = "SIMULATED_AFTER_CAMERA_ERROR"
            else:
                source_label = "LIVE_CAMERA"
        
        cv2.rectangle(frame, (0, 0), (frame.shape[1], 32), (255, 255, 255), -1)
        cv2.putText(frame, f"{source_label} | source={source} | frame={counter}", (10, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (0, 0, 0), 2)
        jpg = frame_to_jpeg_bytes(frame)
        yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + jpg + b"\r\n"
        counter += 1
        time.sleep(0.08)


# ==================== MOTION CAPTURE ADVANCED ====================
def motion_capture_advanced(
    source: str, 
    seconds: int = 8, 
    diff_threshold: int = 25, 
    min_area: int = 800,
    roi: Optional[Tuple[int, int, int, int]] = None,
    cooldown: float = 0
) -> Dict[str, Any]:
    """
    Capture motion with advanced parameters:
    - diff_threshold: ngưỡng khác biệt giữa các frame
    - min_area: diện tích tối thiểu để coi là chuyển động
    - roi: vùng quan tâm để giảm nhiễu
    - cooldown: thời gian chờ giữa các event (giây)
    """
    seconds = max(1, min(int(seconds), 30))
    cap = open_capture(source)
    prev_gray = None
    best_frame = None
    best_score = 0.0
    frames_seen = 0
    last_event_time = 0
    start = time.perf_counter()
    
    while time.perf_counter() - start < seconds:
        if cap is None:
            frame = simulated_frame(frames_seen)
        else:
            ok, frame = cap.read()
            if not ok or frame is None:
                frame = simulated_frame(frames_seen)
        frames_seen += 1
        
        # Apply ROI for motion detection
        frame_roi = crop_roi(frame, roi)
        gray = cv2.cvtColor(cv2.resize(frame_roi, (320, 240)), cv2.COLOR_BGR2GRAY)
        
        if prev_gray is not None:
            diff = cv2.absdiff(prev_gray, gray)
            _, mask = cv2.threshold(diff, diff_threshold, 255, cv2.THRESH_BINARY)
            
            # Morphological operations to reduce noise
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            score = float(sum(cv2.contourArea(c) for c in contours))
            
            if score > best_score:
                best_score = score
                best_frame = frame.copy()
        prev_gray = gray
        time.sleep(0.08)
    
    if cap is not None:
        cap.release()
    if best_frame is None:
        best_frame = simulated_frame(frames_seen)
    
    motion_detected = best_score >= float(min_area)
    
    # Check cooldown
    current_time = time.time()
    if motion_detected and (current_time - last_event_time) >= cooldown:
        last_event_time = current_time
    
    result = log_image_pipeline_advanced(
        best_frame, 
        source_type="motion_capture_advanced", 
        device_id=f"camera:{source}", 
        note=f"motion_score={round(best_score, 2)}, diff_threshold={diff_threshold}, min_area={min_area}, roi={roi if roi else 'full'}",
        roi=roi,
        threshold_value=120,
        canny_low=80,
        canny_high=160
    )
    
    motion_event = {
        "event_id": f"evt_{uuid.uuid4().hex[:10]}",
        "image_id": result["image_id"],
        "timestamp": now_iso(),
        "event_type": "MOTION_DETECTED" if motion_detected else "NO_SIGNIFICANT_MOTION",
        "score": round(best_score, 2),
        "severity": "WARNING" if motion_detected else "NORMAL",
        "explanation": f"Motion score {round(best_score, 2)} {'exceeded' if motion_detected else 'below'} threshold {min_area}.",
        "action_hint": "Review captured image." if motion_detected else "Continue monitoring.",
        "rule_used": f"diff_threshold={diff_threshold}, min_area={min_area}, cooldown={cooldown}",
    }
    append_csv(EVENT_CSV, EVENT_FIELDS, motion_event)
    
    # Log motion parameters
    log_parameter_experiment("Motion Detection", "diff_threshold", diff_threshold, 
                              result["image_id"], f"Frame difference sensitivity set to {diff_threshold}", 
                              "Lower = more sensitive, higher = less noise")
    log_parameter_experiment("Motion Detection", "min_area", min_area, 
                              result["image_id"], f"Minimum area for motion: {min_area}", 
                              "Smaller = detects small movements")
    log_parameter_experiment("Motion Detection", "cooldown", cooldown, 
                              result["image_id"], f"Event cooldown: {cooldown}s", 
                              "Prevents repeated alerts")
    
    result["motion_event"] = motion_event
    result["motion_detected"] = motion_detected
    result["motion_score"] = round(best_score, 2)
    result["frames_seen"] = frames_seen
    return result


# ==================== FASTAPI APP ====================
app = FastAPI(title="Lab 6 - Computer Vision as IoT Sensor (Advanced)", 
              description="Advanced camera stream, ROI, threshold tuning, Canny edge, motion detection with parameter logging")
app.mount("/files", StaticFiles(directory=str(ROOT)), name="files")


@app.get("/")
def home() -> FileResponse:
    return FileResponse(INDEX_HTML)


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"status": "ok", "lab": "Lab 6 - Computer Vision as IoT Sensor (Advanced)", 
            "outputs": {"metadata_csv": str(METADATA_CSV.relative_to(ROOT)), 
                       "event_csv": str(EVENT_CSV.relative_to(ROOT)),
                       "param_log": str(PARAMETER_EXPERIMENT_CSV.relative_to(ROOT))}}


@app.post("/upload-image")
async def upload_image(
    file: UploadFile = File(...), 
    device_id: str = "upload_client",
    roi_x: int = Query(0, ge=0),
    roi_y: int = Query(0, ge=0),
    roi_w: int = Query(0, ge=0),
    roi_h: int = Query(0, ge=0),
    threshold_value: int = Query(120, ge=0, le=255),
    canny_low: int = Query(80, ge=0, le=255),
    canny_high: int = Query(160, ge=0, le=255)
) -> Dict[str, Any]:
    data = await file.read()
    img = validate_image_bytes(data)
    frame = pil_to_bgr(img)
    
    roi = None
    if roi_w > 0 and roi_h > 0:
        roi = (roi_x, roi_y, roi_w, roi_h)
    
    return log_image_pipeline_advanced(
        frame, source_type="upload", device_id=device_id, 
        note=f"filename={file.filename}",
        roi=roi, threshold_value=threshold_value, 
        canny_low=canny_low, canny_high=canny_high
    )


@app.get("/snapshot")
def snapshot(
    source: str = Query("0"),
    roi_x: int = Query(0, ge=0),
    roi_y: int = Query(0, ge=0),
    roi_w: int = Query(0, ge=0),
    roi_h: int = Query(0, ge=0),
    threshold_value: int = Query(120, ge=0, le=255),
    canny_low: int = Query(80, ge=0, le=255),
    canny_high: int = Query(160, ge=0, le=255)
) -> Dict[str, Any]:
    frame, source_type = read_one_frame(source)
    roi = None
    if roi_w > 0 and roi_h > 0:
        roi = (roi_x, roi_y, roi_w, roi_h)
    
    return log_image_pipeline_advanced(
        frame, source_type=source_type, device_id=f"camera:{source}", 
        note="snapshot with advanced parameters",
        roi=roi, threshold_value=threshold_value, 
        canny_low=canny_low, canny_high=canny_high
    )


@app.get("/motion-capture")
def motion_capture_endpoint(
    source: str = Query("0"),
    seconds: int = Query(8, ge=1, le=30),
    diff_threshold: int = Query(25, ge=1, le=255),
    min_area: int = Query(800, ge=10, le=50000),
    roi_x: int = Query(0, ge=0),
    roi_y: int = Query(0, ge=0),
    roi_w: int = Query(0, ge=0),
    roi_h: int = Query(0, ge=0),
    cooldown: float = Query(0, ge=0, le=10)
) -> Dict[str, Any]:
    roi = None
    if roi_w > 0 and roi_h > 0:
        roi = (roi_x, roi_y, roi_w, roi_h)
    
    return motion_capture_advanced(
        source, seconds=seconds, diff_threshold=diff_threshold, 
        min_area=min_area, roi=roi, cooldown=cooldown
    )


@app.get("/video_feed")
def video_feed(source: str = Query("0")) -> StreamingResponse:
    return StreamingResponse(stream_frames(source), media_type="multipart/x-mixed-replace; boundary=frame")


@app.get("/metadata")
def metadata(limit: int = 20) -> Dict[str, Any]:
    rows = read_csv(METADATA_CSV)
    return {"count": len(rows), "items": rows[-limit:]}


@app.get("/events")
def events(limit: int = 20) -> Dict[str, Any]:
    rows = read_csv(EVENT_CSV)
    return {"count": len(rows), "items": rows[-limit:]}


@app.get("/param-logs")
def param_logs(limit: int = 50) -> Dict[str, Any]:
    rows = read_csv(PARAMETER_EXPERIMENT_CSV)
    return {"count": len(rows), "items": rows[-limit:]}


@app.get("/latest")
def latest() -> Dict[str, Any]:
    meta_rows = read_csv(METADATA_CSV)
    event_rows = read_csv(EVENT_CSV)
    latest_meta = meta_rows[-1] if meta_rows else None
    raw_url = processed_url = None
    if latest_meta:
        raw_url = relative_url(ROOT / latest_meta.get("image_path", ""))
        processed_url = relative_url(ROOT / latest_meta.get("processed_path", ""))
    return {
        "latest_metadata": latest_meta, 
        "latest_event": event_rows[-1] if event_rows else None, 
        "raw_image_url": raw_url, 
        "processed_image_url": processed_url, 
        "metadata_count": len(meta_rows), 
        "event_count": len(event_rows)
    }


@app.get("/test-camera")
def test_camera(source: str = Query("0")) -> Dict[str, Any]:
    """Test camera connectivity"""
    cap = open_capture(source)
    if cap is None:
        return {"status": "failed", "message": "Cannot open camera", "using_simulated": True}
    ret, frame = cap.read()
    cap.release()
    if ret and frame is not None:
        return {"status": "ok", "message": "Camera working", "frame_shape": frame.shape}
    else:
        return {"status": "failed", "message": "Cannot read frame", "using_simulated": True}


if __name__ == "__main__":
    # Smoke test
    frame = simulated_frame(1)
    result = log_image_pipeline_advanced(frame, source_type="script", device_id="local_smoke", 
                                          note="python app.py smoke test - advanced")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("\n✅ Advanced Lab 6 smoke test passed!")
    print(f"📊 Parameter experiment log: {PARAMETER_EXPERIMENT_CSV}")