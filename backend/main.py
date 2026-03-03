from fastapi import FastAPI
from backend.services.income_service import get_all_income

app = FastAPI()


@app.get("/")
def root():
    return {"message": "Budget API is alive"}


@app.get("/income")
def get_income():
    df = get_all_income()
    return df.to_dict(orient="records")