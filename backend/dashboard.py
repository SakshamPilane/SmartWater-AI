# dashboard.py
from fastapi import APIRouter, HTTPException, Depends
from database import fetch_query
from login import get_current_user  # ✅ Import JWT validation

router = APIRouter()

# =====================================================
# 🔹 Dashboard endpoint (Protected)
# =====================================================
@router.get("/dashboard/{mc_code}")
def get_dashboard_data(mc_code: str, current_user: dict = Depends(get_current_user)):
    """
    Fetch dashboard data for a specific municipal corporation.
    Protected route — requires a valid JWT token.
    """
    # ✅ Authorization check (optional, ensures MC matches token)
    if current_user["mc_code"] != mc_code:
        raise HTTPException(status_code=403, detail="Access denied: not authorized for this municipal corporation.")

    # Fetch MC info
    mc_query = """
        SELECT MC_Code, MC_Name, Population, Total_Demand_MLD, Current_Supply_MLD,
               Division_Code, predicted_efficiency, critical_risk, recommended_action, last_updated
        FROM municipal_data
        WHERE MC_Code = :mc_code
    """
    mc_result = fetch_query(mc_query, {"mc_code": mc_code})
    if not mc_result:
        raise HTTPException(status_code=404, detail="Municipal Corporation not found.")

    # Fetch associated hubs
    hubs_query = """
        SELECT h.Hub_ID, h.Hub_Name
        FROM mc_hub_mapping m
        JOIN hub_table h ON m.Hub_ID = h.Hub_ID
        WHERE m.MC_Code = :mc_code
        ORDER BY h.Hub_Name ASC
    """
    hubs_result = fetch_query(hubs_query, {"mc_code": mc_code})

    return {
        "municipal_info": mc_result[0],
        "connected_hubs": hubs_result or [],
        "message": f"Dashboard data for {mc_result[0]['MC_Name']}"
    }

# =====================================================
# 🔹 Overall Statistics (Protected)
# =====================================================
@router.get("/overall-stats")
def get_overall_stats(current_user: dict = Depends(get_current_user)):
    """
    Fetches overall Maharashtra-level water management stats.
    Accessible only to authenticated users.
    """
    try:
        # Total Municipal Corporations
        mc_count_query = "SELECT COUNT(*) AS Total_MC FROM municipal_data"
        mc_result = fetch_query(mc_count_query)
        total_mc = mc_result[0]["Total_MC"] if mc_result else 0

        # Total Population
        pop_query = "SELECT SUM(Population) AS Total_Population FROM municipal_data"
        pop_result = fetch_query(pop_query)
        total_pop = pop_result[0]["Total_Population"] if pop_result else 0

        # Average Water Supply Efficiency
        eff_query = "SELECT AVG(Predicted_Supply_Efficiency) AS Avg_Efficiency FROM water_distribution_records"
        eff_result = fetch_query(eff_query)
        avg_efficiency = round(eff_result[0]["Avg_Efficiency"], 2) if eff_result and eff_result[0]["Avg_Efficiency"] else 0

        # Average Water Quality Index
        wqi_query = "SELECT AVG(WQI) AS Avg_WQI FROM water_quality_records"
        wqi_result = fetch_query(wqi_query)
        avg_wqi = round(wqi_result[0]["Avg_WQI"], 2) if wqi_result and wqi_result[0]["Avg_WQI"] else 0

        # Total anomalies & critical hubs
        anomalies_query = "SELECT COUNT(*) AS Total_Anomalies FROM water_quality_records WHERE Anomaly_Status='Anomaly Detected'"
        crit_query = "SELECT COUNT(DISTINCT Hub_ID) AS Critical_Hubs FROM water_distribution_records WHERE Critical_Risk=1"

        anomaly_count = fetch_query(anomalies_query)[0]["Total_Anomalies"]
        critical_hubs = fetch_query(crit_query)[0]["Critical_Hubs"]

        # Last update
        last_update_q = """
            SELECT MAX(Created_At) AS Last_Updated FROM (
                SELECT MAX(Created_At) AS Created_At FROM water_quality_records
                UNION
                SELECT MAX(Created_At) AS Created_At FROM water_distribution_records
            ) AS combined
        """
        last_update = fetch_query(last_update_q)[0]["Last_Updated"]

        return {
            "Total_Municipal_Corporations": total_mc,
            "Total_Population": total_pop,
            "Average_WQI": avg_wqi,
            "Average_Distribution_Efficiency": avg_efficiency,
            "Total_Anomalies": anomaly_count,
            "Total_Critical_Hubs": critical_hubs,
            "Last_Updated": str(last_update),
            "Message": "✅ Overall Maharashtra Water Statistics fetched successfully.",
            "Requested_By": current_user["username"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching overall stats: {str(e)}")


# =====================================================
# 🔹 State Trends (Protected)
# =====================================================
@router.get("/state-trends")
def get_state_trends(current_user: dict = Depends(get_current_user)):
    """
    Fetch year-wise trend of WQI and Efficiency across the state.
    Requires JWT token.
    """
    query = """
        SELECT 
            YEAR(Created_At) AS Year,
            ROUND(AVG(WQI),2) AS Avg_WQI,
            ROUND(AVG(Predicted_Supply_Efficiency),2) AS Avg_Efficiency
        FROM (
            SELECT WQI, NULL AS Predicted_Supply_Efficiency, Created_At FROM water_quality_records
            UNION ALL
            SELECT NULL AS WQI, Predicted_Supply_Efficiency, Created_At FROM water_distribution_records
        ) merged
        WHERE Created_At IS NOT NULL
        GROUP BY YEAR(Created_At)
        ORDER BY Year ASC
    """
    data = fetch_query(query)
    if not data:
        raise HTTPException(status_code=404, detail="No trend data found")
    return {
        "Trend_Data": data,
        "Message": "✅ State-level yearly trend data generated successfully.",
        "Requested_By": current_user["username"]
    }
