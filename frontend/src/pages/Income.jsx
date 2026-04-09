import { useEffect, useState } from "react";
import { getIncome } from "../api/api";

// ==============================
// 📅 Month Generator
// ==============================
function generateMonths() {
  const today = new Date();
  const year = today.getFullYear();
  const month = today.getMonth() + 1;

  let months = [];

  for (let i = 1; i <= month; i++) {
    const m = String(i).padStart(2, "0");
    months.push(`${year}-${m}`);
  }

  const nextMonth = month + 1;
  if (nextMonth <= 12) {
    months.push(`${year}-${String(nextMonth).padStart(2, "0")}`);
  }

  return months;
}

// ==============================
// 📂 CONSTANTS
// ==============================
const INCOME_CATEGORIES = [
  "Salary", "Bonus", "Edenred", "Investments", "Other"
];

export default function Income() {

  const months = generateMonths();

  // ==============================
  // 🔥 STATE
  // ==============================
  const [month, setMonth] = useState(months[months.length - 2]);
  const [data, setData] = useState([]);
  const [editedData, setEditedData] = useState([]);

  const [category, setCategory] = useState("");
  const [source, setSource] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  const [sortField, setSortField] = useState("amount"); // "amount" | "date"
  const [sortAsc, setSortAsc] = useState(true);

  const [newItem, setNewItem] = useState({
    date: "",
    source: "",
    category: "",
    amount: ""
  });

  // ==============================
  // 🔄 FETCH
  // ==============================
  useEffect(() => {
    getIncome(month)
      .then((res) => {
        const safe = Array.isArray(res) ? res : [];
        setData(safe);
        setEditedData(safe);
      })
      .catch((err) => {
        console.error("Income fetch failed:", err);
        setData([]);
        setEditedData([]);
      });
  }, [month]);

  // ==============================
  // ➕ ADD
  // ==============================
  const handleAddIncome = async () => {
    if (!newItem.date || !newItem.source || !newItem.amount) {
      alert("Fill required fields");
      return;
    }

    const token = localStorage.getItem("token");

    try {
      const res = await fetch(`${API_URL}/income`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          ...newItem,
          amount: Number(newItem.amount),
          income_type: "One-time"
        })
      });

      if (!res.ok) throw new Error("Failed");

      const updated = await getIncome(month);
      setData(updated);
      setEditedData(updated);

      setNewItem({
        date: "",
        source: "",
        category: "",
        amount: ""
      });

    } catch (err) {
      console.error(err);
      alert("Error adding income");
    }
  };

  // ==============================
  // 🧠 FILTER + SORT
  // ==============================
  const filteredData = editedData
    .filter((item) => {
      const itemDate = item.date?.split("T")[0];

      return (
        (category ? item.category === category : true) &&
        (source ? item.source === source : true) &&
        (startDate ? itemDate >= startDate : true) &&
        (endDate ? itemDate <= endDate : true)
      );
    })
    .sort((a, b) => {
        if (sortField === "amount") {
            return sortAsc ? a.amount - b.amount : b.amount - a.amount;
        }

        if (sortField === "date") {
            return sortAsc
                ? new Date(a.date) - new Date(b.date)
                : new Date(b.date) - new Date(a.date);
        }

        return 0;
    });

  // ==============================
  // 💾 SAVE
  // ==============================
  const handleSave = async () => {
    const token = localStorage.getItem("token");

    for (const item of editedData) {
      await fetch(`${API_URL}/income/${item.id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          ...item,
          amount: Number(item.amount),
          income_type: "One-time"
        })
      });
    }

    const refreshed = await getIncome(month);
    setData(refreshed);
    setEditedData(refreshed);
  };

  // ==============================
  // 🗑 DELETE
  // ==============================
  const handleDelete = async () => {
    const token = localStorage.getItem("token");

    for (const item of editedData.filter(i => i.Delete)) {
      await fetch(`${API_URL}/income/${item.id}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
    }

    const refreshed = await getIncome(month);
    setData(refreshed);
    setEditedData(refreshed);
  };

  // ==============================
  // 🎨 UI
  // ==============================
  return (
    <div className="card">

      <h2>💰 Income</h2>

      {/* ➕ ADD FORM */}
      <div className="card" style={{ marginBottom: "15px" }}>
        <h3>Add Income</h3>

        <input
          type="date"
          value={newItem.date}
          onChange={(e) =>
            setNewItem({ ...newItem, date: e.target.value })
          }
        />

        <input
          placeholder="Source"
          value={newItem.source}
          onChange={(e) =>
            setNewItem({ ...newItem, source: e.target.value })
          }
        />

        <select
          value={newItem.category}
          onChange={(e) =>
            setNewItem({ ...newItem, category: e.target.value })
          }
        >
          <option value="">Select Category</option>
          {INCOME_CATEGORIES.map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>

        <input
          type="number"
          placeholder="Amount"
          value={newItem.amount}
          onChange={(e) =>
            setNewItem({ ...newItem, amount: e.target.value })
          }
        />

        <button onClick={handleAddIncome}>Add</button>
      </div>

      {/* FILTERS */}
      <div className="filters">

        <select value={month} onChange={(e) => setMonth(e.target.value)}>
          {months.map((m) => (
            <option key={m}>{m}</option>
          ))}
        </select>

        <select value={category} onChange={(e) => setCategory(e.target.value)}>
          <option value="">All Categories</option>
          {[...new Set(data.map((i) => i.category))].map((c) => (
            <option key={c}>{c}</option>
          ))}
        </select>

        <select value={source} onChange={(e) => setSource(e.target.value)}>
          <option value="">All Sources</option>
          {[...new Set(data.map((i) => i.source))].map((s) => (
            <option key={s}>{s}</option>
          ))}
        </select>

        <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
        <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} />

        <select value={sortField} onChange={(e) => setSortField(e.target.value)}>
            <option value="amount">Sort by Amount</option>
            <option value="date">Sort by Date</option>
        </select>

        <button onClick={() => setSortAsc(!sortAsc)}>
          {sortAsc ? "⬆️ Asc" : "⬇️ Desc"}
        </button>

        <button onClick={() => {
          setCategory("");
          setSource("");
          setStartDate("");
          setEndDate("");
        }}>
          Reset
        </button>


      </div>

      {/* TABLE */}
      {filteredData.length === 0 ? (
        <p style={{ marginTop: "15px", color: "#9ca3af" }}>
          No income data found.
        </p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>Source</th>
              <th>Category</th>
              <th>Amount</th>
              <th>Delete</th>
            </tr>
          </thead>

          <tbody>
            {filteredData.map((item) => (
              <tr key={item.id}>

                <td>
                  <input
                    type="date"
                    value={item.date?.split("T")[0]}
                    onChange={(e) => {
                      const updated = editedData.map((row) =>
                        row.id === item.id
                          ? { ...row, date: e.target.value }
                          : row
                      );
                      setEditedData(updated);
                    }}
                  />
                </td>

                <td>
                  <input
                    value={item.source}
                    onChange={(e) => {
                      const updated = editedData.map((row) =>
                        row.id === item.id
                          ? { ...row, source: e.target.value }
                          : row
                      );
                      setEditedData(updated);
                    }}
                  />
                </td>

                <td>
                  <select
                    value={item.category}
                    onChange={(e) => {
                      const updated = editedData.map((row) =>
                        row.id === item.id
                          ? { ...row, category: e.target.value }
                          : row
                      );
                      setEditedData(updated);
                    }}
                  >
                    {INCOME_CATEGORIES.map((c) => (
                      <option key={c}>{c}</option>
                    ))}
                  </select>
                </td>

                <td>
                  <input
                    type="number"
                    value={item.amount}
                    onChange={(e) => {
                      const updated = editedData.map((row) =>
                        row.id === item.id
                          ? { ...row, amount: e.target.value }
                          : row
                      );
                      setEditedData(updated);
                    }}
                  />
                </td>

                <td>
                  <input
                    type="checkbox"
                    onChange={(e) => {
                      const updated = editedData.map((row) =>
                        row.id === item.id
                          ? { ...row, Delete: e.target.checked }
                          : row
                      );
                      setEditedData(updated);
                    }}
                  />
                </td>

              </tr>
            ))}
          </tbody>
        </table>
      )}

      {/* ACTIONS */}
      <div style={{ marginTop: "10px" }}>
        <button onClick={handleSave}>💾 Save Changes</button>
        <button onClick={handleDelete}>🗑 Delete Selected</button>
      </div>

    </div>
  );
}