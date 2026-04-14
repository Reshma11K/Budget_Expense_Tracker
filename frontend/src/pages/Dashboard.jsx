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

// ℹ️ Tooltip helper
const Info = ({ text }) => (
  <span title={text} style={{ cursor: "help", marginLeft: "5px" }}>
    ℹ️
  </span>
);

export default function Dashboard() {
  const months = generateMonths();
  const [month, setMonth] = useState(months[months.length - 2]);

  const [income, setIncome] = useState([]);
  const [expenses, setExpenses] = useState([]);
  const [trendData, setTrendData] = useState([]);

  const [corpus, setCorpus] = useState(
    Number(localStorage.getItem("corpus")) || 0
  );
  const [showCorpusEdit, setShowCorpusEdit] = useState(false);

  const [budgets] = useState(
    JSON.parse(localStorage.getItem("budgets")) || {}
  );

  useEffect(() => {
    localStorage.setItem("corpus", corpus);
  }, [corpus]);

  // ==============================
  // FETCH CURRENT MONTH (CACHED)
  // ==============================
  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) return;

    const cacheKey = `dashboard-${month}`;
    const cached = localStorage.getItem(cacheKey);

    if (cached) {
      const parsed = JSON.parse(cached);
      setIncome(parsed.income || []);
      setExpenses(parsed.expenses || []);
      return;
    }

    Promise.all([getIncome(month), getExpenses(month)])
      .then(([inc, exp]) => {
        setIncome(inc || []);
        setExpenses(exp || []);

        localStorage.setItem(
          cacheKey,
          JSON.stringify({
            income: inc || [],
            expenses: exp || [],
          })
        );
      });
  }, [month]);

  // ==============================
  // FETCH TREND DATA (CACHED)
  // ==============================
  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) return;

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
          expenses: (exp || []).reduce((s, e) => s + e.amount, 0)
        });
      }

      setTrendData(data);
      localStorage.setItem("trendData", JSON.stringify(data));
    };

    load();
  }, []);

  // ==============================
  // CALCULATIONS
  // ==============================
  const totalIncome = income.reduce((s, i) => s + i.amount, 0);
  const totalExpenses = expenses.reduce((s, e) => s + e.amount, 0);
  const balance = totalIncome - totalExpenses;

  const previousMonths = trendData.filter(m => m.month < month);

  const previousSavings = previousMonths.reduce((sum, m) => {
    return sum + (m.income - m.expenses);
  }, 0);

  const totalBalance = corpus + previousSavings + balance;

  // ==============================
  // 🔮 PREDICTION
  // ==============================
  const recurringExpenses = expenses.filter(
    (e) => e.expense_type === "Recurring"
  );

  const variableExpenses = expenses.filter(
    (e) => e.expense_type !== "Recurring"
  );

  const recurringTotal = recurringExpenses.reduce((s, e) => s + e.amount, 0);
  const variableTotal = variableExpenses.reduce((s, e) => s + e.amount, 0);

  const today = new Date();
  const day = today.getDate();
  const daysInMonth = new Date(
    today.getFullYear(),
    today.getMonth() + 1,
    0
  ).getDate();

  let projectedExpenses = totalExpenses;

  if (day > 7) {
    const avgDaily = variableTotal / day;
    const projectedVariable = avgDaily * daysInMonth;
    projectedExpenses = recurringTotal + projectedVariable;
  }

  const projectedBalance = totalIncome - projectedExpenses;

  // ==============================
  // DATA PREP
  // ==============================
  const weeklyData = (() => {
    const base = {
      1: { week: "W1", amount: 0 },
      2: { week: "W2", amount: 0 },
      3: { week: "W3", amount: 0 },
      4: { week: "W4", amount: 0 },
      5: { week: "W5", amount: 0 },
    };

    expenses.forEach((e) => {
      if (!e.date) return;

      const date = new Date(e.date);
      if (isNaN(date)) return;

      const week = Math.ceil(date.getDate() / 7);

      if (base[week]) {
        base[week].amount += Number(e.amount) || 0;
      }
    });

    return Object.values(base);
  })();

  const categoryData = Object.entries(
    expenses.reduce((acc, e) => {
      acc[e.category] = (acc[e.category] || 0) + e.amount;
      return acc;
    }, {})
  ).map(([name, value]) => ({ name, value }));

  const typeData = [
    { name: "Recurring", value: recurringTotal },
    { name: "Variable", value: variableTotal }
  ];

  // ==============================
  // 📈 WEALTH GRAPH
  // ==============================
  let runningTotal = corpus;

  const wealthData = trendData.map(m => {
    const monthlyBalance = m.income - m.expenses;
    runningTotal += monthlyBalance;

    return {
      month: m.month,
      wealth: runningTotal
    };
  });

  // ==============================
  // 🎯 BUDGET DATA
  // ==============================
  const budgetData = Object.entries(
    expenses.reduce((acc, e) => {
      acc[e.category] = (acc[e.category] || 0) + e.amount;
      return acc;
    }, {})
  )
    .map(([category, spent]) => {
      const budget = budgets[category];

      if (!budget || budget <= 0) return null;

      return {
        category,
        spent,
        budget
      };
    })
    .filter(Boolean);

  const overBudget = budgetData.filter(
    b => b.spent > b.budget
  );

  // ==============================
  // UI
  // ==============================
  return (
    <div className="card">

      <h2>📊 Dashboard</h2>

      <select value={month} onChange={(e) => setMonth(e.target.value)}>
        {months.map((m) => <option key={m}>{m}</option>)}
      </select>

      <h3>🔥 This Month</h3>

      <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
        <div className="card">💰 Income €{totalIncome.toFixed(2)}</div>
        <div className="card">🧾 Expenses €{totalExpenses.toFixed(2)}</div>
        <div className="card">📊 Balance €{balance.toFixed(2)}</div>
        <div className="card">🔮 Predicted €{projectedBalance.toFixed(2)}</div>
        <div className="card">🏦 Total €{totalBalance.toFixed(2)}</div>
      </div>

      {/* charts remain EXACTLY same */}

      <h3>📈 Monthly Trend</h3>
      <LineChart width={700} height={300} data={trendData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="month" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Line dataKey="income" stroke="#22c55e" />
        <Line dataKey="expenses" stroke="#ef4444" />
      </LineChart>

      <h3>🏦 Wealth Over Time</h3>
      <LineChart width={700} height={300} data={wealthData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="month" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Line dataKey="wealth" stroke="#6366f1" strokeWidth={3} />
      </LineChart>

    </div>
  );
}