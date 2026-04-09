from fastapi import FastAPI, Query, Depends
from fastapi.middleware.cors import CORSMiddleware

from dotenv import load_dotenv
import os

load_dotenv()

print("LOADED DB HOST:", os.getenv("DB_HOST"))

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
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://budget-expense-tracker-pi.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from backend.auth import create_token, verify_token

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


from backend.services.auth_service import authenticate_user

class LoginRequest(BaseModel):
    username: str
    password: str



@app.post("/login")
def login(data: LoginRequest):
    try:
        print("LOGIN ATTEMPT:", data.username)

        user = authenticate_user(data.username, data.password)

        print("USER RESULT:", user)

        if user:
            return {"access_token": create_token(user["username"])}

        return {"error": "Invalid credentials"}

    except Exception as e:
        print("🔥 LOGIN CRASH:", e)
        return {"error": str(e)}

from backend.services.auth_service import create_user

from pydantic import BaseModel

class RegisterRequest(BaseModel):
    username: str
    password: str


@app.post("/register")
def register(data: RegisterRequest):
    try:
        create_user(data.username, data.password)
        return {"status": "user created"}
    except Exception as e:
        return {"error": str(e)}  # show real error

@app.get("/income")
def get_income(month: Optional[str] = Query(None), user: str = Depends(verify_token)):
    df = get_all_income()

    if month:
        df = df[df["Month"] == month]

    return df.to_dict(orient="records")


@app.post("/income")
def create_income(income: IncomeCreate, user: str = Depends(verify_token)):
    add_income(
        income.date,
        income.source,
        income.category,
        income.amount,
        income.income_type,
    )
    return {"status": "created"}

@app.put("/income/{income_id}")
def update_income_api(income_id: int, income: IncomeCreate, user: str = Depends(verify_token)):
    from backend.services.income_service import update_income

    update_income(
        income_id,
        income.date,
        income.source,
        income.category,
        income.amount,
    )
    return {"status": "updated"}

@app.delete("/income/{income_id}")
def remove_income(income_id: int , user: str = Depends(verify_token)):
    delete_income([income_id])
    return {"status": "deleted"}

@app.get("/expenses")
def get_expenses(month: Optional[str] = Query(None),user: str = Depends(verify_token)):
    df = get_all_expenses()

    if month:
        df = df[df["Month"] == month]

    return df.to_dict(orient="records")

@app.post("/expenses")
def create_expense(expense: ExpenseCreate, user: str = Depends(verify_token)):
    add_expense(
        expense.date,
        expense.name,
        expense.category,
        expense.amount,
        expense.payment_method,
        expense.expense_type,
    )
    return {"status": "created"}

@app.put("/expenses/{expense_id}")
def update_expense_api(expense_id: int, expense: ExpenseCreate , user: str = Depends(verify_token)):
    from backend.services.expense_service import update_expense

    update_expense(
        expense_id,
        expense.date,
        expense.name,
        expense.category,
        expense.amount,
        expense.payment_method,
    )
    return {"status": "updated"}

@app.delete("/expenses/{expense_id}")
def remove_expense(expense_id: int, user: str = Depends(verify_token)):
    delete_expenses([expense_id])
    return {"status": "deleted"}

@app.get("/dashboard-summary")
def dashboard_summary(month: str , user: str = Depends(verify_token)):
    return get_dashboard_summary(month)