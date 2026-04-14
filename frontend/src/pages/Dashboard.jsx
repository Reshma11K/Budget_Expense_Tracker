import { useEffect, useState } from "react";
import { getIncome, getExpenses } from "../api/api";
import {
  PieChart, Pie, Cell, Tooltip,
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  LineChart, Line, Legend
} from "recharts";

// ==============================
// 📅 MONTH GENERATOR
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

const COLORS = ["#6366f1", "#22c55e", "#f59e0b", "#ef4444"];

export default function Dashboard() {
  const months = generateMonths();
  const [month, setMonth] = useState(months[months.length - 2]);

  const [income, setIncome] = useState([]);
  const [expenses, setExpenses] = useState([]);
  const [trendData, setTrendData] = useState([]);

  // ==============================
  // 💾 FETCH CURRENT MONTH (CACHED)
  // ==============================
  useEffect(() => {
    const cacheKey = `dashboard-${month}`;
    const cached = localStorage.getItem(cacheKey);

    if (cached) {
      const parsed = JSON.parse(cached);
      setIncome(parsed.income);
      setExpenses(parsed.expenses);
      return;
    }

    Promise.all([getIncome(month), getExpenses(month)])
      .then(([inc, exp]) => {
        setIncome(inc || []);
        setExpenses(exp || []);

        localStorage.setItem(
          cacheKey,
          JSON.stringify({
            income: inc,
            expenses: exp,
          })
        );
      });
  }, [month]);

  // ==============================
  // 📈 FETCH TREND DATA (CACHED)
  // ==============================
  useEffect(() => {
    const cached = localStorage.getItem("trendData");

    if (cached) {
      setTrendData(JSON.parse(cached));
      return;
    }

    const load = async () => {
      let data = [];

      for (let m of months) {
        const inc = await getIncome(m);
        const exp = await getExpenses(m);

        data.push({
          month: m,
          income: (inc || []).reduce((s, i) => s + i.amount, 0),
          expenses: (exp || []).reduce((s, e) => s + e.amount, 0),
        });
      }

      setTrendData(data);
      localStorage.setItem("trendData", JSON.stringify(data));
    };

    load();
  }, [month]);

  // ==============================
  // CALCULATIONS (UNCHANGED)
  // ==============================
  const totalIncome = income.reduce((s, i) => s + i.amount, 0);
  const totalExpenses = expenses.reduce((s, e) => s + e.amount, 0);
  const balance = totalIncome - totalExpenses;

  return (
    <div className="card">
      <h2>📊 Dashboard</h2>

      <select value={month} onChange={(e) => setMonth(e.target.value)}>
        {months.map((m) => (
          <option key={m}>{m}</option>
        ))}
      </select>

      <h3>🔥 This Month</h3>

      <p>💰 Income: €{totalIncome.toFixed(2)}</p>
      <p>🧾 Expenses: €{totalExpenses.toFixed(2)}</p>
      <p>📊 Balance: €{balance.toFixed(2)}</p>

      {/* SIMPLE TREND CHART */}
      <h3>📈 Monthly Trend</h3>
      <LineChart width={600} height={300} data={trendData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="month" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Line dataKey="income" stroke="#22c55e" />
        <Line dataKey="expenses" stroke="#ef4444" />
      </LineChart>
    </div>
  );
}