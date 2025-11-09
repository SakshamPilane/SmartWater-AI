import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import getHubImage from "../utils/getHubImage";
import "./Dashboard.css";

const API_BASE = "http://127.0.0.1:8000";

const Dashboard = () => {
  const navigate = useNavigate();
  const [hubs, setHubs] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  // 🔹 Trend display
  const [trendType, setTrendType] = useState(null); // "quality" | "distribution"
  const [trendData, setTrendData] = useState(null);
  const [selectedHub, setSelectedHub] = useState(null);
  const [loadingTrend, setLoadingTrend] = useState(false);

  const mcCode = localStorage.getItem("mc_code");
  const mcName = localStorage.getItem("mc_name");

  // 🧠 Fetch Hubs
  useEffect(() => {
    if (!mcCode) {
      navigate("/login");
      return;
    }

    axios
      .get(`${API_BASE}/api/mc/${mcCode}/hubs`)
      .then((res) => setHubs(res.data?.Hubs || []))
      .catch(() => setError("⚠️ Failed to load hubs."))
      .finally(() => setLoading(false));
  }, [mcCode, navigate]);

  // 💧 Fetch water quality or distribution trend
  const fetchTrend = async (hub, type) => {
    setTrendData(null);
    setTrendType(type);
    setSelectedHub(hub);
    setLoadingTrend(true);

    try {
      let endpoint = "";
      if (type === "quality") {
        endpoint = `${API_BASE}/api/mc/${mcCode}/trend?Hub_ID=${hub.Hub_ID}`;
      } else {
        endpoint = `${API_BASE}/api/mc/${mcCode}/distribution-trend`;
      }

      const res = await axios.get(endpoint);
      setTrendData(res.data.Trend_Summary || {});
    } catch (err) {
      console.error("❌ Trend Fetch Error:", err);
      setTrendData(null);
      setError("Failed to fetch trend data.");
    } finally {
      setLoadingTrend(false);
    }
  };

  const handleLogout = () => {
    localStorage.clear();
    navigate("/login");
  };

  return (
    <div className="dashboard-container">
      {/* 🧭 Header */}
      <header className="dashboard-header">
        <div>
          <h2>{mcName || "Municipal Dashboard"}</h2>
          <p>Water Resource Department – Maharashtra</p>
        </div>
        <nav>
          <button onClick={() => navigate("/monitor")}>Monitor Quality</button>
          <button onClick={() => navigate("/distribution")}>Distribution</button>
          <button onClick={handleLogout}>Logout</button>
        </nav>
      </header>

      {loading ? (
        <div className="loading-spinner">Loading Dashboard...</div>
      ) : error ? (
        <p className="error">{error}</p>
      ) : (
        <>
          {/* 💧 Hubs Section */}
          <section className="hub-section">
            <h3>Registered Hubs</h3>
            {hubs.length === 0 ? (
              <p className="error">No hubs available for {mcName}.</p>
            ) : (
              <div className="hub-grid">
                {hubs.map((hub) => (
                  <div key={hub.Hub_ID} className="hub-card fade-in">
                    <img
                      src={getHubImage(hub.Hub_ID)}
                      alt={hub.Hub_Name}
                      className="hub-img"
                      onError={(e) => (e.target.src = "/fallback.jpg")}
                    />
                    <h4>{hub.Hub_Name}</h4>
                    <p>ID: {hub.Hub_ID}</p>

                    <div className="trend-buttons">
                      <button
                        className="trend-btn primary"
                        onClick={() => fetchTrend(hub, "quality")}
                      >
                        Monitor Trends
                      </button>
                      <button
                        className="trend-btn secondary"
                        onClick={() => fetchTrend(hub, "distribution")}
                      >
                        Distribution Trends
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>

          {/* 📊 Trends Section */}
          {trendData && (
            <section className="trend-section fade-in">
              <h3>
                {trendType === "quality"
                  ? `💧 Water Quality Trend – ${selectedHub?.Hub_Name}`
                  : `⚙️ Distribution Efficiency Trend – ${mcName}`}
              </h3>

              {trendType === "distribution" && (
                <p className="note">
                  * Distribution data shown is for the entire Municipal
                  Corporation.
                </p>
              )}

              {loadingTrend ? (
                <p>Loading trend data...</p>
              ) : (
                <div className="trend-stats-grid">
                  {trendType === "quality" ? (
                    <>
                      <div className="trend-stat-card">
                        <h4>Average WQI</h4>
                        <div className="trend-value">
                          {trendData[selectedHub?.Hub_ID]?.Average_WQI ?? "—"}
                        </div>
                        <span>Water Quality Index</span>
                      </div>

                      <div className="trend-stat-card">
                        <h4>Total Records</h4>
                        <div className="trend-value">
                          {trendData[selectedHub?.Hub_ID]?.Total_Records ?? "—"}
                        </div>
                        <span>Data Entries</span>
                      </div>

                      <div className="trend-stat-card">
                        <h4>Anomalies</h4>
                        <div className="trend-value anomaly">
                          {trendData[selectedHub?.Hub_ID]?.Anomaly_Count ?? 0}
                        </div>
                        <span>Detected Issues</span>
                      </div>
                    </>
                  ) : (
                    <>
                      <div className="trend-stat-card">
                        <h4>Average Efficiency</h4>
                        <div className="trend-value">
                          {trendData[selectedHub?.Hub_ID]?.Average_Efficiency ??
                            "—"}
                          %
                        </div>
                        <span>Distribution</span>
                      </div>

                      <div className="trend-stat-card">
                        <h4>Total Records</h4>
                        <div className="trend-value">
                          {trendData[selectedHub?.Hub_ID]?.Total_Records ?? "—"}
                        </div>
                        <span>Distribution Logs</span>
                      </div>

                      <div className="trend-stat-card">
                        <h4>Critical Risks</h4>
                        <div className="trend-value anomaly">
                          {trendData[selectedHub?.Hub_ID]?.Critical_Count ?? 0}
                        </div>
                        <span>Performance Alerts</span>
                      </div>
                    </>
                  )}
                </div>
              )}
            </section>
          )}
        </>
      )}
    </div>
  );
};

export default Dashboard;
