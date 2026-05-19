from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
import argparse
import random
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)


def find_best_csv_file():
    """Tự động tìm file CSV phù hợp nhất trong thư mục data"""
    csv_files = list(DATA_DIR.glob("*.csv"))
    csv_files += list(DATA_DIR.glob("*.CSV"))
    
    if not csv_files:
        return None
    
    # Ưu tiên các file có chứa từ khóa
    priority_keywords = [
        "cleaned_data_IsDefault_Interpolate",  # File đã được làm sạch
        "IoTData_25K_with_interpolation",      # File có interpolation
        "IoTData_IsDefaultInterpolate",        # File có interpolate
        "IoTData_25K_without_interpolation",   # File raw hơn
        "IoTData --Raw--"                      # File raw nhất
    ]
    
    # Tìm file theo thứ tự ưu tiên
    for keyword in priority_keywords:
        for f in csv_files:
            if keyword.lower() in f.name.lower():
                print(f"✅ Chọn file: {f.name}")
                return f
    
    # Nếu không tìm thấy file ưu tiên, chọn file lớn nhất (có nhiều dữ liệu nhất)
    largest_file = max(csv_files, key=lambda f: f.stat().st_size)
    print(f"✅ Chọn file lớn nhất: {largest_file.name}")
    return largest_file


def inspect_csv_structure(file_path: Path):
    """Kiểm tra cấu trúc của file CSV"""
    print(f"\n🔍 Đang kiểm tra file: {file_path.name}")
    
    # Đọc 5 dòng đầu
    df_sample = pd.read_csv(file_path, nrows=5)
    print(f"Columns: {df_sample.columns.tolist()}")
    print(f"Shape: {df_sample.shape}")
    
    return df_sample.columns.tolist()


def load_hydroponics_dataset(source_path: Path) -> pd.DataFrame:
    """Load and preprocess Hydroponics dataset from Kaggle"""
    print(f"\n📂 Loading Hydroponics dataset from: {source_path}")
    
    # Kiểm tra cấu trúc file
    columns = inspect_csv_structure(source_path)
    
    # Đọc toàn bộ file
    df = pd.read_csv(source_path)
    print(f"Total rows: {len(df)}")
    
    # Phát hiện cột timestamp
    timestamp_candidates = ['timestamp', 'time', 'date', 'datetime', 'created_at', 'Time', 'Timestamp']
    timestamp_col = None
    for col in timestamp_candidates:
        if col in df.columns:
            timestamp_col = col
            break
    
    if timestamp_col is None:
        # Nếu không có timestamp, tạo cột mới
        print("⚠️ Không tìm thấy timestamp column, sẽ tạo mới")
        df['created_at'] = pd.date_range(start='2024-01-01', periods=len(df), freq='H')
    else:
        df = df.rename(columns={timestamp_col: 'created_at'})
        df['created_at'] = pd.to_datetime(df['created_at'])
    
    # Phát hiện cột node_id
    node_candidates = ['node_id', 'node', 'device_id', 'Device', 'Node']
    node_col = None
    for col in node_candidates:
        if col in df.columns:
            node_col = col
            break
    
    if node_col is None:
        print("⚠️ Không tìm thấy node_id column, sẽ tạo mặc định")
        df['node_id'] = 'NODE_01'
    else:
        df = df.rename(columns={node_col: 'node_id'})
        df['node_id'] = df['node_id'].astype(str)
    
    # Phát hiện và mapping các sensor columns
    sensor_mapping = {
        'temp': ['temp', 'temperature', 'Temperature', 'TEMP'],
        'humi': ['humi', 'humidity', 'Humidity', 'HUMI', 'RH'],
        'ph': ['ph', 'pH', 'Ph'],
        'ec': ['ec', 'EC', 'E.C.', 'conductivity'],
        'water_temp': ['water_temp', 'water_temperature', 'WaterTemp', 'water temperature'],
        'light': ['light', 'light_intensity', 'Light', 'illuminance', 'lux'],
        'co2': ['co2', 'CO2', 'carbon_dioxide', 'CarbonDioxide'],
        'soil': ['soil', 'soil_moisture', 'Soil', 'moisture']
    }
    
    for target, possible_names in sensor_mapping.items():
        for name in possible_names:
            if name in df.columns:
                df = df.rename(columns={name: target})
                print(f"  ✓ Mapped '{name}' → '{target}'")
                break
    
    # Đảm bảo label column tồn tại
    if 'label' in df.columns:
        df['label'] = df['label'].fillna(0).astype(int)
    elif 'anomaly' in df.columns:
        df = df.rename(columns={'anomaly': 'label'})
        df['label'] = df['label'].fillna(0).astype(int)
    else:
        print("⚠️ Không tìm thấy label column, sẽ tạo mặc định (0)")
        df['label'] = 0
    
    # Sort và clean
    df = df.sort_values(['node_id', 'created_at']).reset_index(drop=True)
    
    # Loại bỏ duplicate
    df = df.drop_duplicates(['node_id', 'created_at']).reset_index(drop=True)
    
    return df


