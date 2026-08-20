from datetime import datetime, timedelta

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import database as db


async def check_reminders(bot: Bot):
    """Проверяет, какие напоминания пора отправить, и шлёт их."""
    now_iso = datetime.now().isoformat()
    due_tasks = await db.get_due_tasks(now_iso)

    for task in due_tasks:
        try:
            await bot.send_message(
                task["user_id"],
                f"⏰ Напоминание: {task['text']}"
            )
        except Exception as e:
            print(f"Не удалось отправить напоминание пользователю {task['user_id']}: {e}")

        # Если задача повторяющаяся — переносим дату на следующий раз
        if task["repeat"] == "daily":
            new_dt = datetime.fromisoformat(task["remind_at"]) + timedelta(days=1)
            await db.update_task_remind_at(task["id"], new_dt.isoformat())
        elif task["repeat"] == "weekly":
            new_dt = datetime.fromisoformat(task["remind_at"]) + timedelta(weeks=1)
            await db.update_task_remind_at(task["id"], new_dt.isoformat())
        else:
            # Одноразовая задача — отмечаем выполненной
            await db.mark_task_done(task["id"], task["user_id"])


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_reminders, "interval", seconds=30, args=[bot])
    return scheduler