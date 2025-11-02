"""Клавиатуры для бота"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def get_energy_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура выбора уровня энергии"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔋 Меньше 40%"), KeyboardButton(text="⚡ Около 60%")],
            [KeyboardButton(text="💪 Больше 80%")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def get_day_type_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура выбора типа дня"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="😌 Мягкий день")],
            [KeyboardButton(text="🎯 Обычный день")],
            [KeyboardButton(text="🚀 Активный день")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def get_pomodoro_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура управления Pomodoro"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Продолжить", callback_data="pomodoro_continue")],
            [InlineKeyboardButton(text="🏁 Завершить", callback_data="pomodoro_stop")]
        ]
    )


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Главная клавиатура с командами"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="/goal"), KeyboardButton(text="/focus")],
            [KeyboardButton(text="/note"), KeyboardButton(text="/notes")],
            [KeyboardButton(text="/evening"), KeyboardButton(text="/quiet")],
            [KeyboardButton(text="/energy")]
        ],
        resize_keyboard=True
    )


def get_goal_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения цели"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Да, это моя цель", callback_data="goal_confirm")],
            [InlineKeyboardButton(text="✏️ Изменить", callback_data="goal_edit")]
        ]
    )


def get_goal_completion_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура завершения цели"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Сделал(а)", callback_data="goal_done")],
            [InlineKeyboardButton(text="⏭️ Не сегодня", callback_data="goal_skip")]
        ]
    )

