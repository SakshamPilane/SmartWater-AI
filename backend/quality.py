import os
import joblib
import pandas as pd
import numpy as np
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends  # ✅ Added Depends for token validation
from pydantic import BaseModel
from database import execute_query, fetch_query
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest, RandomForestRegressor
from login import get_current_user  # ✅ Import JWT authentication method

router = APIRouter()

# ==============================
# 🔹 Input Schema
# ==============================
class WaterQualityInput(BaseModel):
    MC_Code: str
    Hub_ID: str
    Temperature_Min: float
    Temperature_Max: float
    pH_Min: float
    pH_Max: float
    Conductivity_Min: float
    Conductivity_Max: float
    BOD_Min: float
    BOD_Max: float
    Faecal_Coliform_Min: float
    Faecal_Coliform_Max: float
    Total_Coliform_Min: float
    Total_Coliform_Max: float
    Nitrate_N_Min: float
    Nitrate_N_Max: float

# ==============================
# 🔹 Load Models
# ==============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")

regressor = RandomForestRegressor(n_estimators=200, random_state=42)
scaler = StandardScaler()
anomaly_model = IsolationForest(n_estimators=200, contamination=0.02, random_state=42)

try:
    if os.path.exists(os.path.join(MODELS_DIR, "wqi_regressor.pkl")):
        regressor = joblib.load(os.path.join(MODELS_DIR, "wqi_regressor.pkl"))
    if os.path.exists(os.path.join(MODELS_DIR, "wqi_scaler.pkl")):
        scaler = joblib.load(os.path.join(MODELS_DIR, "wqi_scaler.pkl"))
    if os.path.exists(os.path.join(MODELS_DIR, "isolation_forest.pkl")):
        anomaly_model = joblib.load(os.path.join(MODELS_DIR, "isolation_forest.pkl"))
    print("✅ AI Models loaded successfully")
except Exception as e:
    print("❌ Error loading models, using defaults:", e)

# ==============================
# 🔹 Rule-based WQI Calculation
# ==============================
WEIGHTS = {
    "Temperature": 0.1,
    "pH": 0.2,
    "Conductivity": 0.1,
    "BOD": 0.2,
    "Faecal_Coliform": 0.2,
    "Total_Coliform": 0.1,
    "Nitrate_N": 0.1
}

STANDARDS = {
    'pH': 7,
    'BOD': 6,
    'Faecal_Coliform': 500,
    'Total_Coliform': 500,
    'Nitrate_N': 10,
    'Conductivity': 2000,
    'Temperature': 25
}

CAPS = {
    'pH': 14,
    'BOD': 50,
    'Faecal_Coliform': 2000,
    'Total_Coliform': 2000,
    'Nitrate_N': 50,
    'Conductivity': 100000,
    'Temperature': 50
}

# ==============================
# 🔹 Compute Rule-Based WQI (Utility)
# ==============================
def compute_rule_wqi(values: dict):
    """
    Calculates Water Quality Index (WQI) based on environmental parameters.
    This is a local utility function and does not require authentication.
    """
    for k in values:
        if k in CAPS:
            values[k] = min(values[k], CAPS[k])

    temp_score = max(0, 100 - abs(values['Temperature'] - STANDARDS['Temperature']) * 4)
    ph_score = max(0, 100 - abs(values['pH'] - STANDARDS['pH']) * 10)
    cond_score = max(0, 100 - values['Conductivity'] / 100)
    bod_score = max(0, 100 - values['BOD'] * 10)
    fc_score = max(0, 100 - values['Faecal_Coliform'] / 10)
    tc_score = max(0, 100 - values['Total_Coliform'] / 10)
    nitrate_score = max(0, 100 - values['Nitrate_N'] * 5)

    wqi = (
        temp_score * WEIGHTS['Temperature'] +
        ph_score * WEIGHTS['pH'] +
        cond_score * WEIGHTS['Conductivity'] +
        bod_score * WEIGHTS['BOD'] +
        fc_score * WEIGHTS['Faecal_Coliform'] +
        tc_score * WEIGHTS['Total_Coliform'] +
        nitrate_score * WEIGHTS['Nitrate_N']
    )
    return round(wqi, 2)

