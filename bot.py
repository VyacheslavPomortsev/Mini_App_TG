import os
import json
import sqlite3
from datetime import datetime, time

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# ================== НАСТРОЙКИ ==================

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise RuntimeError("❌ TELEGRAM_TOKEN не задан")

DB_NAME = "finance.db"
MINI_APP_URL = "https://vyacheslavpomortsev.github.io/finance-mini-app/"

CATEGORIES = {
    "food": "🍔 Еда",
    "transport": "🚕 Транспорт",
    "home": "🏠 Дом",
    "fun": "🎮 Развлечения",
    "other": "🧾 Прочее"
}

# ================== БАЗА ДАННЫХ ==================

def get_db():
    return sqlite3.connect(DB_NAME)

def init_db():
    with get_db() as conn:
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                created_at TEXT
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount INTEGER,
                category TEXT,
                created_at TEXT
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS incomes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount INTEGER,
                created_at TEXT
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS credits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT,
                amount INTEGER,
                pay_day INTEGER
            )
        """)

        conn.commit()

# ================== DB HELPERS ==================

def register_user(user_id: int):
    with get_db() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO users VALUES (?, ?)",
            (user_id, datetime.now().isoformat())
        )
        conn.commit()

def add_expense(user_id: int, amount: int, category: str):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO expenses VALUES (NULL, ?, ?, ?, ?)",
            (user_id, amount, category, datetime.now().isoformat())
        )
        conn.commit()

def add_income(user_id: int, amount: int):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO incomes VALUES (NULL, ?, ?, ?)",
            (user_id, amount, datetime.now().isoformat())
        )
        conn.commit()

def add_credit(user_id: int, name: str, amount: int, day: int):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO credits VALUES (NULL, ?, ?, ?, ?)",
            (user_id, name, amount, day)
        )
        conn.commit()

def delete_credit(user_id: int, name: str):
    with get_db() as conn:
        conn.execute(
            "DELETE FROM credits WHERE user_id = ? AND name = ?",
            (user_id, name)
        )
        conn.commit()

def get_credits(user_id: int):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT name, amount, pay_day FROM credits WHERE user_id = ?",
            (user_id,)
        )
        return cur.fetchall()

def sum_query(query, params):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        return cur.fetchone()[0] or 0

def get_incomes(user_id, days=None):
    q = "SELECT SUM(amount) FROM incomes WHERE user_id = ?"
    p = [user_id]
    if days:
        q += " AND DATE(created_at) >= DATE('now', ?)"
        p.append(f"-{days} days")
    return sum_query(q, p)

def get_expenses(user_id, days=None):
    q = "SELECT SUM(amount) FROM expenses WHERE user_id = ?"
    p = [user_id]
    if days:
        q += " AND DATE(created_at) >= DATE('now', ?)"
        p.append(f"-{days} days")
    return sum_query(q, p)

def get_expenses_by_category(user_id, days):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT category, SUM(amount)
            FROM expenses
            WHERE user_id = ?
              AND DATE(created_at) >= DATE('now', ?)
            GROUP BY category
        """, (user_id, f"-{days} days"))
        return cur.fetchall()

# ================== КНОПКИ ==================

def main_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "📊 Открыть приложение",
                web_app=WebAppInfo(url=MINI_APP_URL)
            )
        ],
        [
            InlineKeyboardButton("➕ Расход", callback_data="add"),
            InlineKeyboardButton("💰 Доход", callback_data="income")
        ],
        [
            InlineKeyboardButton("📊 Сегодня", callback_data="today"),
            InlineKeyboardButton("📅 Неделя", callback_data="week"),
            InlineKeyboardButton("📆 Месяц", callback_data="month")
        ],
        [
            InlineKeyboardButton("🏦 Кредиты", callback_data="credits")
        ]
    ])

def credits_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Добавить кредит", callback_data="credit_add")],
        [InlineKeyboardButton("🗑 Удалить кредит", callback_data="credit_delete")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back")]
    ])

# ================== HANDLERS ==================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    register_user(update.effective_user.id)
    await update.message.reply_text(
        "💰 *Финансовый помощник*\n\n"
        "Примеры:\n"
        "`500 еда`\n"
        "`5000 доход`\n"
        "`кредит ипотека 25000 15`",
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )

async def webapp_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = json.loads(update.message.web_app_data.data)
    if data["type"] == "expense":
        await update.message.reply_text("Введите расход:\n`500 еда`", parse_mode="Markdown")
    elif data["type"] == "income":
        await update.message.reply_text("Введите доход:\n`5000 доход`", parse_mode="Markdown")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id

    if q.data == "add":
        await q.message.reply_text("Введите расход:\n`500 еда`", parse_mode="Markdown")

    elif q.data == "income":
        await q.message.reply_text("Введите доход:\n`5000 доход`", parse_mode="Markdown")

    elif q.data in ("today", "week", "month"):
        days = {"today": 1, "week": 7, "month": 30}[q.data]
        inc = get_incomes(uid, days)
        exp = get_expenses(uid, days)
        bal = inc - exp
        sign = "🟢" if bal >= 0 else "🔴"

        text = (
            f"*Статистика*\n\n"
            f"💰 Доходы: {inc} ₽\n"
            f"💸 Расходы: {exp} ₽\n"
            f"{sign} Баланс: {bal} ₽\n\n"
        )

        cats = get_expenses_by_category(uid, days)
        for c, a in cats:
            text += f"{CATEGORIES.get(c, c)} — {a} ₽\n"

        await q.message.reply_text(text, parse_mode="Markdown", reply_markup=main_keyboard())

    elif q.data == "credits":
        credits = get_credits(uid)
        if not credits:
            await q.message.reply_text(
                "Кредитов нет",
                reply_markup=credits_keyboard()
            )
            return
        text = "*Ваши кредиты:*\n\n"
        for n, a, d in credits:
            text += f"{n}: {a} ₽, день {d}\n"
        await q.message.reply_text(text, parse_mode="Markdown", reply_markup=credits_keyboard())

    elif q.data == "credit_add":
        await q.message.reply_text(
            "`кредит <название> <сумма> <день>`",
            parse_mode="Markdown"
        )

    elif q.data == "credit_delete":
        await q.message.reply_text(
            "`удалить <название>`",
            parse_mode="Markdown"
        )

    elif q.data == "back":
        await q.message.reply_text("Главное меню", reply_markup=main_keyboard())

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.lower().split()

    if len(text) == 2 and text[1] == "доход":
        add_income(uid, int(text[0]))
        await update.message.reply_text("Доход добавлен", reply_markup=main_keyboard())
        return

    if len(text) == 2:
        amount, cat = text
        for k, v in CATEGORIES.items():
            if cat in v.lower():
                add_expense(uid, int(amount), k)
                await update.message.reply_text("Расход добавлен", reply_markup=main_keyboard())
                return

    if len(text) == 4 and text[0] == "кредит":
        _, name, amount, day = text
        add_credit(uid, name, int(amount), int(day))
        await update.message.reply_text("Кредит добавлен", reply_markup=main_keyboard())
        return

    if len(text) == 2 and text[0] == "удалить":
        delete_credit(uid, text[1])
        await update.message.reply_text("Кредит удалён", reply_markup=main_keyboard())

# ================== ЗАПУСК ==================

init_db()

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button_handler))
app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, webapp_handler))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

print("✅ Финансовый бот запущен")
app.run_polling()




