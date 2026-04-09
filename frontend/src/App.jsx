import { useState } from "react";
import Income from "./pages/Income";
import Expenses from "./pages/Expenses";
import Dashboard from "./pages/Dashboard";
import Budget from "./pages/Budget";

export default function App() {

  // ==============================
  // 🔐 AUTH STATE
  // ==============================
  const API_URL = "https://budget-expense-tracker-backend-0965.onrender.com";
  const [token, setToken] = useState(localStorage.getItem("token"));
  const [page, setPage] = useState("dashboard");

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  // ==============================
  // 🔐 LOGIN FUNCTION (🔥 YOU LOST THIS)
  // ==============================
  const handleLogin = async () => {
    try {
      const res = await fetch(`${API_URL}/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ username, password })
      });

      const data = await res.json();

      if (data.access_token) {
        localStorage.setItem("token", data.access_token);
        setToken(data.access_token);
      } else {
        alert("Login failed");
      }

    } catch (err) {
      console.error(err);
      alert("Login error");
    }
  };

  // ==============================
  // 🔓 LOGOUT
  // ==============================
  const handleLogout = () => {
    localStorage.removeItem("token");
    setToken(null);
  };

 // ==============================
// 🔐 LOGIN SCREEN (ONLY ONE!)
// ==============================
if (!token) {
  return (
    <form onSubmit={(e) => {
      e.preventDefault();
      handleLogin();
    }}>
      <h2>🔐 Login</h2>

      <input
        placeholder="Username"
        autoComplete="username"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
      />

      <br /><br />

      <input
        type="password"
        placeholder="Password"
        autoComplete="current-password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
      />

      <br /><br />

      <button type="submit">Login</button>
    </form>
  );
}

  // ==============================
  // 🧭 MAIN APP
  // ==============================
  return (
  <div style={{ display: "flex" }}>

    {/* SIDEBAR */}
    <div className="sidebar">
      <h3>🏠 Budget</h3>

      <p onClick={() => setPage("dashboard")}>📊 Dashboard</p>
      <p onClick={() => setPage("income")}>💰 Income</p>
      <p onClick={() => setPage("expenses")}>🧾 Expenses</p>
      <p onClick={() => setPage("budget")}>🎯 Budget</p>

      <br />
      <button onClick={handleLogout}>Logout</button>
    </div>

    {/* MAIN */}
    <div className="main">

      {page === "dashboard" && <Dashboard />}
      {page === "income" && <Income />}
      {page === "expenses" && <Expenses />}
      {page === "budget" && <Budget />}

    </div>

  </div>
);
}