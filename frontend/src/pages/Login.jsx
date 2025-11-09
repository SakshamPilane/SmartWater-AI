import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import govLogo from "../assets/logo.jpg";
import axios from "axios";
import "./Login.css";

const API_BASE = "http://127.0.0.1:8000"; // FastAPI backend

const Login = () => {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [mcList, setMcList] = useState([]);
  const [selectedMC, setSelectedMC] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  // ✅ Fetch list of Municipal Corporations
  useEffect(() => {
    axios
      .get(`${API_BASE}/api/municipal-list`)
      .then((res) => {
        if (res.data.Municipals) setMcList(res.data.Municipals);
      })
      .catch(() => setError("⚠️ Failed to load municipal list."));
  }, []);

  // ✅ Handle login
  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const formData = new FormData();
      formData.append("username", username);
      formData.append("password", password);
      formData.append("mc_code", selectedMC);

      const res = await axios.post(`${API_BASE}/api/login`, formData);

      if (res.data.status === "success") {
        const { mc_code, mc_name } = res.data;
        localStorage.setItem("mc_code", mc_code);
        localStorage.setItem("mc_name", mc_name);
        localStorage.setItem(
          "user",
          JSON.stringify({ username, mc_code, mc_name })
        );
        navigate("/dashboard");
      } else {
        setError("Invalid credentials. Please check again.");
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Login failed. Try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      {loading && <div className="loader-overlay">🔄 Authenticating...</div>}

      <div className="login-box">
        {/* Logo + Titles */}
        <img src={govLogo} alt="Government Logo" className="login-logo" />
        <h2>महाराष्ट्र शासन</h2>
        <h3>Water Resource Department – Secure Access</h3>

        {/* Form */}
        <form onSubmit={handleLogin} className="login-form">
          <div className="input-group">
            <input
              type="text"
              placeholder="Username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>

          <div className="input-group">
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <div className="input-group">
            <select
              value={selectedMC}
              onChange={(e) => setSelectedMC(e.target.value)}
              required
            >
              <option value="">Select Municipal Corporation</option>
              {mcList.map((mc) => (
                <option key={mc.MC_Code} value={mc.MC_Code}>
                  {mc.MC_Name}
                </option>
              ))}
            </select>
          </div>

          <button type="submit" disabled={loading}>
            {loading ? "Logging in..." : "Login"}
          </button>
        </form>

        {error && <p className="error">{error}</p>}

        <p className="back-home" onClick={() => navigate("/")}>
          ← Back to Home
        </p>
      </div>
    </div>
  );
};

export default Login;
