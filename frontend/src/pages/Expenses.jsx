import { useEffect, useState } from "react";
import { getExpenses } from "../api/api";

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
// 📂 CONSTANTS (MATCH STREAMLIT)
// ==============================
const EXPENSE_CATEGORIES = [
  "Grocery/Utilities", "Credit Cards", "India", "Transport",
  "Foodgasm", "Wants/Need", "Entertainment", "Emergency",
  "Invest", "Savings", "Travel", "Gifts", "Others"
];

const RECURRING_CATEGORIES = [
  "Rent", "Transport", "Internet", "Mobile charges",
  "Electricity", "Insurance", "Scalable Savings", "Other"
];

const PAYMENT_METHODS = [
  "Cash", "Bank Transfer", "N26 V", "N26 R",
  "Edenred", "Amex", "Gebührenfrei", "Trade Republic"
];

export default function Expenses() {

  const months = generateMonths();

  // ==============================
  // 🔥 STATE
  // ==============================
  const [month, setMonth] = useState(months[months.length - 2]);
  const [data, setData] = useState([]);
  const [editedData, setEditedData] = useState([]);

  const [tab, setTab] = useState("Variable");

  const [category, setCategory] = useState("");
  const [name, setName] = useState("");
  const [payment, setPayment] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  const [sortField, setSortField] = useState("amount"); // "amount" | "date"
  const [sortAsc, setSortAsc] = useState(true);

  const [newItem, setNewItem] = useState({
    date: "",
    name: "",
    category: "",
    amount: "",
    payment_method: ""
  });

  // ==============================
  // 🔄 FETCH
  // ==============================
  useEffect(() => {
    getExpenses(month)
      .then((res) => {
        const safe = Array.isArray(res) ? res : [];
        setData(safe);
        setEditedData(safe);
      })
      .catch((err) => {
        console.error("Expense fetch failed:", err);
        setData([]);
        setEditedData([]);
      });
  }, [month]);

  // ==============================
  // 🧠 CATEGORY SWITCH
  // ==============================
  const CATEGORY_OPTIONS =
    tab === "Variable"
      ? EXPENSE_CATEGORIES
      : RECURRING_CATEGORIES;

  // ==============================
  // ➕ ADD
  // ==============================
  const handleAddExpense = async () => {
    const token = localStorage.getItem("token");

    if (!newItem.date || !newItem.name || !newItem.amount) {
      alert("Fill required fields");
      return;
    }

    try {
      const res = await fetch(`${API_URL}/expenses`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          ...newItem,
          amount: Number(newItem.amount),
          expense_type: tab
        })
      });

      if (!res.ok) throw new Error("Failed");

      const updated = await getExpenses(month);
      setData(updated);
      setEditedData(updated);

      setNewItem({
        date: "",
        name: "",
        category: "",
        amount: "",
        payment_method: ""
      });

    } catch (err) {
      console.error(err);
      alert("Error adding expense");
    }
  };

  // ==============================
  // SPLIT DATA
  // ==============================
  const variableData = editedData.filter(i => i.expense_type === "Variable");
  const recurringData = editedData.filter(i => i.expense_type === "Recurring");

  const baseData = tab === "Variable" ? variableData : recurringData;

  // ==============================
  // FILTER + SORT
  // ==============================
  const filteredData = baseData
    .filter((item) => {
      const itemDate = item.date?.split("T")[0];

      return (
        (category ? item.category === category : true) &&
        (name ? item.name === name : true) &&
        (payment ? item.payment_method === payment : true) &&
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
  // SAVE
  // ==============================
  const handleSave = async () => {
    const token = localStorage.getItem("token");

    for (const item of editedData) {
      await fetch(`${API_URL}/expenses/${item.id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          ...item,
          amount: Number(item.amount),
          expense_type: item.expense_type
        })
      });
    }

    const refreshed = await getExpenses(month);
    setData(refreshed);
    setEditedData(refreshed);
  };

  // ==============================
  // DELETE
  // ==============================
  const handleDelete = async () => {
    const token = localStorage.getItem("token");

    for (const item of editedData.filter(i => i.Delete)) {
      await fetch(`${API_URL}/expenses/${item.id}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
    }

    const refreshed = await getExpenses(month);
    setData(refreshed);
    setEditedData(refreshed);
  };

  // ==============================
  // UI
  // ==============================
  return (
    <div className="card">

      <h2>🧾 Expenses</h2>

      {/* TABS */}
      <div style={{ marginBottom: "15px" }}>
        <button onClick={() => setTab("Variable")}>💸 Variable</button>
        <button onClick={() => setTab("Recurring")}>🔁 Recurring</button>
      </div>

      {/* ADD FORM */}
      <div className="card" style={{ marginBottom: "15px" }}>
        <h3>Add {tab} Expense</h3>

        <input type="date"
          value={newItem.date}
          onChange={(e) => setNewItem({ ...newItem, date: e.target.value })}
        />

        <input placeholder="Name"
          value={newItem.name}
          onChange={(e) => setNewItem({ ...newItem, name: e.target.value })}
        />

        <select value={newItem.category}
          onChange={(e) => setNewItem({ ...newItem, category: e.target.value })}
        >
          <option value="">Category</option>
          {CATEGORY_OPTIONS.map(c => <option key={c}>{c}</option>)}
        </select>

        <select value={newItem.payment_method}
          onChange={(e) => setNewItem({ ...newItem, payment_method: e.target.value })}
        >
          <option value="">Payment</option>
          {PAYMENT_METHODS.map(p => <option key={p}>{p}</option>)}
        </select>

        <input type="number"
          placeholder="Amount"
          value={newItem.amount}
          onChange={(e) => setNewItem({ ...newItem, amount: e.target.value })}
        />

        <button onClick={handleAddExpense}>Add</button>
      </div>

      {/* FILTERS */}
      <div className="filters">

        <select value={month} onChange={(e) => setMonth(e.target.value)}>
          {months.map(m => <option key={m}>{m}</option>)}
        </select>

        <select value={category} onChange={(e) => setCategory(e.target.value)}>
          <option value="">All Categories</option>
          {[...new Set(data.map(i => i.category))].map(c => <option key={c}>{c}</option>)}
        </select>

        <select value={name} onChange={(e) => setName(e.target.value)}>
          <option value="">All Names</option>
          {[...new Set(data.map(i => i.name))].map(n => <option key={n}>{n}</option>)}
        </select>

        <select value={payment} onChange={(e) => setPayment(e.target.value)}>
          <option value="">All Payments</option>
          {[...new Set(data.map(i => i.payment_method))].map(p => <option key={p}>{p}</option>)}
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
          setCategory(""); setName(""); setPayment(""); setStartDate(""); setEndDate("");
        }}>
          Reset
        </button>


      </div>

      {/* TABLE */}
      {filteredData.length === 0 ? (
        <p>No expenses found.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>Name</th>
              <th>Category</th>
              <th>Payment</th>
              <th>Amount</th>
              <th>Delete</th>
            </tr>
          </thead>

          <tbody>
            {filteredData.map(item => (
              <tr key={item.id}>

                <td>
                  <input type="date"
                    value={item.date?.split("T")[0]}
                    onChange={(e) => {
                      setEditedData(editedData.map(r =>
                        r.id === item.id ? { ...r, date: e.target.value } : r
                      ));
                    }}
                  />
                </td>

                <td>
                  <input value={item.name}
                    onChange={(e) => {
                      setEditedData(editedData.map(r =>
                        r.id === item.id ? { ...r, name: e.target.value } : r
                      ));
                    }}
                  />
                </td>

                <td>
                  <select value={item.category}
                    onChange={(e) => {
                      setEditedData(editedData.map(r =>
                        r.id === item.id ? { ...r, category: e.target.value } : r
                      ));
                    }}
                  >
                    {CATEGORY_OPTIONS.map(c => <option key={c}>{c}</option>)}
                  </select>
                </td>

                <td>
                  <select value={item.payment_method}
                    onChange={(e) => {
                      setEditedData(editedData.map(r =>
                        r.id === item.id ? { ...r, payment_method: e.target.value } : r
                      ));
                    }}
                  >
                    {PAYMENT_METHODS.map(p => <option key={p}>{p}</option>)}
                  </select>
                </td>

                <td>
                  <input type="number"
                    value={item.amount}
                    onChange={(e) => {
                      setEditedData(editedData.map(r =>
                        r.id === item.id ? { ...r, amount: e.target.value } : r
                      ));
                    }}
                  />
                </td>

                <td>
                  <input type="checkbox"
                    onChange={(e) => {
                      setEditedData(editedData.map(r =>
                        r.id === item.id ? { ...r, Delete: e.target.checked } : r
                      ));
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
        <button onClick={handleSave}>💾 Save</button>
        <button onClick={handleDelete}>🗑 Delete</button>
      </div>

    </div>
  );
}