# ==============================
# 🔹 Categorize WQI (Utility Function)
# ==============================
def categorize_wqi(wqi: float):
    """
    Categorizes Water Quality Index (WQI) into qualitative levels.
    This is a local utility function — no authentication required.
    """
    if wqi >= 70:
        return "Good"
    elif wqi >= 50:
        return "Moderate"
    else:
        return "Poor"
    
# ==============================
# 🔹 Robust Incremental Model Update / Full Retrain
# ==============================
def update_models():
    """
    Retrains AI models (WQI regressor, scaler, anomaly detector) using latest water quality data.
    ⚙️ Internal backend utility — NOT exposed as an API route, so authentication is not applied here.
    """
    global regressor, scaler, anomaly_model

    # Fetch latest training data
    records = fetch_query("SELECT * FROM water_quality_records WHERE Temperature IS NOT NULL")
    if not records:
        return

    df = pd.DataFrame(records)
    essential_cols = [
        "Temperature", "pH", "BOD", "Faecal_Coliform",
        "Total_Coliform", "Nitrate", "Conductivity", "WQI", "Anomaly_Status"
    ]
    df = df.dropna(subset=essential_cols)
    if df.empty:
        return

    # Prepare data
    X = df[["Temperature", "pH", "BOD", "Faecal_Coliform",
            "Total_Coliform", "Nitrate", "Conductivity"]]
    y_reg = df["WQI"].astype(float)

    # Retrain models
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    regressor.fit(X_scaled, y_reg)
    anomaly_model = IsolationForest(n_estimators=200, contamination=0.02, random_state=42)
    anomaly_model.fit(X_scaled)

    # Save updated models
    os.makedirs(MODELS_DIR, exist_ok=True)
    joblib.dump(regressor, os.path.join(MODELS_DIR, "wqi_regressor.pkl"))
    joblib.dump(scaler, os.path.join(MODELS_DIR, "wqi_scaler.pkl"))
    joblib.dump(anomaly_model, os.path.join(MODELS_DIR, "isolation_forest.pkl"))

    # Mark records as used
    execute_query("UPDATE water_quality_records SET Used_For_Training=1 WHERE Used_For_Training=0")

# ==============================
# 🔹 POST: Predict + Store Hub Quality (final stable version)
# ==============================
from fastapi import Depends
from login import get_current_user  # ✅ import JWT validator

