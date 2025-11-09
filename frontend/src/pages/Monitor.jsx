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
import "./Monitor.css";

const API_BASE = "http://127.0.0.1:8000";

const Monitor = () => {
  const navigate = useNavigate();
  const [hubList, setHubList] = useState([]);
  const [selectedHub, setSelectedHub] = useState("");
  const [result, setResult] = useState(null);
  const [trend, setTrend] = useState([]);
  const [yearlyTrend, setYearlyTrend] = useState({});
  const [anomalies, setAnomalies] = useState([]);
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [activeView, setActiveView] = useState(null);

  const mcCode = localStorage.getItem("mc_code");
  const mcName = localStorage.getItem("mc_name");

  // 🏙️ Fetch hubs
  useEffect(() => {
    if (!mcCode) {
      navigate("/login");
      return;
    }
    axios
      .get(`${API_BASE}/api/mc/${mcCode}/hubs`)
      .then((res) => setHubList(res.data?.Hubs || []))
      .catch(() => setError("⚠️ Failed to load hubs."));
  }, [mcCode, navigate]);

  // 📋 Input fields
  const [formData, setFormData] = useState({
    Temperature_Min: 35,
    Temperature_Max: 40,
    pH_Min: 5.5,
    pH_Max: 6.0,
    Conductivity_Min: 1500,
    Conductivity_Max: 2000,
    BOD_Min: 12,
    BOD_Max: 15,
    Faecal_Coliform_Min: 600,
    Faecal_Coliform_Max: 1000,
    Total_Coliform_Min: 600,
    Total_Coliform_Max: 1000,
    Nitrate_N_Min: 10,
    Nitrate_N_Max: 15,
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  // 🧠 Predict WQI
  const handlePredict = async () => {
    setError("");
    setResult(null);
    setTrend([]);
    setYearlyTrend({});
    setAnomalies([]);
    setRecords([]);
    setActiveView("predict");

    if (!selectedHub) return setError("Please select a Hub before prediction.");

    const payload = {
      MC_Code: mcCode,
      Hub_ID: selectedHub,
      ...Object.fromEntries(
        Object.entries(formData).map(([k, v]) => [k, parseFloat(v) || 0])
      ),
    };

    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/api/predict-quality`, payload);
      setResult(res.data);
    } catch (err) {
      console.error("❌ Prediction Error:", err);
      setError(
        err.response?.data?.detail || "Prediction failed. Check backend logs."
      );
    } finally {
      setLoading(false);
    }
  };

  // 📈 Trend
  const fetchTrend = async () => {
    setActiveView("trend");
    setResult(null);
    setYearlyTrend({});
    setAnomalies([]);
    setRecords([]);
    setError("");

    if (!selectedHub) return setError("Select a hub first.");
    try {
      const res = await axios.get(
        `${API_BASE}/api/mc/${mcCode}/trend?Hub_ID=${selectedHub}`
      );
      setTrend(res.data.Trend_Summary[selectedHub]?.Records || []);
    } catch {
      setError("Trend data unavailable.");
    }
  };

  // 📆 Yearly trend
  const fetchYearlyTrend = async () => {
    setActiveView("yearly");
    setResult(null);
    setTrend([]);
    setAnomalies([]);
    setRecords([]);
    setError("");

    if (!selectedHub) return setError("Select a hub first.");
    try {
      const res = await axios.get(
        `${API_BASE}/api/mc/${mcCode}/yearly-trend?Hub_ID=${selectedHub}`
      );
      setYearlyTrend(res.data.Yearly_Trend_Summary[selectedHub] || {});
    } catch {
      setError("Yearly trend unavailable.");
    }
  };

  // ⚠️ Anomalies
  const fetchAnomalies = async () => {
    setActiveView("anomalies");
    setResult(null);
    setTrend([]);
    setYearlyTrend({});
    setRecords([]);
    setError("");

    if (!selectedHub) return setError("Select a hub first.");
    try {
      const res = await axios.get(
        `${API_BASE}/api/mc/${mcCode}/anomalies?Hub_ID=${selectedHub}`
      );
      setAnomalies(res.data.Records || []);
    } catch {
      setError("No anomalies found.");
    }
  };

  // 📜 Records
  const fetchRecords = async () => {
    setActiveView("records");
    setResult(null);
    setTrend([]);
    setYearlyTrend({});
    setAnomalies([]);
    setError("");

    if (!selectedHub) return setError("Select a hub first.");
    try {
      const res = await axios.get(
        `${API_BASE}/api/mc/${mcCode}/quality-records?Hub_ID=${selectedHub}`
      );
      setRecords(res.data.Records || []);
    } catch {
      setError("No records found.");
    }
  };

  // 🚪 Logout
  const handleLogout = () => {
    localStorage.clear();
    navigate("/login");
  };

  // 🎨 WQI color map
  const getWQIColor = (category) => {
    switch (category?.toLowerCase()) {
      case "excellent":
        return "#00b894";
      case "good":
        return "#74b9ff";
      case "moderate":
        return "#fdcb6e";
      case "poor":
        return "#e17055";
      case "very poor":
        return "#d63031";
      default:
        return "#636e72";
    }
  };

  return (
    <div className="monitor-container">
      {/* 🧭 Header Navbar */}
      <header className="dashboard-header">
        <div>
          <h2>{mcName || "Municipal Dashboard"}</h2>
          <p>Water Resource Department – Maharashtra</p>
        </div>
        <nav>
          <button onClick={() => navigate("/dashboard")}>Dashboard</button>
          <button onClick={() => navigate("/distribution")}>Distribution</button>
          <button onClick={handleLogout}>Logout</button>
        </nav>
      </header>

      {/* ================= FORM SECTION ================= */}
      <div className="monitor-form">
        <h3>📊 Enter Water Quality Parameters</h3>

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

          {Object.keys(formData).map((key) => (
            <div className="form-field" key={key}>
              <label>{key.replaceAll("_", " ")}</label>
              <input
                type="number"
                name={key}
                value={formData[key]}
                step="any"
                onChange={handleChange}
              />
            </div>
          ))}
        </div>

        {error && <p className="error-text">{error}</p>}

        <div className="action-buttons">
          <button
            className="analyze-btn"
            onClick={handlePredict}
            disabled={loading}
          >
            {loading ? "Analyzing..." : "Predict Quality"}
          </button>
          <button onClick={fetchTrend}>📈 Trend</button>
          <button onClick={fetchYearlyTrend}>📆 Yearly Report</button>
          <button onClick={fetchAnomalies}>⚠️ Anomalies</button>
          <button onClick={fetchRecords}>📋 History</button>
        </div>
      </div>

      {/* ✅ Prediction Results */}
      {activeView === "predict" && result && (
        <section className="prediction-section fade-in">
          <h3>✅ AI Water Quality Prediction Summary</h3>

          <div className="trend-stats-grid">
            <div className="trend-stat-card">
              <h4>💧 Final WQI</h4>
              <div
                className="trend-value"
                style={{ color: getWQIColor(result.Category) }}
              >
                {result.Final_WQI}
              </div>
              <span>{result.Category}</span>
            </div>

            <div className="trend-stat-card">
              <h4>{result.Emoji_Status} Status</h4>
              <div
                className={`trend-value ${
                  result.Anomaly_Status === "Anomaly Detected" ? "anomaly" : ""
                }`}
              >
                {result.Anomaly_Status === "Anomaly Detected"
                  ? "⚠️ Issue"
                  : "✅ Normal"}
              </div>
              <span>{result.Anomaly_Status}</span>
            </div>

            <div className="trend-stat-card">
              <h4>📖 AI Summary</h4>
              <div className="trend-value">🧠</div>
              <span>{result.Interpretation}</span>
            </div>
          </div>

          <div className="ai-summary-card">
            <h4>🧠 Detailed AI Analysis</h4>
            <p className="ai-text">{result.AI_Summary}</p>
            <div className="recommendation">
              <strong>Recommended Action:</strong>
              <p>{result.Recommended_Action}</p>
            </div>
          </div>

          <div className="details-card">
            <h4>⚙️ Technical Details</h4>
            <ul>
              <li>
                <strong>Model Blend:</strong> {result.Details?.Hybrid_Model}
              </li>
              <li>
                <strong>AI WQI:</strong> {result.Details?.ML_WQI}
              </li>
              <li>
                <strong>Rule-based WQI:</strong> {result.Details?.Rule_WQI}
              </li>
            </ul>

            <h5>📊 Input Feature Averages</h5>
            <div className="input-grid">
              {Object.entries(result.Details?.Input_Features || {}).map(
                ([key, value]) => (
                  <div key={key} className="input-chip">
                    <span>{key}</span>
                    <b>{value}</b>
                  </div>
                )
              )}
            </div>
          </div>

          <div className="save-message">
            <p>💾 {result.Message}</p>
          </div>
        </section>
      )}

      {/* 📈 Trend */}
      {activeView === "trend" && trend.length > 0 && (
        <div className="chart-section fade-in">
          <h3>📈 WQI Trend Over Time</h3>
          <ResponsiveContainer width="100%" height={320}>
            <LineChart data={trend}>
              <XAxis dataKey="Created_At" />
              <YAxis domain={[0, 100]} />
              <Tooltip />
              <Line
                type="monotone"
                dataKey="WQI"
                stroke="#0984e3"
                strokeWidth={2}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* 📆 Yearly Report */}
      {activeView === "yearly" && Object.keys(yearlyTrend).length > 0 && (
        <div className="chart-section fade-in">
          <h3>📆 Yearly Average WQI</h3>
          <ResponsiveContainer width="100%" height={320}>
            <BarChart
              data={Object.entries(yearlyTrend).map(([year, d]) => ({
                year,
                Average_WQI: d.Average_WQI,
              }))}
            >
              <XAxis dataKey="year" />
              <YAxis domain={[0, 100]} />
              <Tooltip />
              <Bar dataKey="Average_WQI" fill="#00cec9" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* ⚠️ Anomalies */}
      {activeView === "anomalies" && anomalies.length > 0 && (
        <div className="table-section fade-in">
          <h3>⚠️ Recent Anomalies</h3>
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Hub</th>
                <th>WQI</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {anomalies.map((a, i) => (
                <tr key={i}>
                  <td>{a.Created_At}</td>
                  <td>{a.Hub_ID}</td>
                  <td>{a.WQI}</td>
                  <td>{a.Anomaly_Status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* 📋 History */}
      {activeView === "records" && records.length > 0 && (
        <div className="table-section fade-in">
          <h3>📋 Historical Records</h3>
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Hub</th>
                <th>WQI</th>
                <th>Category</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {records.slice(0, 10).map((r, i) => (
                <tr key={i}>
                  <td>{r.Created_At}</td>
                  <td>{r.Hub_ID}</td>
                  <td>{r.WQI}</td>
                  <td>{r.Category}</td>
                  <td>{r.Anomaly_Status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default Monitor;
