from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# --- CORS (обязательно для Mini App) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # для начала разрешаем всё
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Проверка, что API жив ---
@app.get("/")
def root():
    return {"status": "API is running"}

# --- Добавить расход ---
@app.post("/expense")
def add_expense(data: dict):
    print("EXPENSE:", data)
    return {
        "ok": True,
        "message": "Расход добавлен",
        "data": data
    }

# --- Добавить доход ---
@app.post("/income")
def add_income(data: dict):
    print("INCOME:", data)
    return {
        "ok": True,
        "message": "Доход добавлен",
        "data": data
    }



