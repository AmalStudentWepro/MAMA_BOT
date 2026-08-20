from datetime import datetime

import aiosqlite

DB_PATH = "bot.db"


async def init_db():
    """Создаёт таблицы, если их ещё нет."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                remind_at TEXT,           -- дата/время следующего напоминания (ISO)
                repeat TEXT DEFAULT NULL, -- 'daily', 'weekly' или NULL
                done INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                note TEXT,
                created_at TEXT NOT NULL
            )
        """)
        await db.commit()


# ---------- ЗАДАЧИ ----------

async def add_task(user_id: int, text: str, remind_at: str | None, repeat: str | None):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "INSERT INTO tasks (user_id, text, remind_at, repeat, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, text, remind_at, repeat, datetime.now().isoformat())
        )
        await db.commit()
        return cur.lastrowid


async def get_tasks(user_id: int, only_active: bool = True):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        query = "SELECT * FROM tasks WHERE user_id = ?"
        if only_active:
            query += " AND done = 0"
        query += " ORDER BY remind_at IS NULL, remind_at ASC"
        cur = await db.execute(query, (user_id,))
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def mark_task_done(task_id: int, user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE tasks SET done = 1 WHERE id = ? AND user_id = ?",
            (task_id, user_id)
        )
        await db.commit()


async def delete_task(task_id: int, user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM tasks WHERE id = ? AND user_id = ?",
            (task_id, user_id)
        )
        await db.commit()


async def get_due_tasks(now_iso: str):
    """Задачи, время напоминания которых уже наступило (для планировщика)."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM tasks WHERE done = 0 AND remind_at IS NOT NULL AND remind_at <= ?",
            (now_iso,)
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def update_task_remind_at(task_id: int, new_remind_at: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE tasks SET remind_at = ? WHERE id = ?",
            (new_remind_at, task_id)
        )
        await db.commit()


# ---------- РАСХОДЫ ----------

async def add_expense(user_id: int, amount: float, category: str, note: str | None = None):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "INSERT INTO expenses (user_id, amount, category, note, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, amount, category, note, datetime.now().isoformat())
        )
        await db.commit()
        return cur.lastrowid


async def get_expenses(user_id: int, date_from: str | None = None):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        query = "SELECT * FROM expenses WHERE user_id = ?"
        params = [user_id]
        if date_from:
            query += " AND created_at >= ?"
            params.append(date_from)
        query += " ORDER BY created_at DESC"
        cur = await db.execute(query, params)
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def get_expense_stats(user_id: int, date_from: str | None = None):
    """Возвращает список (категория, сумма) и общую сумму."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        query = "SELECT category, SUM(amount) as total FROM expenses WHERE user_id = ?"
        params = [user_id]
        if date_from:
            query += " AND created_at >= ?"
            params.append(date_from)
        query += " GROUP BY category ORDER BY total DESC"
        cur = await db.execute(query, params)
        rows = await cur.fetchall()
        by_category = [dict(r) for r in rows]
        total = sum(r["total"] for r in by_category)
        return by_category, total