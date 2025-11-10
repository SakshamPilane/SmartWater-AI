from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import joblib
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.preprocessing import StandardScaler
from database import fetch_query, execute_query
from distribution import router as distribution_router
from login import router as login_router, get_current_user  # ✅ JWT dependency
from dashboard import router as dashboard_router
from quality import router as quality_router

# ✅ NEW: Import public routes (no auth required)
from public_routes import public_router

# ====================================
# 🔹 Load Environment Variables
# ====================================
load_dotenv()
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
APP_VERSION = "2.5"

# ====================================
# 🔹 App Initialization
# ====================================
app = FastAPI(
    title="💧 Smart Water Management Backend API",
    version=APP_VERSION,
    description="FastAPI backend for SmartWater-AI — integrates municipal data, AI-based water quality prediction, and distribution efficiency analytics with secure JWT authentication."
)

# ====================================
# 🔹 CORS Setup
# ====================================
origins = [
    FRONTEND_URL,
    "http://127.0.0.1:3000",
    "http://localhost:3000",
    "http://192.168.1.4:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ====================================
# 🔹 Include Routers
# ====================================
# Public routes (NO authentication required)
app.include_router(public_router, prefix="/api", tags=["Public"])

# Authentication routes (public)
app.include_router(login_router, prefix="/api", tags=["Authentication"])

# Protected routes (secured with JWT)
if dashboard_router:
    app.include_router(
        dashboard_router,
        prefix="/api",
        tags=["Dashboard"],
        dependencies=[Depends(get_current_user)]
    )

app.include_router(
    quality_router,
    prefix="/api",
    tags=["Water Quality"],
    dependencies=[Depends(get_current_user)]
)

app.include_router(
    distribution_router,
    prefix="/api",
    tags=["Water Distribution"],
    dependencies=[Depends(get_current_user)]
)

# ====================================
# 🔹 Root Endpoint
# ====================================
@app.get("/")
def home():
    return {
        "message": "💧 SmartWater-AI Backend is running successfully and secured with JWT!",
        "version": APP_VERSION,
        "available_routes": [
            "/api/public-overall-stats  (🌍 public)",
            "/api/login  (🔓 public)",
            "/api/overall-stats  (🔐 protected)",
            "/api/predict-quality  (🔐 protected)",
            "/api/predict-distribution  (🔐 protected)",
            "/api/mc/{MC_Code}/trend  (🔐 protected)",
            "/api/mc/{MC_Code}/distribution-trend  (🔐 protected)"
        ]
    }

# ====================================
# 🔹 Load AI Models (on startup)
# ====================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")

try:
    regressor = joblib.load(os.path.join(MODELS_DIR, "wqi_regressor.pkl"))
    scaler = joblib.load(os.path.join(MODELS_DIR, "wqi_scaler.pkl"))
    anomaly_model = joblib.load(os.path.join(MODELS_DIR, "isolation_forest.pkl"))
    print(f"✅ AI Models loaded successfully from: {MODELS_DIR}")
except Exception as e:
    print(f"⚠️ Warning: Failed to load one or more AI models: {e}")
    regressor = scaler = anomaly_model = None

# ====================================
# 🔹 Model Update Function
# ====================================
def update_models():
    global regressor, scaler, anomaly_model

    if not all([regressor, scaler, anomaly_model]):
        print("⚠️ Models not initialized properly. Skipping retraining.")
        return

    records = fetch_query("SELECT * FROM water_quality_records WHERE Temperature IS NOT NULL")
    if not records:
        print("ℹ️ No records available for retraining.")
        return

    df = pd.DataFrame(records)
    required_cols = ["Temperature", "pH", "BOD", "Faecal_Coliform",
                     "Total_Coliform", "Nitrate", "Conductivity", "WQI", "Anomaly_Status"]
    df = df.dropna(subset=required_cols)
    if df.empty:
        print("⚠️ Dataset empty after cleaning. Retraining skipped.")
        return

    X = df[["Temperature", "pH", "BOD", "Faecal_Coliform",
            "Total_Coliform", "Nitrate", "Conductivity"]]
    y = df["WQI"].astype(float)

    try:
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        regressor.fit(X_scaled, y)
        anomaly_model = IsolationForest(n_estimators=200, contamination=0.02, random_state=42)
        anomaly_model.fit(X_scaled)

        os.makedirs(MODELS_DIR, exist_ok=True)
        joblib.dump(regressor, os.path.join(MODELS_DIR, "wqi_regressor.pkl"))
        joblib.dump(scaler, os.path.join(MODELS_DIR, "wqi_scaler.pkl"))
        joblib.dump(anomaly_model, os.path.join(MODELS_DIR, "isolation_forest.pkl"))

        execute_query("UPDATE water_quality_records SET Used_For_Training=1 WHERE Used_For_Training=0")
        print(f"✅ Models retrained successfully on {len(df)} records.")
    except Exception as e:
        print(f"❌ Error during model retraining: {e}")

# ====================================
# 🔹 Health Check / DB Test Route (protected)
# ====================================
@app.get("/api/db-test", tags=["System"])
def test_db(current_user: dict = Depends(get_current_user)):
    try:
        result = fetch_query("SELECT NOW() AS current_time")
        return {
            "status": "✅ Database connection successful",
            "timestamp": result[0]["current_time"],
            "user": current_user
        }
    except Exception as e:
        return {"status": "❌ Database connection failed", "error": str(e)}

# ====================================
# 🔹 Run Server
# ====================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
