import { useEffect, useState } from "react";
import { getExpenses } from "../api/api";
import { getBudgets } from "../api/api";

// ==============================
// 📅 Month Generator
// ==============================
function generateMonths() {
  const today = new Date();
  const year = today.getFullYear();
  const month = today.getMonth() + 1;

  let months = [];

  for (let i = 1; i <= month; i++) {
    months.push(`${year}-${String(i).padStart(2, "0")}`);
  }

  if (month < 12) {
    months.push(`${year}-${String(month + 1).padStart(2, "0")}`);
  }

  return months;
}

export default function Budget() {
  const months = generateMonths();

  const [month, setMonth] = useState(months[months.length - 2]);
  const [expenses, setExpenses] = useState([]);
  const [budgets, setBudgets] = useState({});

  // ==============================
  // FETCH EXPENSES
  // ==============================
  useEffect(() => {
    getExpenses(month)
      .then((res) => setExpenses(res || []))
      .catch(() => setExpenses([]));
  }, [month]);

 // FETCH BUDGETS
    useEffect(() => {
      getBudgets(month)
        .then((res) => {
          const mapped = {};
          res.forEach((b) => {
            mapped[b.category] = b.budget;
          });
          setBudgets(mapped);
        })
        .catch(() => setBudgets({}));
    }, [month]);
  // ==============================
  // SAVE BUDGETS
  // ==============================
  useEffect(() => {
    localStorage.setItem("budgets", JSON.stringify(budgets));
  }, [budgets]);

  // ==============================
  // CATEGORY TOTALS
  // ==============================
  const categoryTotals = expenses.reduce((acc, e) => {
    acc[e.category] = (acc[e.category] || 0) + e.amount;
    return acc;
  }, {});

  const categories = Object.keys(categoryTotals);

  return (
    <div className="card">

      <h2>🎯 Budget</h2>

      {/* MONTH */}
      <select value={month} onChange={(e) => setMonth(e.target.value)}>
        {months.map((m) => <option key={m}>{m}</option>)}
      </select>

      <table style={{ marginTop: "20px" }} border="1" cellPadding="10">
        <thead>
          <tr>
            <th>Category</th>
            <th>Budget (€)</th>
            <th>Spent (€)</th>
            <th>Status</th>
          </tr>
        </thead>

        <tbody>
          {categories.map((cat) => {
            const spent = categoryTotals[cat] || 0;
            const budget = budgets[cat] || 0;

            const isOver = spent > budget;

            return (
              <tr key={cat}>
                <td>{cat}</td>

                <td>
                  <input
                    type="number"
                    value={budget}
                    onChange={(e) =>
                      setBudgets({
                        ...budgets,
                        [cat]: Number(e.target.value)
                      })
                    }
                    style={{ width: "80px" }}
                  />
                </td>

                <td>€{spent.toFixed(2)}</td>

                <td style={{
                  color: isOver ? "red" : "green",
                  fontWeight: "bold"
                }}>
                  {budget === 0
                    ? "—"
                    : isOver
                      ? "Over"
                      : "OK"}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>

    </div>
  );
}