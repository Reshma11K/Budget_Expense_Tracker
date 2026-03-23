from fastapi import FastAPI, Query
from backend.services.income_service import (
    get_all_income,
    add_income,
    delete_income,
)
from pydantic import BaseModel
from typing import Optional

from backend.services.expense_service import (
    get_all_expenses,
    add_expense,
    delete_expenses,
)

from backend.services.dashboard_service import get_dashboard_summary

app = FastAPI()

class IncomeCreate(BaseModel):
    date: str
    source: str
    category: str
    amount: float
    income_type: str

class ExpenseCreate(BaseModel):
    date: str
    name: str
    category: str
    amount: float
    payment_method: str
    expense_type: str

@app.get("/")
def root():
    return {"message": "Budget API is alive"}


@app.get("/income")
def get_income(month: Optional[str] = Query(None)):
    df = get_all_income()

    if month:
        df = df[df["Month"] == month]

    return df.to_dict(orient="records")


@app.post("/income")
def create_income(income: IncomeCreate):
    add_income(
        income.date,
        income.source,
        income.category,
        income.amount,
        income.income_type,
    )
    return {"status": "created"}


@app.delete("/income/{income_id}")
def remove_income(income_id: int):
    delete_income([income_id])
    return {"status": "deleted"}

@app.get("/expenses")
def get_expenses(month: Optional[str] = Query(None)):
    df = get_all_expenses()

    if month:
        df = df[df["Month"] == month]

    return df.to_dict(orient="records")

@app.post("/expenses")
def create_expense(expense: ExpenseCreate):
    add_expense(
        expense.date,
        expense.name,
        expense.category,
        expense.amount,
        expense.payment_method,
        expense.expense_type,
    )
    return {"status": "created"}

@app.delete("/expenses/{expense_id}")
def remove_expense(expense_id: int):
    delete_expenses([expense_id])
    return {"status": "deleted"}

@app.get("/dashboard-summary")
def dashboard_summary(month: str):
    return get_dashboard_summary(month)