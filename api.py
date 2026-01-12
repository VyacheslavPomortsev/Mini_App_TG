from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# 🔓 CORS (ОЧЕНЬ ВАЖНО для Mini App)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # позже можно ограничить
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== MODELS =====

class Expense(BaseModel):
    amount: int
    category: str

class Income(BaseModel):
    amount: int

# ===== ROUTES =====

@app.get("/")
def root():
    return {"status": "ok"}

@app.post("/expense")
def add_expense(expense: Expense):
    return {
        "message": "Расход добавлен",
        "amount": expense.amount,
        "category": expense.category
    }

@app.post("/income")
def add_income(income: Income):
    return {
        "message": "Доход добавлен",
        "amount": income.amount
    }



