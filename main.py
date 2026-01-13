from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import json

app = FastAPI()

# CORS (чтобы Mini App мог вызывать API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 📂 раздаём статические файлы
app.mount("/static", StaticFiles(directory="static"), name="static")


# 👉 Mini App
@app.get("/", response_class=HTMLResponse)
def mini_app():
    with open("static/index.html", encoding="utf-8") as f:
        return f.read()


# 👉 API
@app.post("/expense")
async def add_expense(data: dict):
    return {"ok": True, "type": "expense", "data": data}


@app.post("/income")
async def add_income(data: dict):
    return {"ok": True, "type": "income", "data": data}




