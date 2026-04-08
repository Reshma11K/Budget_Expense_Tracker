const API_URL = "http://127.0.0.1:8000";

export async function getIncome(month) {
  const token = localStorage.getItem("token");

  const res = await fetch(
    `http://127.0.0.1:8000/income?month=${month}`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  if (res.status === 401) {
    // 💥 AUTO RESET BAD TOKEN
    localStorage.removeItem("token");
    window.location.reload(); // forces login screen
    throw new Error("Unauthorized");
  }

  return await res.json();
}

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

export async function getExpenses(month) {
  const token = localStorage.getItem("token");

  const res = await fetch(
    `http://127.0.0.1:8000/expenses?month=${month}`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
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