from pathlib import Path
import sys
import json
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DATA_DIR = PROJECT_ROOT / "data" 

from src.data_utils import (
    API_FEATURES,
    OUTPUTS_DIR,
    FIGURES_DIR,
    check_schema,
    clean_iot_data,
    create_features,
    ensure_dataset,
    evaluate_model,
    make_decision_log,
    save_artifacts,
    time_train_test_split,
    train_baseline_model,
    compute_train_stats,
    TARGET_COL,
)

if __name__ == "__main__":
    # Load và xử lý dữ liệu
    raw_df, dataset_status = ensure_dataset(prefer_public=True)
    print(f"Dataset loaded: {raw_df.shape}")
    
    # Clean data
    clean_df, cleaning_report = clean_iot_data(raw_df)
    print(f"After cleaning: {clean_df.shape}")
    
    # Feature engineering
    feature_df = create_features(clean_df)
    print(f"Features created: {feature_df.shape}")
    
    # Train/test split
    train_df, test_df = time_train_test_split(feature_df, test_ratio=0.25)
    print(f"Train: {train_df.shape}, Test: {test_df.shape}")
    
    # Train model
    model = train_baseline_model(train_df)
    metrics = evaluate_model(model, test_df)
    print(f"Model metrics: R²={metrics['r2']:.3f}, RMSE={metrics['rmse']:.3f}")
    
    # Train stats và decision log
    train_stats = compute_train_stats(train_df)
    decision_log = make_decision_log(model, test_df, train_stats, n_rows=200)
    
    # Lưu artifacts
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    clean_df.to_csv(DATA_DIR / "telemetry_clean.csv", index=False)
    feature_df.to_csv(DATA_DIR / "feature_dataset.csv", index=False)
    decision_log.to_csv(OUTPUTS_DIR / "decision_log.csv", index=False)
    
    save_artifacts(model, API_FEATURES, train_stats, metrics, dataset_status)
    
    # Vẽ biểu đồ cho Air Quality
    # 1. CO predictions vs actual
    plt.figure(figsize=(10, 4))
    test_sample = test_df.tail(200)
    preds = model.predict(test_sample[API_FEATURES])
    plt.plot(test_sample["timestamp"], test_sample[TARGET_COL].values, label="Actual CO", alpha=0.7)
    plt.plot(test_sample["timestamp"], preds, label="Predicted CO", alpha=0.7)
    plt.title("CO Concentration: Actual vs Predicted")
    plt.xlabel("Timestamp")
    plt.ylabel("CO (mg/m³)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "01_co_predictions.png", dpi=160)
    plt.close()
    
    # 2. Residual plot
    residuals = test_sample[TARGET_COL].values - preds
    plt.figure(figsize=(10, 4))
    plt.scatter(preds, residuals, alpha=0.5)
    plt.axhline(y=0, color='r', linestyle='--')
    plt.title("Residual Plot")
    plt.xlabel("Predicted CO")
    plt.ylabel("Residuals")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "02_residual_plot.png", dpi=160)
    plt.close()
    
    # 3. Feature importance (coefficients)
    coefficients = model.named_steps["regressor"].coef_
    plt.figure(figsize=(10, 6))
    plt.barh(API_FEATURES, coefficients)
    plt.title("Feature Importance (Linear Regression Coefficients)")
    plt.xlabel("Coefficient Value")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "03_feature_importance.png", dpi=160)
    plt.close()
    
    print("DONE: Training pipeline completed for Air Quality dataset!")
    print(f"Metrics: {json.dumps(metrics, indent=2)}")
    print("\nGenerated files:")
    print("- data/telemetry_clean.csv")
    print("- data/feature_dataset.csv")
    print("- models/air_quality_model.joblib")
    print("- outputs/metrics.json")
    print("- outputs/decision_log.csv")
    print("- outputs/figures/*.png")