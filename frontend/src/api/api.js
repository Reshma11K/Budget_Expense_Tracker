const API_URL = import.meta.env.VITE_API_URL;
//const API_URL = "http://127.0.0.1:8000";

// ==============================
// 💰 GET INCOME
// ==============================
export async function getIncome(month) {
  const token = localStorage.getItem("token");

  if (!token) {
    throw new Error("No token found");
  }

  console.log("TOKEN SENT:", token);

  const res = await fetch(
    `${API_URL}/income?month=${month}`,
    {
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json"
      },
    }
  );

  if (res.status === 401) {
    localStorage.removeItem("token");
    window.location.reload();
    throw new Error("Unauthorized");
  }

  return await res.json();
}

// ==============================
// 🔐 LOGIN
// ==============================
export async function login(username, password) {
  const res = await fetch(`${API_URL}/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ username, password })
  });

  return res.json();
}

// ==============================
// 🧾 GET EXPENSES
// ==============================
export async function getExpenses(month) {
  const token = localStorage.getItem("token");

  if (!token) {
    throw new Error("No token found");
  }

  console.log("TOKEN SENT:", token);

  const res = await fetch(
    `${API_URL}/expenses?month=${month}`,
    {
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json"
      },
    }
  );

  if (res.status === 401) {
    localStorage.removeItem("token");
    window.location.reload();
    throw new Error("Unauthorized");
  }

  return await res.json();
}