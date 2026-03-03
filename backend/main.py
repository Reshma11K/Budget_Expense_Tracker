from fastapi import FastAPI, Query
from backend.services.income_service import (
    get_all_income,
    add_income,
    delete_income,
)
from pydantic import BaseModel
from typing import Optional

app = FastAPI()


class IncomeCreate(BaseModel):
    date: str
    source: str
    category: str
    amount: float
    income_type: str


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