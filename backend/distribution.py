import os
import joblib
import pandas as pd
import numpy as np
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from functools import lru_cache
from database import execute_query, fetch_query

router = APIRouter()

# ===================================================
# 🔹 Load AI Models
# ===================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "distribution_models")

try:
    eff_model = joblib.load(os.path.join(MODELS_DIR, "water_efficiency_regression_model.pkl"))
    risk_model = joblib.load(os.path.join(MODELS_DIR, "water_criticality_classifier.pkl"))
    print("✅ Distribution AI models loaded successfully")
except Exception as e:
    eff_model = risk_model = None
    print("❌ Error loading distribution models:", e)


# ===================================================
# 🔹 Input Schema
# ===================================================
class DistributionInput(BaseModel):
    MC_Code: str
    Hub_ID: str
    Total_Demand_MLD: float
    Current_Supply_MLD: float
    Population: int


# ===================================================
# 🔹 Utility: Smart AI Simulation Function
# ===================================================
def simulate_distribution(demand, supply, population):
    deficit = demand - supply
    efficiency = (supply / demand) * 100
    per_capita = (supply * 1000000) / (population * 1000)  # LPCD

    X_new = pd.DataFrame([{
        "Population": population,
        "Total_Demand_MLD": demand,
        "Current_Supply_MLD": supply,
        "Deficit_MLD": deficit,
        "PerCapita_LPCD": per_capita
    }])

    eff_pred = float(eff_model.predict(X_new)[0])
    risk_pred = int(risk_model.predict(X_new)[0])

    status = "⚠️ Critical" if risk_pred == 1 else "✅ Stable"
    action = (
        "Increase pumping / reduce non-revenue water"
        if eff_pred < 70
        else "Implement rotational supply or leakage audit"
        if risk_pred == 1
        else "Maintain normal operation"
    )

    return {
        "Predicted_Supply_Efficiency": round(eff_pred, 2),
        "Critical_Risk": bool(risk_pred),
        "Status": status,
        "Recommended_Action": action,
        "Deficit_MLD": round(deficit, 2),
        "PerCapita_LPCD": round(per_capita, 2)
    }