def main() -> None:
    parser = argparse.ArgumentParser(description="Load Hydroponics dataset from Kaggle")
    parser.add_argument("--source", help="Path to the downloaded hydroponics CSV file from Kaggle")
    parser.add_argument("--auto", action="store_true", help="Auto-detect best CSV file")
    args = parser.parse_args()
    
    # Xác định file nguồn
    if args.source:
        src = Path(args.source)
        if not src.exists():
            print(f"❌ Source file not found: {src}")
            print(f"Current working directory: {Path.cwd()}")
            print(f"Files in data directory: {list(DATA_DIR.glob('*'))}")
            return
    elif args.auto:
        src = find_best_csv_file()
        if src is None:
            print("❌ Không tìm thấy file CSV nào trong thư mục data/")
            print("\n📥 Hãy đặt file CSV đã giải nén vào thư mục data/")
            return
    else:
        # Thử auto-detect nếu không có argument
        src = find_best_csv_file()
        if src is None:
            print("❌ Không tìm thấy file CSV. Vui lòng chỉ định --source")
            print("\nUsage:")
            print("  python src/download_data.py --source data/<ten_file.csv>")
            print("  python src/download_data.py --auto  # Auto-detect")
            return
    
    print(f"\n📁 Sử dụng file: {src}")
    
    # Load dataset
    try:
        df = load_hydroponics_dataset(src)
        
        # Save to data directory
        output_path = DATA_DIR / "measurements.csv"
        df.to_csv(output_path, index=False)
        print(f"\n✅ Saved master dataset: {output_path} ({len(df)} rows)")
        
        # Create sample file
        sample_path = DATA_DIR / "sample_measurements.csv"
        df.head(100).to_csv(sample_path, index=False)
        print(f"✅ Saved sample: {sample_path} (100 rows)")
        
        # Display dataset info
        print("\n" + "="*60)
        print("📊 DATASET INFO")
        print("="*60)
        print(f"Total rows: {len(df):,}")
        print(f"Columns: {df.columns.tolist()}")
        print(f"Date range: {df['created_at'].min()} → {df['created_at'].max()}")
        print(f"Nodes: {df['node_id'].nunique()} nodes")
        print(f"Anomaly count: {df['label'].sum():,} ({df['label'].mean()*100:.2f}%)")
        
        print("\n📋 Sample data:")
        print(df.head(10))
        
        print("\n📈 Statistics per sensor:")
        sensor_cols = [c for c in df.columns if c not in ['created_at', 'node_id', 'label'] 
                      and pd.api.types.is_numeric_dtype(df[c])]
        for col in sensor_cols:
            print(f"  {col}: min={df[col].min():.2f}, max={df[col].max():.2f}, mean={df[col].mean():.2f}")
        
    except Exception as e:
        print(f"\n❌ Error loading dataset: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()