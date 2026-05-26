from __future__ import annotations

from pathlib import Path

from Lab_01.src.utils import DATA_DIR

DATASET_PATH = DATA_DIR / "lab4_forecast_NODE03_augmented.csv"


def ensure_dataset_available() -> bool:
    DATA_DIR.mkdir(exist_ok=True)
    if DATASET_PATH.exists():
        print(f"Dataset ready: {DATASET_PATH}")
        return True
    print(f"Missing dataset: {DATASET_PATH}")
    print("Please copy the NODE_03 augmented dataset into the data/ folder.")
    return False


if __name__ == "__main__":
    if not ensure_dataset_available():
        raise FileNotFoundError("Dataset file lab4_forecast_NODE03_augmented.csv không tồn tại.")