@router.post("/predict-quality")
def predict_water_quality(
    data: WaterQualityInput,
    current_user: dict = Depends(get_current_user)  # ✅ Require valid token
):
    """
    Predicts WQI using AI + Rule-based hybrid model, stores results,
    and provides natural-language interpretation and action guidance.
    🔐 Protected route: Requires JWT authentication.
    """

    try:
        # Step 1: Ensure models are loaded
        if regressor is None or scaler is None or anomaly_model is None:
            raise HTTPException(status_code=500, detail="AI Models not loaded properly")

        # Optional: Cross-check MC_Code from token vs payload
        if data.MC_Code != current_user["mc_code"]:
            raise HTTPException(status_code=403, detail="Unauthorized access for this MC_Code")

        # Step 2: Compute mean values between min/max
        features_dict = {
            "Temperature": (data.Temperature_Min + data.Temperature_Max) / 2,
            "pH": (data.pH_Min + data.pH_Max) / 2,
            "BOD": (data.BOD_Min + data.BOD_Max) / 2,
            "Faecal_Coliform": (data.Faecal_Coliform_Min + data.Faecal_Coliform_Max) / 2,
            "Total_Coliform": (data.Total_Coliform_Min + data.Total_Coliform_Max) / 2,
            "Nitrate_N": (data.Nitrate_N_Min + data.Nitrate_N_Max) / 2,
            "Conductivity": (data.Conductivity_Min + data.Conductivity_Max) / 2
        }

        # Step 3: Rename nitrate for ML model compatibility
        ml_features = {
            "Temperature": features_dict["Temperature"],
            "pH": features_dict["pH"],
            "BOD": features_dict["BOD"],
            "Faecal_Coliform": features_dict["Faecal_Coliform"],
            "Total_Coliform": features_dict["Total_Coliform"],
            "Nitrate": features_dict["Nitrate_N"],
            "Conductivity": features_dict["Conductivity"]
        }

        # Step 4: Prepare dataframe for prediction
        features = pd.DataFrame([ml_features], columns=[
            "Temperature", "pH", "BOD", "Faecal_Coliform", "Total_Coliform", "Nitrate", "Conductivity"
        ])
        scaled = scaler.transform(features)
        ml_wqi = float(regressor.predict(scaled)[0])

        # Step 5: Compute rule-based WQI
        rule_wqi = compute_rule_wqi(features_dict)

        # Step 6: Combine both (70% ML + 30% Rule)
        predicted_wqi = round((ml_wqi * 0.7 + rule_wqi * 0.3), 2)

        # Step 7: Categorize the WQI
        if predicted_wqi >= 80:
            predicted_category = "Excellent"
            emoji = "💧"
            interpretation = "Water quality is excellent — clean, safe, and fit for all domestic and industrial uses."
            action = "Continue regular monitoring. Maintain current supply and sanitation standards."
        elif predicted_wqi >= 65:
            predicted_category = "Good"
            emoji = "✅"
            interpretation = "Water quality is good — generally safe for domestic use. Occasional treatment may be required."
            action = "Recommend monthly bacterial checks and quarterly chemical sampling."
        elif predicted_wqi >= 50:
            predicted_category = "Moderate"
            emoji = "⚠️"
            interpretation = "Water quality is moderate — safe for limited domestic use but not advisable for direct consumption."
            action = "Increase monitoring frequency. Consider mild chlorination or filtration improvement."
        elif predicted_wqi >= 30:
            predicted_category = "Poor"
            emoji = "🚨"
            interpretation = "Water quality is poor — indicates contamination risk, unsafe for direct use."
            action = "Immediate water treatment required. Investigate contamination sources."
        else:
            predicted_category = "Very Poor"
            emoji = "☠️"
            interpretation = "Water is severely polluted — unsafe for any use without purification."
            action = "Urgent intervention: conduct microbial testing and suspend direct water supply."

        # Step 8: Safety auto downgrade for critical contamination
        if (
            features_dict["pH"] < 5.5
            or features_dict["BOD"] > 20
            or features_dict["Faecal_Coliform"] > 5000
        ):
            predicted_category = "Very Poor"
            predicted_wqi = min(predicted_wqi, 35)
            emoji = "☠️"
            interpretation = "Severe contamination detected — unsafe water."
            action = "Immediate isolation and thorough water treatment recommended."

        # Step 9: Detect anomalies
        anomaly_status = "Anomaly Detected" if anomaly_model.predict(scaled)[0] == -1 else "Normal"
        if anomaly_status == "Anomaly Detected":
            emoji = "⚠️"
            action += " Possible sensor or data anomaly — recheck readings."

        # Step 10: Save prediction in database
        insert_query = """
            INSERT INTO water_quality_records (
                MC_Code, Hub_ID, Temperature, pH, BOD, Faecal_Coliform, Total_Coliform,
                Nitrate, Conductivity, WQI, Category, Anomaly_Status, Created_At, Used_For_Training
            ) VALUES (
                :MC_Code, :Hub_ID, :Temperature, :pH, :BOD, :Faecal_Coliform, :Total_Coliform,
                :Nitrate, :Conductivity, :WQI, :Category, :Anomaly_Status, :Created_At, 0
            )
        """

        execute_query(insert_query, {
            "MC_Code": data.MC_Code,
            "Hub_ID": data.Hub_ID,
            "Temperature": features_dict["Temperature"],
            "pH": features_dict["pH"],
            "BOD": features_dict["BOD"],
            "Faecal_Coliform": features_dict["Faecal_Coliform"],
            "Total_Coliform": features_dict["Total_Coliform"],
            "Nitrate": features_dict["Nitrate_N"],
            "Conductivity": features_dict["Conductivity"],
            "WQI": predicted_wqi,
            "Category": predicted_category,
            "Anomaly_Status": anomaly_status,
            "Created_At": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        # Step 11: Retrain models asynchronously
        update_models()

        # Step 12: Human-style AI output
        return {
            "Hub_ID": data.Hub_ID,
            "Final_WQI": predicted_wqi,
            "Category": predicted_category,
            "Emoji_Status": emoji,
            "Anomaly_Status": anomaly_status,
            "Interpretation": interpretation,
            "Recommended_Action": action,
            "Details": {
                "ML_WQI": round(ml_wqi, 2),
                "Rule_WQI": round(rule_wqi, 2),
                "Hybrid_Model": "70% AI + 30% Rule-based",
                "Input_Features": features_dict
            },
            "AI_Summary": f"{emoji} The AI predicts a WQI of {predicted_wqi} ({predicted_category}). {interpretation} Recommended action: {action}",
            "Message": f"✅ Record saved successfully for Hub {data.Hub_ID}.",
            "Authenticated_User": current_user["username"]  # ✅ helpful for audit logging
        }

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"Prediction failed: {str(ve)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error during prediction: {str(e)}")

# ==============================
# 🔹 GET: List all Hubs for an MC
# ==============================
from fastapi import Depends
from login import get_current_user  # ✅ Import JWT validator

@router.get("/mc/{mc_code}/hubs")
def get_hubs(
    mc_code: str,
    current_user: dict = Depends(get_current_user)  # ✅ Require authentication
):
    """
    Fetches all water supply hubs mapped to a given Municipal Corporation (MC).
    🔐 Protected route: Requires JWT authentication.
    """

    # ✅ Verify the logged-in user's MC matches the requested MC
    if mc_code != current_user["mc_code"]:
        raise HTTPException(status_code=403, detail="Unauthorized access to another MC’s data.")

    query = """
        SELECT h.Hub_ID, h.Hub_Name
        FROM mc_hub_mapping m
        JOIN hub_table h ON m.Hub_ID = h.Hub_ID
        WHERE m.MC_Code = :mc_code
        ORDER BY h.Hub_Name ASC
    """
    hubs = fetch_query(query, {"mc_code": mc_code})

    if not hubs:
        raise HTTPException(status_code=404, detail="No hubs found for this MC.")

    return {
        "MC_Code": mc_code,
        "Total_Hubs": len(hubs),
        "Hubs": hubs,
        "Message": "✅ Hubs fetched successfully",
        "Authenticated_User": current_user["username"]  # optional, for logs/debugging
    }

# ==============================
# 🔹 GET: All Quality Records for an MC (🔐 Protected)
# ==============================
from fastapi import Depends
from login import get_current_user  # ✅ Import token validator

@router.get("/mc/{mc_code}/quality-records")
def get_quality_records(
    mc_code: str,
    hub_id: str = None,
    current_user: dict = Depends(get_current_user)  # ✅ Require JWT authentication
):
    """
    Fetch all stored water quality records for a given Municipal Corporation (MC).
    Optionally filter by Hub ID.
    🔐 Protected route: Requires valid JWT token and matching MC_Code.
    """

    # ✅ Enforce MC authorization
    if mc_code != current_user["mc_code"]:
        raise HTTPException(status_code=403, detail="Unauthorized access to another MC’s data.")

    query = """
        SELECT * FROM water_quality_records
        WHERE MC_Code = :mc_code
    """
    params = {"mc_code": mc_code}

    if hub_id:
        query += " AND Hub_ID = :hub_id"
        params["hub_id"] = hub_id

    query += " ORDER BY Created_At DESC"

    records = fetch_query(query, params)

    if not records:
        raise HTTPException(status_code=404, detail="No quality records found for this MC.")

    return {
        "MC_Code": mc_code,
        "Hub_Filter": hub_id if hub_id else "All Hubs",
        "Total_Records": len(records),
        "Records": records,
        "Message": "✅ Quality records fetched successfully",
        "Authenticated_User": current_user["username"]  # for audit/logging visibility
    }

# ==============================
# 🔹 GET: Trend Summary per MC / Hub (🔐 Authenticated)
# ==============================
from fastapi import Depends
from login import get_current_user  # ✅ Import authentication dependency

@router.get("/mc/{MC_Code}/trend")
def get_quality_trend(
    MC_Code: str,
    Hub_ID: str = None,
    current_user: dict = Depends(get_current_user)  # ✅ Require valid JWT
):
    """
    Generate a trend summary of Water Quality Index (WQI) over time for a given MC or specific hub.
    🔐 Protected route: Requires authentication & MC validation.
    """

    # ✅ Ensure user is accessing their own municipal data
    if MC_Code != current_user["mc_code"]:
        raise HTTPException(status_code=403, detail="Unauthorized access to another MC’s data.")

    query = """
        SELECT Hub_ID, WQI, Anomaly_Status, Created_At
        FROM water_quality_records
        WHERE MC_Code = :MC_Code
    """
    params = {"MC_Code": MC_Code}
    if Hub_ID:
        query += " AND Hub_ID = :Hub_ID"
        params["Hub_ID"] = Hub_ID
    query += " ORDER BY Created_At ASC"

    records = fetch_query(query, params)
    if not records:
        raise HTTPException(status_code=404, detail="No records found for trend analysis.")

    # Convert to DataFrame
    df = pd.DataFrame(records)
    df["Created_At"] = pd.to_datetime(df["Created_At"], errors="coerce")

    # Drop invalid rows
    df = df.dropna(subset=["Created_At", "WQI"])

    # Ensure numeric values
    df["WQI"] = pd.to_numeric(df["WQI"], errors="coerce")
    df = df.replace([np.inf, -np.inf], np.nan).fillna(0)

    # Build aggregated trend summary safely
    trend_summary = (
        df.groupby("Hub_ID", group_keys=False)
        .apply(lambda x: {
            "Total_Records": int(len(x)),
            "Average_WQI": round(float(x["WQI"].mean()), 2),
            "Anomaly_Count": int((x["Anomaly_Status"] == "Anomaly Detected").sum()),
            "Records": json_safe_records(x)
        })
        .to_dict()
    )

    return {
        "MC_Code": MC_Code,
        "Hub_Filter": Hub_ID if Hub_ID else "All Hubs",
        "Trend_Summary": trend_summary,
        "Message": "✅ Trend summary generated successfully",
        "Authenticated_User": current_user["username"]  # for audit/debug
    }


# Helper to make JSON-safe records
def json_safe_records(df: pd.DataFrame):
    records = df.to_dict(orient="records")
    safe = []
    for r in records:
        clean = {}
        for k, v in r.items():
            if isinstance(v, float):
                if np.isnan(v) or np.isinf(v):
                    clean[k] = None
                else:
                    clean[k] = round(v, 3)
            elif isinstance(v, (np.int64, np.int32)):
                clean[k] = int(v)
            else:
                clean[k] = v
        safe.append(clean)
    return safe

# ==============================
# 🔹 GET: Anomaly Summary per MC / Hub (🔐 Authenticated)
# ==============================
from fastapi import Depends
from login import get_current_user  # ✅ Import JWT validation helper

@router.get("/mc/{MC_Code}/anomalies")
def get_anomaly_summary(
    MC_Code: str,
    Hub_ID: str = None,
    current_user: dict = Depends(get_current_user)  # ✅ Require JWT authentication
):
    """
    Returns a summary of all detected anomalies for a given Municipal Corporation (MC) or specific Hub.
    🔐 Protected route: Only accessible to authenticated municipal users.
    """

    # ✅ Validate municipal access
    if MC_Code != current_user["mc_code"]:
        raise HTTPException(status_code=403, detail="Unauthorized access to another MC’s data.")

    query = """
        SELECT Hub_ID, WQI, Anomaly_Status, Created_At
        FROM water_quality_records
        WHERE MC_Code = :MC_Code
          AND Anomaly_Status = 'Anomaly Detected'
    """
    params = {"MC_Code": MC_Code}

    if Hub_ID:
        query += " AND Hub_ID = :Hub_ID"
        params["Hub_ID"] = Hub_ID

    query += " ORDER BY Created_At DESC"

    records = fetch_query(query, params)

    total_anomalies = len(records)
    message = "✅ No anomalies detected" if total_anomalies == 0 else f"⚠️ {total_anomalies} anomalies detected"

    return {
        "MC_Code": MC_Code,
        "Hub_Filter": Hub_ID if Hub_ID else "All Hubs",
        "Total_Anomalies": total_anomalies,
        "Records": records,
        "Message": message,
        "Authenticated_User": current_user["username"]  # for debugging/logging
    }

# ==============================
# 🔹 GET: Yearly / Hub Trend Summary with Trend Direction + Yearly Delta (🔐 Authenticated)
# ==============================
from fastapi import Depends
from login import get_current_user  # ✅ Import token verification function

@router.get("/mc/{MC_Code}/yearly-trend")
def get_yearly_trend(
    MC_Code: str,
    Hub_ID: str = None,
    current_user: dict = Depends(get_current_user)  # ✅ Require JWT authentication
):
    """
    Generate yearly trend analysis for each Hub or entire Municipal Corporation (MC).
    Includes WQI averages, yearly deltas, and trend direction.
    🔐 Protected route: Accessible only by authorized municipal users.
    """

    # ✅ Enforce access control
    if MC_Code != current_user["mc_code"]:
        raise HTTPException(status_code=403, detail="Unauthorized access to another MC’s data.")

    query = """
        SELECT Hub_ID, WQI, Anomaly_Status, Created_At
        FROM water_quality_records
        WHERE MC_Code = :MC_Code
    """
    params = {"MC_Code": MC_Code}

    if Hub_ID:
        query += " AND Hub_ID = :Hub_ID"
        params["Hub_ID"] = Hub_ID

    query += " ORDER BY Created_At ASC"
    records = fetch_query(query, params)

    if not records:
        return {
            "MC_Code": MC_Code,
            "Hub_Filter": Hub_ID if Hub_ID else "All Hubs",
            "Yearly_Trend_Summary": {},
            "Message": "✅ No records found for yearly trend.",
            "Authenticated_User": current_user["username"]  # For traceability
        }

    df = pd.DataFrame(records)
    df["Created_At"] = pd.to_datetime(df["Created_At"])
    df["Year"] = df["Created_At"].dt.year

    summary = {}
    hubs = df["Hub_ID"].unique()

    for hub in hubs:
        hub_summary = {}
        prev_avg_wqi = None
        for year in range(2018, pd.Timestamp.now().year + 1):
            year_group = df[(df["Hub_ID"] == hub) & (df["Year"] == year)]
            if not year_group.empty:
                avg_wqi = float(year_group["WQI"].mean())
                max_wqi = float(year_group["WQI"].max())
                min_wqi = float(year_group["WQI"].min())
                anomaly_count = int((year_group["Anomaly_Status"] == "Anomaly Detected").sum())
                total_records = len(year_group)

                # Determine trend
                if prev_avg_wqi is None:
                    trend = "N/A"
                    delta = "N/A"
                else:
                    delta_val = round(avg_wqi - prev_avg_wqi, 2)
                    delta = delta_val
                    if delta_val > 1.0:
                        trend = "Improving"
                    elif delta_val < -1.0:
                        trend = "Degrading"
                    else:
                        trend = "Stable"

                prev_avg_wqi = avg_wqi
            else:
                avg_wqi = max_wqi = min_wqi = 0.0
                anomaly_count = total_records = 0
                trend = "N/A"
                delta = "N/A"

            hub_summary[str(year)] = {
                "Average_WQI": avg_wqi,
                "Max_WQI": max_wqi,
                "Min_WQI": min_wqi,
                "Total_Records": total_records,
                "Anomaly_Count": anomaly_count,
                "Trend": trend,
                "Yearly_Delta": delta
            }
        summary[hub] = hub_summary

    return {
        "MC_Code": MC_Code,
        "Hub_Filter": Hub_ID if Hub_ID else "All Hubs",
        "Yearly_Trend_Summary": summary,
        "Message": "✅ Yearly trend summary with trend direction and yearly delta generated",
        "Authenticated_User": current_user["username"]
    }