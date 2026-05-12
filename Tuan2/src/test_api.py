import json
import requests

BASE_URL = "http://127.0.0.1:8000"

sample_payload = {
    "location": "station_center",
    "timestamp": "2004-03-10 15:30:00",
    "PT08_S1_CO": 1100.5,
    "PT08_S2_NMHC": 950.2,
    "PT08_S3_NOx": 850.3,
    "PT08_S4_NO2": 680.7,
    "PT08_S5_O3": 550.1,
    "Temperature": 22.5,
    "Relative_Humidity": 48.3,
    "Absolute_Humidity": 9.2
}


if __name__ == "__main__":
    print("Checking /health ...")
    h = requests.get(f"{BASE_URL}/health", timeout=10)
    print(h.status_code, h.json())
    h.raise_for_status()

    print("\nChecking /model-info ...")
    info = requests.get(f"{BASE_URL}/model-info", timeout=10)
    print(info.status_code)
    print(json.dumps(info.json(), ensure_ascii=False, indent=2)[:1000])
    info.raise_for_status()

    print("\nChecking /predict ...")
    r = requests.post(f"{BASE_URL}/predict", json=sample_payload, timeout=10)
    print(r.status_code)
    print(json.dumps(r.json(), ensure_ascii=False, indent=2))
    r.raise_for_status()

    data = r.json()
    assert "predicted_co_concentration_mg_per_m3" in data
    assert "air_quality_level" in data
    assert "status" in data
    assert data["status"] == "success"
    
    print("\n✅ API TEST PASSED: FastAPI model deployment is working.")