# ===================================================
# 🔹 POST: Predict & Store Distribution AI (Human-AI enhanced)
# ===================================================
@router.post("/predict-distribution")
def predict_distribution(data: DistributionInput):
    """
    AI-enhanced endpoint that predicts water distribution efficiency and risk level.
    Returns deep insights with human-like interpretation and actionable advice.
    """

    if not all([eff_model, risk_model]):
        raise HTTPException(status_code=500, detail="Distribution AI models not loaded properly")

    try:
        # Step 1️⃣: Calculate AI prediction
        result = simulate_distribution(
            demand=data.Total_Demand_MLD,
            supply=data.Current_Supply_MLD,
            population=data.Population
        )

        efficiency = result["Predicted_Supply_Efficiency"]
        deficit = result["Deficit_MLD"]
        per_capita = result["PerCapita_LPCD"]
        critical = result["Critical_Risk"]

        # Step 2️⃣: Interpret the AI output
        if efficiency >= 85:
            performance = "Excellent"
            emoji = "💧"
            interpretation = (
                f"Supply system is performing excellently with {efficiency}% efficiency. "
                "Water distribution is balanced and sustainable at current levels."
            )
            advice = "Continue current operation. Perform preventive maintenance bi-monthly."
        elif efficiency >= 70:
            performance = "Good"
            emoji = "✅"
            interpretation = (
                f"Efficiency is healthy at {efficiency}%. System is reliable but can be optimized further."
            )
            advice = "Monitor consumption growth. Conduct a quarterly leakage audit."
        elif efficiency >= 55:
            performance = "Moderate"
            emoji = "⚠️"
            interpretation = (
                f"Efficiency at {efficiency}% suggests strain on supply or losses due to leakage. "
                f"Deficit of {deficit} MLD may lead to periodic shortages."
            )
            advice = "Optimize pumping schedules, fix leaks, and assess non-revenue water zones."
        elif efficiency >= 40:
            performance = "Poor"
            emoji = "🚨"
            interpretation = (
                f"Low efficiency ({efficiency}%) indicates critical imbalance between demand and supply. "
                f"Shortfall of {deficit} MLD affecting per capita supply ({per_capita} LPCD)."
            )
            advice = "Prioritize network repair and pressure zoning. Consider tanker support or staggered supply."
        else:
            performance = "Critical"
            emoji = "☠️"
            interpretation = (
                f"Severe inefficiency detected ({efficiency}%). Water crisis likely. "
                f"Supply deficit of {deficit} MLD has created emergency conditions."
            )
            advice = (
                "Activate emergency protocols. Reduce non-revenue water, initiate alternate supply routes, "
                "and coordinate with municipal crisis teams immediately."
            )

        # Step 3️⃣: Risk interpretation
        if critical:
            risk_label = "⚠️ Critical Risk"
            advice += " AI indicates critical distribution risk — immediate field inspection advised."
        else:
            risk_label = "✅ Stable"
            advice += " Maintain current flow and monitoring routines."

        # Step 4️⃣: Assign grade + commentary
        if efficiency >= 85:
            grade = "A (Excellent)"
        elif efficiency >= 70:
            grade = "B (Good)"
        elif efficiency >= 55:
            grade = "C (Moderate)"
        elif efficiency >= 40:
            grade = "D (Poor)"
        else:
            grade = "E (Critical)"

        commentary = (
            f"{emoji} Hub {data.Hub_ID} operates at {efficiency}% efficiency ({grade}). "
            f"{interpretation} Recommended next action: {advice}"
        )

        # Step 5️⃣: Save results in database
        insert_query = """
            INSERT INTO water_distribution_records (
                MC_Code, Hub_ID, Total_Demand_MLD, Current_Supply_MLD, Population,
                Deficit_MLD, PerCapita_LPCD, Predicted_Supply_Efficiency, Critical_Risk,
                Recommended_Action, Created_At
            ) VALUES (
                :MC_Code, :Hub_ID, :Total_Demand_MLD, :Current_Supply_MLD, :Population,
                :Deficit_MLD, :PerCapita_LPCD, :Predicted_Supply_Efficiency, :Critical_Risk,
                :Recommended_Action, :Created_At
            )
        """

        execute_query(insert_query, {
            "MC_Code": data.MC_Code,
            "Hub_ID": data.Hub_ID,
            "Total_Demand_MLD": data.Total_Demand_MLD,
            "Current_Supply_MLD": data.Current_Supply_MLD,
            "Population": data.Population,
            "Deficit_MLD": result["Deficit_MLD"],
            "PerCapita_LPCD": result["PerCapita_LPCD"],
            "Predicted_Supply_Efficiency": result["Predicted_Supply_Efficiency"],
            "Critical_Risk": int(result["Critical_Risk"]),
            "Recommended_Action": advice,
            "Created_At": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        # Step 6️⃣: Return full AI-style output
        return {
            "MC_Code": data.MC_Code,
            "Hub_ID": data.Hub_ID,
            "Final_Efficiency": efficiency,
            "Performance_Grade": grade,
            "Status": risk_label,
            "Emoji_Status": emoji,
            "Critical_Risk": critical,
            "Deficit_MLD": deficit,
            "PerCapita_LPCD": per_capita,
            "Interpretation": interpretation,
            "AI_Commentary": commentary,
            "Recommended_Action": advice,
            "Summary": f"{emoji} {performance} performance with {efficiency}% efficiency. {interpretation}",
            "Message": f"✅ AI-enhanced distribution prediction saved for Hub {data.Hub_ID}"
        }

    except Exception as e:
        if "no such table" in str(e).lower():
            raise HTTPException(status_code=500, detail="Distribution table missing — please initialize schema and rerun.")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")
    
# ===================================================
# 🔹 Cached Query Wrapper (hashable-safe)
# ===================================================
@lru_cache(maxsize=128)
def cached_fetch(query: str, mc_code: str):
    """
    Cached version of fetch_query() for single-MC queries.
    Keeps mc_code as hashable (string) and rebuilds params internally.
    """
    params = {"mc_code": mc_code}
    return fetch_query(query, params)

# ===================================================
# 🔹 GET: AI Summary per MC
# ===================================================
@router.get("/mc/{mc_code}/distribution-summary")
def get_distribution_summary(mc_code: str):
    query = """
        SELECT 
            AVG(Predicted_Supply_Efficiency) AS Avg_Efficiency,
            COUNT(DISTINCT CASE WHEN Critical_Risk = 1 THEN Hub_ID END) AS Total_Critical_Hubs,
            COUNT(*) AS Total_Records,
            SUM(Deficit_MLD) AS Total_Deficit
        FROM water_distribution_records
        WHERE MC_Code = :mc_code
    """
    try:
        result = cached_fetch(query, mc_code)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    if not result or not result[0]["Total_Records"]:
        raise HTTPException(status_code=404, detail="No summary data available.")

    data = result[0]
    return {
        "MC_Code": mc_code,
        "Average_Supply_Efficiency": round(data["Avg_Efficiency"], 2) if data["Avg_Efficiency"] else 0,
        "Total_Critical_Hubs": int(data["Total_Critical_Hubs"]) if data["Total_Critical_Hubs"] else 0,
        "Total_Records": int(data["Total_Records"]),
        "Total_Deficit_MLD": round(data["Total_Deficit"], 2) if data["Total_Deficit"] else 0,
        "Message": "✅ Distribution summary calculated successfully"
    }

# ===================================================
# 🔹 GET: Distribution Trend per Hub / MC (Warning-Free)
# ===================================================
@router.get("/mc/{mc_code}/distribution-trend")
def get_distribution_trend(mc_code: str, hub_id: str = None):
    query = """
        SELECT Hub_ID, Predicted_Supply_Efficiency, Critical_Risk, Created_At
        FROM water_distribution_records
        WHERE MC_Code = :mc_code
    """
    params = {"mc_code": mc_code}
    if hub_id:
        query += " AND Hub_ID = :hub_id"
        params["hub_id"] = hub_id
    query += " ORDER BY Created_At ASC"

    try:
        records = fetch_query(query, params)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    if not records:
        raise HTTPException(status_code=404, detail="No distribution records found for trend analysis.")

    df = pd.DataFrame(records)
    df["Created_At"] = pd.to_datetime(df["Created_At"])

    # ✅ Fixed FutureWarning: exclude grouping column in .apply()
    trend_summary = (
        df.groupby("Hub_ID", group_keys=False)
        .apply(lambda x: {
            "Total_Records": len(x),
            "Average_Efficiency": round(x["Predicted_Supply_Efficiency"].mean(), 2),
            "Critical_Count": int(x["Critical_Risk"].sum()),
            "Records": x.to_dict(orient="records")
        })
        .to_dict()
    )

    return {
        "MC_Code": mc_code,
        "Hub_Filter": hub_id if hub_id else "All Hubs",
        "Trend_Summary": trend_summary,
        "Message": "✅ Distribution trend summary generated"
    }

# ===================================================
# 🔹 GET: Critical Risk Summary (Fixed Cached Call)
# ===================================================
@router.get("/mc/{mc_code}/critical-summary")
def get_critical_summary(mc_code: str):
    query = """
        SELECT Hub_ID, Predicted_Supply_Efficiency, Critical_Risk, Recommended_Action, Created_At
        FROM water_distribution_records
        WHERE MC_Code = :mc_code
          AND Critical_Risk = 1
        ORDER BY Created_At DESC
    """
    try:
        result = cached_fetch(query, mc_code)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    total = len(result)
    return {
        "MC_Code": mc_code,
        "Total_Critical_Instances": total,
        "Records": result,
        "Message": "✅ No critical risk hubs detected" if total == 0 else f"⚠️ {total} critical risk events recorded"
    }

# ===================================================
# 🔹 GET: Latest Distribution Snapshot (for dashboard)
# ===================================================
@router.get("/mc/{mc_code}/distribution-latest")
def get_latest_distribution(mc_code: str):
    query = """
        SELECT Hub_ID, Predicted_Supply_Efficiency, Critical_Risk, Recommended_Action, Created_At
        FROM water_distribution_records
        WHERE MC_Code = :mc_code
          AND Created_At = (
              SELECT MAX(Created_At) FROM water_distribution_records WHERE MC_Code = :mc_code
          )
    """
    result = fetch_query(query, {"mc_code": mc_code})
    if not result:
        raise HTTPException(status_code=404, detail="No recent distribution records found for this MC.")
    return {
        "MC_Code": mc_code,
        "Latest_Records": result,
        "Message": "✅ Latest distribution data fetched successfully"
    }

# ===================================================
# 🔹 GET: Yearly Trend with Direction + Efficiency Delta (AI Enhanced, JSON-Safe + Accurate)
# ===================================================
@router.get("/mc/{mc_code}/yearly-distribution-trend")
def get_yearly_distribution_trend(mc_code: str, hub_id: str = None):
    query = """
        SELECT Hub_ID, Predicted_Supply_Efficiency, Critical_Risk, Created_At
        FROM water_distribution_records
        WHERE MC_Code = :mc_code
    """
    params = {"mc_code": mc_code}
    if hub_id:
        query += " AND Hub_ID = :hub_id"
        params["hub_id"] = hub_id
    query += " ORDER BY Created_At ASC"

    records = fetch_query(query, params)
    if not records:
        return {
            "MC_Code": mc_code,
            "Hub_Filter": hub_id if hub_id else "All Hubs",
            "Yearly_Distribution_Trend": {},
            "Message": "✅ No records found for yearly trend."
        }

    df = pd.DataFrame(records)
    df["Created_At"] = pd.to_datetime(df["Created_At"], errors="coerce")
    df = df.dropna(subset=["Created_At"])
    df["Year"] = df["Created_At"].dt.year

    summary = {}

    # ✅ improved numeric converter
    def safe_num(x):
        if x is None:
            return None
        try:
            val = float(x)
            if np.isnan(val) or np.isinf(val):
                return None
            return round(val, 4)
        except Exception:
            return None

    def assign_grade(eff):
        if eff is None:
            return "Unknown"
        if eff >= 85:
            return "A (Excellent)"
        elif eff >= 70:
            return "B (Good)"
        elif eff >= 55:
            return "C (Moderate)"
        elif eff >= 40:
            return "D (Poor)"
        else:
            return "E (Critical)"

    for hub in df["Hub_ID"].unique():
        hub_df = df[df["Hub_ID"] == hub].copy()
        if hub_df.empty:
            continue

        yearly_data = (
            hub_df.groupby("Year")
            .agg({
                "Predicted_Supply_Efficiency": "mean",
                "Critical_Risk": "sum"
            })
            .rename(columns={
                "Predicted_Supply_Efficiency": "Average_Efficiency",
                "Critical_Risk": "Critical_Count"
            })
            .reset_index()
            .sort_values("Year")
        )

        # rolling 3-year smoothing
        yearly_data["Rolling_3yr_Avg"] = yearly_data["Average_Efficiency"].rolling(window=3, min_periods=1).mean()
        yearly_data["Yearly_Delta"] = yearly_data["Average_Efficiency"].diff().round(2)
        yearly_data["Trend"] = yearly_data["Yearly_Delta"].apply(
            lambda x: "Improving" if pd.notna(x) and x > 1.0
            else "Degrading" if pd.notna(x) and x < -1.0
            else "Stable"
        )
        yearly_data["Performance_Grade"] = yearly_data["Average_Efficiency"].apply(assign_grade)
        yearly_data["Volatility_Index"] = yearly_data["Average_Efficiency"].rolling(window=3, min_periods=2).std().fillna(0).round(2)

        # long-term 3-year comparison
        if len(yearly_data) >= 3:
            early_avg = yearly_data["Rolling_3yr_Avg"].iloc[:3].mean()
            latest_avg = yearly_data["Rolling_3yr_Avg"].iloc[-3:].mean()
            diff = latest_avg - early_avg
            long_term_trend = "Improving" if diff > 2 else "Degrading" if diff < -2 else "Stable"
        else:
            long_term_trend = "Insufficient Data"

        latest_eff = safe_num(yearly_data["Average_Efficiency"].iloc[-1])
        latest_vol = safe_num(yearly_data["Volatility_Index"].iloc[-1])

        commentary = (
            f"Hub {hub} shows a {long_term_trend.lower()} trend overall. "
            f"Latest efficiency is {latest_eff if latest_eff is not None else 'N/A'}%. "
            f"Volatility Index: {latest_vol if latest_vol is not None else 'N/A'}."
        )

        records_per_year = {}
        for _, row in yearly_data.iterrows():
            y = str(int(row["Year"]))
            records_per_year[y] = {
                "Average_Efficiency": safe_num(row["Average_Efficiency"]),
                "Critical_Count": int(row["Critical_Count"]),
                "Rolling_3yr_Avg": safe_num(row["Rolling_3yr_Avg"]),
                "Yearly_Delta": safe_num(row["Yearly_Delta"]),
                "Trend": row["Trend"],
                "Performance_Grade": row["Performance_Grade"],
                "Volatility_Index": safe_num(row["Volatility_Index"])
            }

        summary[hub] = {
            "Records_Per_Year": records_per_year,
            "Long_Term_Trend": long_term_trend,
            "AI_Commentary": commentary
        }

    return {
        "MC_Code": mc_code,
        "Hub_Filter": hub_id if hub_id else "All Hubs",
        "Yearly_Distribution_Trend": summary,
        "Message": "✅ AI-enhanced yearly efficiency trend generated successfully"
    }