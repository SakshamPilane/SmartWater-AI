import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
} from "recharts";
import "./DistributionDashboard.css"; // ✅ Updated to new CSS

const API_BASE = "http://127.0.0.1:8000";

const DistributionDashboard = () => {
  const navigate = useNavigate();
  const [hubList, setHubList] = useState([]);
  const [selectedHub, setSelectedHub] = useState("");
  const [formData, setFormData] = useState({
    Total_Demand_MLD: 150,
    Current_Supply_MLD: 120,
    Population: 800000,
  });
  const [result, setResult] = useState(null);
  const [trend, setTrend] = useState([]);
  const [yearlyTrend, setYearlyTrend] = useState({});
  const [critical, setCritical] = useState([]);
  const [records, setRecords] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [activeView, setActiveView] = useState(null);

  const mcCode = localStorage.getItem("mc_code");
  const mcName = localStorage.getItem("mc_name");
  const token = localStorage.getItem("access_token");

  // 🚫 Redirect if token missing
  useEffect(() => {
    if (!token || !mcCode) {
      navigate("/login");
      return;
    }
  }, [token, mcCode, navigate]);

  // 🧩 Axios instance with auth
  const axiosAuth = axios.create({
    baseURL: API_BASE,
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  // 🏙️ Fetch hubs (Authenticated)
  useEffect(() => {
    if (!mcCode) {
      navigate("/login");
      return;
    }
    axiosAuth
      .get(`/api/mc/${mcCode}/hubs`)
      .then((res) => setHubList(res.data?.Hubs || []))
      .catch(() => setError("⚠️ Failed to load hubs."));
  }, [mcCode, navigate]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: parseFloat(value) || 0 }));
  };

  // 🔮 Predict Efficiency (Authenticated)
  const handlePredict = async () => {
    setError("");
    setResult(null);
    setTrend([]);
    setYearlyTrend({});
    setCritical([]);
    setRecords([]);
    setActiveView("predict");

    if (!selectedHub) return setError("Please select a Hub before prediction.");

    const payload = {
      MC_Code: mcCode,
      Hub_ID: selectedHub,
      ...formData,
    };

    setLoading(true);
    try {
      const res = await axiosAuth.post(`/api/predict-distribution`, payload);
      setResult(res.data);
    } catch (err) {
      console.error("❌ Prediction Error:", err);
      setError(err.response?.data?.detail || "Prediction failed.");
    } finally {
      setLoading(false);
    }
  };

  // 📈 Trend (Authenticated)
  const fetchTrend = async () => {
    setActiveView("trend");
    setResult(null);
    setYearlyTrend({});
    setCritical([]);
    setRecords([]);
    setError("");

    if (!selectedHub) return setError("Select a hub first.");
    try {
      const res = await axiosAuth.get(
        `/api/mc/${mcCode}/distribution-trend?hub_id=${selectedHub}`
      );
      setTrend(res.data.Trend_Summary[selectedHub]?.Records || []);
    } catch {
      setError("Trend data unavailable.");
    }
  };

  // 📆 Yearly Trend (Authenticated)
  const fetchYearlyTrend = async () => {
    setActiveView("yearly");
    setResult(null);
    setTrend([]);
    setCritical([]);
    setRecords([]);
    setError("");

    if (!selectedHub) return setError("Select a hub first.");
    try {
      const res = await axiosAuth.get(
        `/api/mc/${mcCode}/yearly-distribution-trend?hub_id=${selectedHub}`
      );
      setYearlyTrend(
        res.data.Yearly_Distribution_Trend[selectedHub]?.Records_Per_Year || {}
      );
    } catch {
      setError("Yearly trend unavailable.");
    }
  };

  // ⚠️ Critical Summary (Authenticated)
  const fetchCritical = async () => {
    setActiveView("critical");
    setResult(null);
    setTrend([]);
    setYearlyTrend({});
    setRecords([]);
    setError("");
    try {
      const res = await axiosAuth.get(`/api/mc/${mcCode}/critical-summary`);
      setCritical(res.data.Records || []);
    } catch {
      setError("No critical events found.");
    }
  };

  // 📋 Latest Records (Authenticated)
  const fetchRecords = async () => {
    setActiveView("records");
    setResult(null);
    setTrend([]);
    setYearlyTrend({});
    setCritical([]);
    setError("");

    try {
      const token = localStorage.getItem("access_token");
      if (!token) {
        navigate("/login");
        return;
      }

      const res = await axios.get(`${API_BASE}/api/mc/${mcCode}/distribution-latest`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      setRecords(res.data.Latest_Records || []);
    } catch {
      setError("No recent data available.");
    }
  };

  // 🚪 Logout
  const handleLogout = () => {
    localStorage.clear();
    navigate("/login");
  };

  // 🎨 Status Colors
  const getStatusColor = (status) => {
    if (status?.includes("Critical")) return "#d63031";
    if (status?.includes("Stable")) return "#00b894";
    return "#636e72";
  };

  return (
    <div className="distribution-container">
      {/* 🧭 Navbar */}
      <header className="dashboard-header">
        <div>
          <h2>{mcName || "Municipal Dashboard"}</h2>
          <p>Water Resource Department – Maharashtra</p>
        </div>
        <nav>
          <button onClick={() => navigate("/dashboard")}>Dashboard</button>
          <button onClick={() => navigate("/monitor")}>Monitor Quality</button>
          <button onClick={handleLogout}>Logout</button>
        </nav>
      </header>

      {/* ================= FORM SECTION ================= */}
      <div className="monitor-form">
        <h3>📊 Enter Distribution Parameters</h3>

        <div className="form-grid">
          <div className="form-field">
            <label>Hub *</label>
            <select
              value={selectedHub}
              onChange={(e) => setSelectedHub(e.target.value)}
              required
            >
              <option value="">Select Hub</option>
              {hubList.map((hub) => (
                <option key={hub.Hub_ID} value={hub.Hub_ID}>
                  {hub.Hub_Name}
                </option>
              ))}
            </select>
          </div>

          <div className="form-field">
            <label>Total Demand (MLD)</label>
            <input
              type="number"
              name="Total_Demand_MLD"
              value={formData.Total_Demand_MLD}
              onChange={handleChange}
            />
          </div>
          <div className="form-field">
            <label>Current Supply (MLD)</label>
            <input
              type="number"
              name="Current_Supply_MLD"
              value={formData.Current_Supply_MLD}
              onChange={handleChange}
            />
          </div>
          <div className="form-field">
            <label>Population</label>
            <input
              type="number"
              name="Population"
              value={formData.Population}
              onChange={handleChange}
            />
          </div>
        </div>

        {error && <p className="error-text">{error}</p>}

        <div className="action-buttons">
          <button className="analyze-btn" onClick={handlePredict} disabled={loading}>
            {loading ? "Analyzing..." : "Predict Efficiency"}
          </button>
          <button onClick={fetchTrend}>📈 Trend</button>
          <button onClick={fetchYearlyTrend}>📆 Yearly Report</button>
          <button onClick={fetchCritical}>⚠️ Critical Summary</button>
          <button onClick={fetchRecords}>📋 History</button>
        </div>
      </div>

      {/* ✅ Prediction Cards */}
      {activeView === "predict" && result && (
        <section className="prediction-section fade-in">
          <h3>✅ AI Distribution Efficiency Summary</h3>

          <div className="trend-stats-grid">
            <div className="trend-stat-card">
              <h4>⚙️ Efficiency</h4>
              <div
                className="trend-value"
                style={{ color: getStatusColor(result.Status) }}
              >
                {result.Final_Efficiency}%
              </div>
              <span>{result.Performance_Grade}</span>
            </div>

            <div className="trend-stat-card">
              <h4>Status</h4>
              <div
                className={`trend-value ${result.Status?.includes("Critical") ? "anomaly" : ""
                  }`}
              >
                {result.Emoji_Status || "💧"}
              </div>
              <span>{result.Status}</span>
            </div>

            <div className="trend-stat-card">
              <h4>🧠 AI Summary</h4>
              <div className="trend-value">🤖</div>
              <span>{result.Interpretation}</span>
            </div>
          </div>

          <div className="ai-summary-card">
            <h4>🧠 Detailed AI Analysis</h4>
            <p className="ai-text">{result.AI_Commentary}</p>
            <div className="recommendation">
              <strong>Recommended Action:</strong>
              <p>{result.Recommended_Action}</p>
            </div>
          </div>

          <div className="save-message">💾 {result.Message}</div>
        </section>
      )}

      {/* 📈 Efficiency Trend */}
      {activeView === "trend" && trend.length > 0 && (
        <div className="chart-section fade-in">
          <h3>📈 Efficiency Trend Over Time</h3>
          <ResponsiveContainer width="100%" height={320}>
            <LineChart data={trend}>
              <XAxis dataKey="Created_At" />
              <YAxis domain={[0, 100]} />
              <Tooltip />
              <Line
                type="monotone"
                dataKey="Predicted_Supply_Efficiency"
                stroke="#00b894"
                strokeWidth={2}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* 📆 Yearly Report */}
      {activeView === "yearly" && Object.keys(yearlyTrend).length > 0 && (
        <div className="chart-section fade-in">
          <h3>📆 Yearly Average Efficiency</h3>
          <ResponsiveContainer width="100%" height={320}>
            <BarChart
              data={Object.entries(yearlyTrend).map(([year, d]) => ({
                year,
                Average_Efficiency: d.Average_Efficiency,
              }))}
            >
              <XAxis dataKey="year" />
              <YAxis domain={[0, 100]} />
              <Tooltip />
              <Bar dataKey="Average_Efficiency" fill="#00cec9" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* ⚠️ Critical Risks */}
      {activeView === "critical" && critical.length > 0 && (
        <div className="table-section fade-in">
          <h3>⚠️ Critical Risk Hubs</h3>
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Hub</th>
                <th>Efficiency</th>
                <th>Recommended Action</th>
              </tr>
            </thead>
            <tbody>
              {critical.map((c, i) => (
                <tr key={i}>
                  <td>{c.Created_At}</td>
                  <td>{c.Hub_ID}</td>
                  <td>{c.Predicted_Supply_Efficiency}</td>
                  <td>{c.Recommended_Action}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* 📋 Records */}
      {activeView === "records" && records.length > 0 && (
        <div className="table-section fade-in">
          <h3>📋 Latest Distribution Records</h3>
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Hub</th>
                <th>Efficiency</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {records.map((r, i) => (
                <tr key={i}>
                  <td>{r.Created_At}</td>
                  <td>{r.Hub_ID}</td>
                  <td>{r.Predicted_Supply_Efficiency}</td>
                  <td>{r.Critical_Risk ? "⚠️ Critical" : "✅ Stable"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

// 🔒 Token-based Protection for Entire Component
export default function ProtectedDistributionDashboard() {
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) navigate("/login");
  }, [navigate]);

  return <DistributionDashboard />;
}