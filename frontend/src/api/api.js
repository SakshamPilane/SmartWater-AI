// src/api/api.js
import axios from "axios";

// ✅ Base API instance (switchable for local or production)
const API = axios.create({
  baseURL: process.env.REACT_APP_API_BASE || "http://127.0.0.1:8000",
});

// ---------------------
// 🧠 Core Monitoring Endpoints
// ---------------------
export const getMCList = () => API.get("/mc_list");
export const getHubsForMC = (mc_code) => API.get(`/get_hubs_for_mc/${mc_code}`);
export const getMCInfo = (mc_code) => API.get(`/get_mc_info/${mc_code}`);
export const getHubImage = (hub_id) => API.get(`/get_hub_image/${hub_id}`);

// ---------------------
// 💧 AI-Powered WQI Analysis
// ---------------------
export const getWQISummary = (payload) => API.post("/wqi_summary", payload);
export const predictWQI = (payload) => API.post("/predict_wqi", payload);
export const predictBatchWQI = (payload) => API.post("/predict_wqi_batch", payload);
export const checkAnomaly = (payload) => API.post("/anomaly_check", payload);
export const predictTrend = (mc_code, hub_id, days = 7) =>
  API.get(`/predict_trend?mc_code=${mc_code}&hub_id=${hub_id}&days=${days}`);

// ---------------------
// 🧭 Distribution / Legacy Endpoints
// ---------------------
export const getSummary = () => API.get("/distribution/summary");
export const getHistory = (mc_code) => API.get(`/distribution/history/${mc_code}`);
export const getEfficiencyTimeseries = (mc_code) =>
  API.get(`/distribution/dashboard/efficiency_timeseries/${mc_code}`);
export const simulate = (data) => API.post("/distribution/simulate", data);
export const simulateHub = (data) => API.post("/distribution/hub/simulate", data);
export const scanAnomalies = () => API.get("/anomaly_scan_all");

// ---------------------
// 🖼️ Image Utility
// ---------------------
export const fetchHubImage = async (hub_id) => {
  try {
    const res = await API.get(`/get_hub_image/${hub_id}`, { responseType: "blob" });
    return URL.createObjectURL(res.data);
  } catch (err) {
    console.error("❌ Failed to fetch hub image:", err);
    return null;
  }
};

// ---------------------
// ⚙️ Server Health Check
// ---------------------
export const pingServer = async () => {
  try {
    const res = await API.get("/healthcheck");
    return res.data;
  } catch (err) {
    console.error("❌ Server not reachable:", err.message);
    return null;
  }
};

export default API;
