import os
import joblib
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.preprocessing import StandardScaler
from database import fetch_query
from datetime import datetime

# ==================================================
# 🔹 Configuration
# ==================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")
os.makedirs(MODELS_DIR, exist_ok=True)

MODEL_VERSION = datetime.now().strftime("%Y%m%d_%H%M")
print(f"🚀 Training Session Started — Version: {MODEL_VERSION}")

# ==================================================
# 🔹 Fetch Training Data
# ==================================================
query = """
SELECT Temperature, pH, BOD, Faecal_Coliform, Total_Coliform, Nitrate, Conductivity,
       Rule_WQI AS WQI, Anomaly_Status
FROM water_quality_training
"""
try:
    df = pd.DataFrame(fetch_query(query, {}))
except Exception as e:
    print(f"❌ Database error while fetching data: {e}")
    exit(1)

print(f"ℹ️ Fetched {len(df)} records from database.")

# ==================================================
# 🔹 Data Cleaning
# ==================================================
required_cols = ["WQI", "Temperature", "pH", "BOD", "Faecal_Coliform",
                 "Total_Coliform", "Nitrate", "Conductivity"]

df = df.dropna(subset=required_cols)
print(f"ℹ️ {len(df)} records remaining after dropping rows with missing values.")

if df.empty:
    print("❌ No valid data found for training. Please populate historical data first.")
    exit(1)

# Ensure correct data types
for col in required_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Drop invalid (non-numeric) rows
df = df.dropna(subset=required_cols)
if df.empty:
    print("❌ All records invalid after type conversion.")
    exit(1)

features = ["Temperature", "pH", "BOD", "Faecal_Coliform", "Total_Coliform", "Nitrate", "Conductivity"]
X = df[features]
y_reg = df["WQI"].astype(float)
y_anomaly = df["Anomaly_Status"].apply(lambda x: -1 if x == "Anomaly Detected" else 1)

# ==================================================
# 🔹 Feature Scaling
# ==================================================
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# ==================================================
# 🔹 Train Models
# ==================================================
print("⏳ Training RandomForest Regressor for WQI...")
regressor = RandomForestRegressor(n_estimators=200, random_state=42)
regressor.fit(X_scaled, y_reg)
r2_score = round(regressor.score(X_scaled, y_reg), 3)
print(f"✅ Regressor trained successfully (R² = {r2_score})")

print("⏳ Training Isolation Forest for anomaly detection...")
anomaly_model = IsolationForest(n_estimators=200, contamination=0.02, random_state=42)
anomaly_model.fit(X_scaled)
print("✅ Anomaly detection model trained successfully.")

# ==================================================
# 🔹 Save Models
# ==================================================
try:
    joblib.dump(regressor, os.path.join(MODELS_DIR, f"wqi_regressor.pkl"))
    joblib.dump(scaler, os.path.join(MODELS_DIR, f"wqi_scaler.pkl"))
    joblib.dump(anomaly_model, os.path.join(MODELS_DIR, f"isolation_forest.pkl"))

    # Optional versioned backups
    joblib.dump(regressor, os.path.join(MODELS_DIR, f"wqi_regressor_{MODEL_VERSION}.pkl"))
    joblib.dump(anomaly_model, os.path.join(MODELS_DIR, f"isolation_forest_{MODEL_VERSION}.pkl"))

    print(f"💾 Models saved successfully in {MODELS_DIR}")
except Exception as e:
    print(f"❌ Error saving models: {e}")
    exit(1)

# ==================================================
# 🔹 Model Evaluation — AI vs Rule-based WQI
# ==================================================
try:
    df["AI_WQI"] = regressor.predict(X_scaled)
    mae_wqi = np.mean(np.abs(df["WQI"] - df["AI_WQI"]))
    print(f"📊 Mean Absolute Error (WQI): {mae_wqi:.2f}")
    print("✅ Model evaluation complete.")
except Exception as e:
    print(f"⚠️ Skipped evaluation — Error comparing AI vs Rule-based WQI: {e}")

print(f"🏁 Training Completed — Model Version: {MODEL_VERSION}")
