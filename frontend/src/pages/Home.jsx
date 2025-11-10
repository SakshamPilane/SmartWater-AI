import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import govLogo from "../assets/logo.jpg";
import cmImage from "../assets/cm.png";
import dcm1 from "../assets/eknath_shinde.jpg";
import dcm2 from "../assets/ajit_pawar.jpg";
import vikhePatil from "../assets/radhakrishna_vikhe_patil.jpeg";
import girishMahajan from "../assets/girish_mahajan.jpeg";
import gulabPatil from "../assets/gulab_patil.jpg";
import sanjayRathod from "../assets/sanjay_rathod.jpg";
import "./Home.css";

const API_BASE = "http://127.0.0.1:8000";

const Home = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    totalCorporations: 0,
    totalPopulation: 0,
    avgWQI: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // 🌿 Government Water Initiatives
  const yojanas = [
    {
      title: "Jal Jeevan Mission",
      desc: "Ensuring safe and adequate drinking water through individual household tap connections by 2025.",
      icon: "💧",
    },
    {
      title: "Mukhyamantri Jal Swavalamban Abhiyan",
      desc: "Focused on water conservation and management to make Maharashtra drought-free.",
      icon: "🌾",
    },
    {
      title: "Smart Water Monitoring Initiative",
      desc: "IoT-enabled sensors to monitor municipal water quality and supply efficiency.",
      icon: "📊",
    },
    {
      title: "Amrut 2.0 Urban Water Scheme",
      desc: "Upgrading city water infrastructure with modern treatment and recycling systems.",
      icon: "🏙️",
    },
  ];

  // 💧 Fetch Public Maharashtra Overview (no auth)
  useEffect(() => {
    const fetchOverview = async () => {
      try {
        setLoading(true);
        const res = await fetch(`${API_BASE}/api/public-overall-stats`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        setStats({
          totalCorporations: data.Total_Municipal_Corporations || 0,
          totalPopulation: data.Total_Population || 0,
          avgWQI: data.Average_WQI || 0,
        });
      } catch (err) {
        console.error("❌ Error fetching public stats:", err);
        setError("⚠️ Unable to load public water statistics at the moment.");
      } finally {
        setLoading(false);
      }
    };

    fetchOverview();
  }, []);

  return (
    <div className="home-container">
      {/* ---------- Header ---------- */}
      <header className="home-header">
        <div className="logo-section" onClick={() => navigate("/")}>
          <img src={govLogo} alt="Government Logo" className="gov-logo" />
          <div>
            <h1>महाराष्ट्र शासन</h1>
            <h2>Government of Maharashtra – Water Resource Department</h2>
          </div>
        </div>

        <nav className="navbar">
          <button onClick={() => navigate("/login")}>Login</button>
          <button onClick={() => navigate("/monitor")}>Monitor</button>
          <button onClick={() => navigate("/distribution")}>Distribution</button>
        </nav>
      </header>

      {/* ---------- Ministers Section ---------- */}
      <section className="leaders-section">
        <h3>🏛️ State Leadership</h3>
        <div className="leaders-container">
          <div className="leader-card">
            <img src={cmImage} alt="Chief Minister" className="leader-photo" />
            <h4>Shri Devendra Fadnavis</h4>
            <p>Hon’ble Chief Minister, Maharashtra</p>
          </div>
          <div className="leader-card">
            <img src={dcm1} alt="Deputy CM 1" className="leader-photo" />
            <h4>Shri Eknath Shinde</h4>
            <p>Deputy Chief Minister, Maharashtra</p>
          </div>
          <div className="leader-card">
            <img src={dcm2} alt="Deputy CM 2" className="leader-photo" />
            <h4>Shri Ajit Pawar</h4>
            <p>Deputy Chief Minister, Maharashtra</p>
          </div>
        </div>

        <h3 style={{ marginTop: "30px" }}>
          🚰 Water Resource & Conservation Ministers
        </h3>
        <div className="leaders-container">
          <div className="leader-card">
            <img src={vikhePatil} alt="Water Minister 1" className="leader-photo" />
            <h4>Shri Radhakrishna Vikhe Patil</h4>
            <p>Minister for Water Resources (Godavari & Krishna Valley Development)</p>
          </div>
          <div className="leader-card">
            <img src={girishMahajan} alt="Water Minister 2" className="leader-photo" />
            <h4>Shri Girish Mahajan</h4>
            <p>Minister for Water Resources (Vidarbha, Tapi & Konkan Development)</p>
          </div>
          <div className="leader-card">
            <img src={gulabPatil} alt="Water Minister 3" className="leader-photo" />
            <h4>Shri Gulab Raghunath Patil</h4>
            <p>Minister for Water Supply and Sanitation</p>
          </div>
          <div className="leader-card">
            <img src={sanjayRathod} alt="Water Minister 4" className="leader-photo" />
            <h4>Shri Sanjay Rathod</h4>
            <p>Minister for Soil and Water Conservation</p>
          </div>
        </div>
      </section>

      {/* ---------- Maharashtra Water Overview ---------- */}
      <section className="summary-section">
        <h3>💧 Maharashtra Water Overview (2025)</h3>

        {loading ? (
          <p className="loading-text">Fetching latest statistics...</p>
        ) : error ? (
          <p className="error-text">{error}</p>
        ) : (
          <>
            <div className="stat-card">
              <h3>Total Corporations</h3>
              <div className="stat-value">{stats.totalCorporations}</div>
              <span>Municipal Bodies</span>
            </div>

            <div className="stat-card">
              <h3>Total Population</h3>
              <div className="stat-value">
                {stats.totalPopulation
                  ? stats.totalPopulation.toLocaleString()
                  : "—"}
              </div>
              <span>Citizens Served</span>
            </div>

            <div className="stat-card">
              <h3>Average WQI</h3>
              <div className="stat-value">{stats.avgWQI}</div>
              <span>Water Quality Index</span>
            </div>
          </>
        )}
      </section>

      {/* ---------- Yojanas Section ---------- */}
      <section className="yojana-section">
        <h3>🌿 Major Water Initiatives & Yojanas</h3>
        <div className="yojana-list">
          {yojanas.map((yoj, index) => (
            <div className="yojana-card" key={index}>
              <span className="yojana-icon">{yoj.icon}</span>
              <h4>{yoj.title}</h4>
              <p>{yoj.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ---------- Government Info Links ---------- */}
      <section className="gov-links">
        <h3>📘 Useful Government Resources</h3>
        <ul>
          <li>
            <a href="https://www.maharashtra.gov.in" target="_blank" rel="noreferrer">
              Official Maharashtra Government Portal
            </a>
          </li>
          <li>
            <a href="https://wrd.maharashtra.gov.in" target="_blank" rel="noreferrer">
              Water Resources Department, Maharashtra
            </a>
          </li>
          <li>
            <a href="https://jalshakti-dowr.gov.in/" target="_blank" rel="noreferrer">
              Ministry of Jal Shakti – Government of India
            </a>
          </li>
          <li>
            <a href="https://amrut.gov.in/" target="_blank" rel="noreferrer">
              AMRUT 2.0 – Urban Water Mission
            </a>
          </li>
          <li>
            <a href="https://jaljeevanmission.gov.in/" target="_blank" rel="noreferrer">
              Jal Jeevan Mission Portal
            </a>
          </li>
        </ul>
      </section>

      {/* ---------- Footer ---------- */}
      <footer className="footer">
        <p>
          © 2025 Government of Maharashtra | Water Resources Department | All Rights Reserved.
        </p>
        <p>
          Designed & Developed for Academic Demonstration by <b>Saksham Pilane</b>
        </p>
      </footer>
    </div>
  );
};

export default Home;
