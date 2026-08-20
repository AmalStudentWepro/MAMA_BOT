from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from keyboards import main_menu

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "Привет! Я личный помощник🤖 Динары\n\n"
        "Я умею:\n"
        "📝 Напоминать о задачах и делах\n"
        "💰 Считать твои расходы\n\n"
        "Выбирай действие на панеле ниже 👇",
        reply_markup=main_menu()
    )


@router.message(F.text == "/help")
async def cmd_help(message: Message):
    await message.answer(
        "Доступные команды:\n"
        "/start — главное меню\n"
        "/tasks — список задач\n"
        "/newtask — новая задача\n"
        "/spend — новый расход\n"
        "/stats — статистика расходов\n\n"
        "Либо просто используй кнопки внизу экрана 👇"
    )