from datetime import datetime, timedelta

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

import database as db
from keyboards import expense_categories_kb, stats_period_kb

router = Router()


class NewExpense(StatesGroup):
    waiting_amount = State()
    waiting_category = State()


# ---------- Добавление расхода ----------

@router.message(F.text.in_({"➕ Новый расход", "/spend"}))
async def new_expense_start(message: Message, state: FSMContext):
    await state.set_state(NewExpense.waiting_amount)
    await message.answer("Сколько потратила? Введи сумму числом (например: 350)")


@router.message(NewExpense.waiting_amount)
async def new_expense_amount(message: Message, state: FSMContext):
    text = message.text.strip().replace(",", ".")
    try:
        amount = float(text)
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("Введи корректное положительное число, например: 350 или 199.90")
        return

    await state.update_data(amount=amount)
    await state.set_state(NewExpense.waiting_category)
    await message.answer("Выбери категорию:", reply_markup=expense_categories_kb())


@router.callback_query(NewExpense.waiting_category, F.data.startswith("cat_"))
async def new_expense_category(callback: CallbackQuery, state: FSMContext):
    category = callback.data[len("cat_"):]
    data = await state.get_data()

    await db.add_expense(callback.from_user.id, data["amount"], category)
    await state.clear()

    await callback.message.edit_text(f"✅ Записано: {data['amount']:.2f} — {category}")
    await callback.answer()


# ---------- Статистика ----------

@router.message(F.text.in_({"📊 Статистика", "/stats"}))
async def stats_start(message: Message):
    await message.answer("За какой период показать статистику?", reply_markup=stats_period_kb())


@router.callback_query(F.data.startswith("stats_"))
async def show_stats(callback: CallbackQuery):
    period = callback.data[len("stats_"):]

    date_from = None
    period_text = "за всё время"
    now = datetime.now()
    if period == "today":
        date_from = now.replace(hour=0, minute=0, second=0).isoformat()
        period_text = "за сегодня"
    elif period == "week":
        date_from = (now - timedelta(days=7)).isoformat()
        period_text = "за последние 7 дней"
    elif period == "month":
        date_from = (now - timedelta(days=30)).isoformat()
        period_text = "за последние 30 дней"

    by_category, total = await db.get_expense_stats(callback.from_user.id, date_from)

    if not by_category:
        await callback.message.edit_text(f"Нет расходов {period_text} 🎉")
        await callback.answer()
        return

    lines = [f"📊 Статистика {period_text}:\n"]
    for row in by_category:
        percent = (row["total"] / total * 100) if total else 0
        lines.append(f"{row['category']}: {row['total']:.2f} ({percent:.0f}%)")
    lines.append(f"\n💰 Итого: {total:.2f}")

    await callback.message.edit_text("\n".join(lines))
    await callback.answer()


# ---------- Список последних расходов ----------

@router.message(F.text.in_({"💰 Расходы"}))
async def list_expenses(message: Message):
    expenses = await db.get_expenses(message.from_user.id)

    if not expenses:
        await message.answer("Расходов пока нет. Добавь через «➕ Новый расход»")
        return

    lines = ["💰 Последние расходы:\n"]
    for exp in expenses[:15]:
        dt = datetime.fromisoformat(exp["created_at"])
        lines.append(f"{dt.strftime('%d.%m %H:%M')} — {exp['amount']:.2f} — {exp['category']}")

    await message.answer("\n".join(lines))