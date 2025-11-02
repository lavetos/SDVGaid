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
            [KeyboardButton(text="/goal"), KeyboardButton(text="/plan")],
            [KeyboardButton(text="/focus"), KeyboardButton(text="/reminders")],
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


def get_reminder_keyboard(reminder_id: int, page: int = 0) -> InlineKeyboardMarkup:
    """Клавиатура управления напоминанием"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Выполнено", callback_data=f"rem_{reminder_id}_done"),
                InlineKeyboardButton(text="✏️ Изменить", callback_data=f"rem_{reminder_id}_edit")
            ],
            [InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"rem_{reminder_id}_delete")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data=f"rem_list_{page}")]
        ]
    )


def get_reminders_list_keyboard(reminders: list, page: int = 0) -> InlineKeyboardMarkup:
    """Клавиатура списка напоминаний"""
    keyboard = []
    
    # Show 5 reminders per page
    start = page * 5
    end = min(start + 5, len(reminders))
    
    for rem in reminders[start:end]:
        emoji = "✅" if rem.completed else "⏰"
        keyboard.append([
            InlineKeyboardButton(
                text=f"{emoji} {rem.text[:30]}...",
                callback_data=f"rem_view_{rem.id}"
            )
        ])
    
    # Pagination
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(text="⬅️", callback_data=f"rem_list_{page-1}"))
    if end < len(reminders):
        nav_row.append(InlineKeyboardButton(text="➡️", callback_data=f"rem_list_{page+1}"))
    
    if nav_row:
        keyboard.append(nav_row)
    
    keyboard.append([InlineKeyboardButton(text="➕ Добавить", callback_data="rem_add")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_plan_item_keyboard(item_id: int) -> InlineKeyboardMarkup:
    """Клавиатура управления пунктом плана"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Сделано", callback_data=f"plan_{item_id}_done"),
                InlineKeyboardButton(text="✏️ Изменить", callback_data=f"plan_{item_id}_edit")
            ],
            [InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"plan_{item_id}_delete")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="plan_list")]
        ]
    )


def get_plan_list_keyboard(items: list) -> InlineKeyboardMarkup:
    """Клавиатура списка плана на день"""
    keyboard = []
    
    for item in items:
        emoji = "✅" if item.completed else "⭕"
        keyboard.append([
            InlineKeyboardButton(
                text=f"{emoji} {item.text[:30]}...",
                callback_data=f"plan_view_{item.id}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton(text="➕ Добавить пункт", callback_data="plan_add")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

