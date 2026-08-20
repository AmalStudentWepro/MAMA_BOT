from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


# Главное меню (постоянная клавиатура внизу экрана)
def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Задачи"), KeyboardButton(text="➕ Новая задача")],
            [KeyboardButton(text="💰 Расходы"), KeyboardButton(text="➕ Новый расход")],
            [KeyboardButton(text="📊 Статистика")],
        ],
        resize_keyboard=True
    )


# Кнопки выбора повтора при создании задачи
def repeat_choice_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Без повтора", callback_data="repeat_none")],
        [InlineKeyboardButton(text="Каждый день", callback_data="repeat_daily")],
        [InlineKeyboardButton(text="Каждую неделю", callback_data="repeat_weekly")],
    ])


# Список задач с кнопками "выполнено" / "удалить" под каждой
def task_item_kb(task_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Выполнено", callback_data=f"task_done_{task_id}"),
            InlineKeyboardButton(text="🗑 Удалить", callback_data=f"task_del_{task_id}"),
        ]
    ])


# Категории расходов
EXPENSE_CATEGORIES = ["🍔 Еда", "🚌 Транспорт", "🎮 Развлечения", "🏠 Дом", "👕 Одежда", "❓ Другое"]

def expense_categories_kb() -> InlineKeyboardMarkup:
    buttons = [[InlineKeyboardButton(text=cat, callback_data=f"cat_{cat}")] for cat in EXPENSE_CATEGORIES]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# Период для статистики
def stats_period_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="За сегодня", callback_data="stats_today")],
        [InlineKeyboardButton(text="За неделю", callback_data="stats_week")],
        [InlineKeyboardButton(text="За месяц", callback_data="stats_month")],
        [InlineKeyboardButton(text="За всё время", callback_data="stats_all")],
    ])