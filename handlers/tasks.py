from datetime import datetime

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

import database as db
from keyboards import main_menu, repeat_choice_kb, task_item_kb

router = Router()


class NewTask(StatesGroup):
    waiting_text = State()
    waiting_datetime = State()
    waiting_repeat = State()


# ---------- Создание задачи ----------

@router.message(F.text.in_({"➕ Новая задача", "/newtask"}))
async def new_task_start(message: Message, state: FSMContext):
    await state.set_state(NewTask.waiting_text)
    await message.answer(
        "О чём напомнить? Напиши текст задачи.\n"
        "(например: «Позвонить маме»)"
    )


@router.message(NewTask.waiting_text)
async def new_task_text(message: Message, state: FSMContext):
    await state.update_data(text=message.text)
    await state.set_state(NewTask.waiting_datetime)
    await message.answer(
        "Когда напомнить? Введи дату и время в формате:\n"
        "<code>ДД.ММ.ГГГГ ЧЧ:ММ</code>\n\n"
        "Например: <code>25.08.2026 18:30</code>\n\n"
        "Или напиши «без напоминания», если просто хочешь добавить в список задач.",
        parse_mode="HTML"
    )


@router.message(NewTask.waiting_datetime)
async def new_task_datetime(message: Message, state: FSMContext):
    text = message.text.strip().lower()

    if text == "без напоминания":
        await state.update_data(remind_at=None)
        data = await state.get_data()
        task_id = await db.add_task(message.from_user.id, data["text"], None, None)
        await state.clear()
        await message.answer(f"✅ Задача добавлена (без напоминания): «{data['text']}»", reply_markup=main_menu())
        return

    try:
        dt = datetime.strptime(text, "%d.%m.%Y %H:%M")
    except ValueError:
        await message.answer(
            "Не получилось распознать дату 😕\n"
            "Используй формат <code>ДД.ММ.ГГГГ ЧЧ:ММ</code>, например <code>25.08.2026 18:30</code>",
            parse_mode="HTML"
        )
        return

    if dt <= datetime.now():
        await message.answer("Эта дата уже прошла. Введи дату в будущем.")
        return

    await state.update_data(remind_at=dt.isoformat())
    await state.set_state(NewTask.waiting_repeat)
    await message.answer("Повторять напоминание?", reply_markup=repeat_choice_kb())


@router.callback_query(NewTask.waiting_repeat, F.data.startswith("repeat_"))
async def new_task_repeat(callback: CallbackQuery, state: FSMContext):
    repeat_map = {"repeat_none": None, "repeat_daily": "daily", "repeat_weekly": "weekly"}
    repeat = repeat_map[callback.data]

    data = await state.get_data()
    task_id = await db.add_task(callback.from_user.id, data["text"], data["remind_at"], repeat)
    await state.clear()

    dt = datetime.fromisoformat(data["remind_at"])
    repeat_text = {"daily": " (каждый день)", "weekly": " (каждую неделю)", None: ""}[repeat]

    await callback.message.edit_text(
        f"✅ Задача добавлена: «{data['text']}»\n"
        f"⏰ Напоминание: {dt.strftime('%d.%m.%Y %H:%M')}{repeat_text}"
    )
    await callback.answer()


# ---------- Список задач ----------

@router.message(F.text.in_({"📝 Задачи", "/tasks"}))
async def list_tasks(message: Message):
    tasks = await db.get_tasks(message.from_user.id)

    if not tasks:
        await message.answer("У тебя пока нет активных задач 🎉\nДобавь новую через «➕ Новая задача»")
        return

    await message.answer(f"📝 Твои активные задачи ({len(tasks)}):")
    for task in tasks:
        text = f"• {task['text']}"
        if task["remind_at"]:
            dt = datetime.fromisoformat(task["remind_at"])
            text += f"\n⏰ {dt.strftime('%d.%m.%Y %H:%M')}"
            if task["repeat"] == "daily":
                text += " (каждый день)"
            elif task["repeat"] == "weekly":
                text += " (каждую неделю)"
        await message.answer(text, reply_markup=task_item_kb(task["id"]))


@router.callback_query(F.data.startswith("task_done_"))
async def task_done(callback: CallbackQuery):
    task_id = int(callback.data.split("_")[-1])
    await db.mark_task_done(task_id, callback.from_user.id)
    await callback.message.edit_text(callback.message.text + "\n\n✅ Выполнено!")
    await callback.answer("Отмечено как выполненное 🎉")


@router.callback_query(F.data.startswith("task_del_"))
async def task_delete(callback: CallbackQuery):
    task_id = int(callback.data.split("_")[-1])
    await db.delete_task(task_id, callback.from_user.id)
    await callback.message.edit_text(callback.message.text + "\n\n🗑 Удалено")
    await callback.answer("Задача удалена")