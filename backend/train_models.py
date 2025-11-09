# train_models.py
import os
import joblib
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.preprocessing import StandardScaler
from database import fetch_query

# ------------------------------
# 🔹 Config
# ------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")
os.makedirs(MODELS_DIR, exist_ok=True)

# ------------------------------
# 🔹 Fetch water quality training data
# ------------------------------
query = """
SELECT Temperature, pH, BOD, Faecal_Coliform, Total_Coliform, Nitrate, Conductivity,
       Rule_WQI AS WQI, Anomaly_Status
FROM water_quality_training
"""
df = pd.DataFrame(fetch_query(query, {}))
print(f"ℹ️ Fetched {len(df)} records from database.")

# ------------------------------
# 🔹 Clean dataset
# ------------------------------
required_cols = ["WQI", "Temperature","pH","BOD",
                 "Faecal_Coliform","Total_Coliform","Nitrate","Conductivity"]

# Drop rows with missing values
df = df.dropna(subset=required_cols)
print(f"ℹ️ {len(df)} records remaining after dropping rows with NaNs.")

if df.empty:
    print("❌ No valid records to train. Populate historical data first.")
    exit()

features = ["Temperature","pH","BOD","Faecal_Coliform","Total_Coliform","Nitrate","Conductivity"]
X = df[features]
y_reg = df["WQI"].astype(float)
y_anomaly = df["Anomaly_Status"].apply(lambda x: -1 if x=="Anomaly Detected" else 1)

# ------------------------------
# 🔹 Scale features
# ------------------------------
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# ------------------------------
# 🔹 Train Regressor
# ------------------------------
print("⏳ Training Regressor for WQI...")
regressor = RandomForestRegressor(n_estimators=200, random_state=42)
regressor.fit(X_scaled, y_reg)
print("✅ Regressor trained. R^2:", round(regressor.score(X_scaled, y_reg),3))

# ------------------------------
# 🔹 Train Anomaly Model
# ------------------------------
print("⏳ Training Isolation Forest for anomalies...")
anomaly_model = IsolationForest(n_estimators=200, contamination=0.02, random_state=42)
anomaly_model.fit(X_scaled)
print("✅ Anomaly model trained.")

# ------------------------------
# 🔹 Save models
# ------------------------------
joblib.dump(regressor, os.path.join(MODELS_DIR,"wqi_regressor.pkl"))
joblib.dump(scaler, os.path.join(MODELS_DIR,"wqi_scaler.pkl"))
joblib.dump(anomaly_model, os.path.join(MODELS_DIR,"isolation_forest.pkl"))
print(f"💾 All models saved to {MODELS_DIR}")

# ------------------------------
# 🔹 Optional: Compare AI vs Rule-based WQI
# ------------------------------
try:
    df["AI_WQI"] = regressor.predict(X_scaled)

    # Calculate mean absolute error for WQI
    mae_wqi = np.mean(np.abs(df["WQI"] - df["AI_WQI"]))
    print(f"📊 Mean Absolute Error (WQI): {mae_wqi:.2f}")
except Exception as e:
    print(f"⚠️ Could not compare AI vs Rule-based WQI: {e}")
