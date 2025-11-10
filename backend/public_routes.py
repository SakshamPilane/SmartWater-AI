# public_routes.py
from fastapi import APIRouter, HTTPException
from database import fetch_query

public_router = APIRouter()

@public_router.get("/public-overall-stats")
def get_public_overall_stats():
    """Public Maharashtra-level water statistics — no authentication needed."""
    try:
        mc_count_query = "SELECT COUNT(*) AS Total_MC FROM municipal_data"
        mc_result = fetch_query(mc_count_query)
        total_mc = mc_result[0]["Total_MC"] if mc_result else 0

        pop_query = "SELECT SUM(Population) AS Total_Population FROM municipal_data"
        pop_result = fetch_query(pop_query)
        total_pop = pop_result[0]["Total_Population"] if pop_result else 0

        eff_query = "SELECT AVG(Predicted_Supply_Efficiency) AS Avg_Efficiency FROM water_distribution_records"
        eff_result = fetch_query(eff_query)
        avg_efficiency = (
            round(eff_result[0]["Avg_Efficiency"], 2)
            if eff_result and eff_result[0]["Avg_Efficiency"]
            else 0
        )

        wqi_query = "SELECT AVG(WQI) AS Avg_WQI FROM water_quality_records"
        wqi_result = fetch_query(wqi_query)
        avg_wqi = (
            round(wqi_result[0]["Avg_WQI"], 2)
            if wqi_result and wqi_result[0]["Avg_WQI"]
            else 0
        )

        return {
            "Total_Municipal_Corporations": total_mc,
            "Total_Population": total_pop,
            "Average_WQI": avg_wqi,
            "Average_Distribution_Efficiency": avg_efficiency,
            "Message": "✅ Public Maharashtra Water Statistics fetched successfully.",
            "Public_Access": True
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching public stats: {str(e)}")
