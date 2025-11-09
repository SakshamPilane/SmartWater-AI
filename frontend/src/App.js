import React from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";

// 🌐 Core Pages
import Home from "./pages/Home";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Monitor from "./pages/Monitor";

// 💧 Distribution Module Pages
import DistributionDashboard from "./pages/DistributionDashboard";

function App() {
  return (
    <Router>
      <Routes>
        {/* 🌍 Public Routes */}
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />

        {/* 🔒 Authenticated Routes */}
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/monitor" element={<Monitor />} />

        {/* 💧 Distribution Module */}
        {/* Redirect /distribution → /distribution/dashboard */}
        <Route
          path="/distribution"
          element={<Navigate to="/distribution/dashboard" replace />}
        />

        <Route
          path="/distribution/dashboard"
          element={<DistributionDashboard />}
        />

        {/* 🚫 404 Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}

export default App;
