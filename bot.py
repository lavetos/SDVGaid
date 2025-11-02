"""Главный файл Telegram-бота SDVGaid"""
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery
from datetime import datetime
from config import BOT_TOKEN, POMODORO_WORK_TIME, POMODORO_BREAK_TIME, QUIET_MODE_DURATION
from database import init_db
from db_helpers import (
    get_or_create_user, save_energy_level, save_goal, get_todays_goal, 
    complete_goal, save_note, get_user_notes, save_evening_checkin,
    get_energy_stats_week, get_user_state, set_quiet_mode, disable_quiet_mode
)
from keyboards import (
    get_energy_keyboard, get_day_type_keyboard, get_pomodoro_keyboard,
    get_main_keyboard, get_goal_confirmation_keyboard, get_goal_completion_keyboard
)
from ai_service import ai_service
from scheduler import ReminderScheduler


# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Инициализация планировщика
scheduler = ReminderScheduler(bot)


# Состояния FSM
class BotStates(StatesGroup):
    waiting_energy = State()
    waiting_goal = State()
    waiting_note = State()
    waiting_evening_worked = State()
    waiting_evening_tired = State()
    waiting_evening_helped = State()


# Словарь для хранения активных Pomodoro сессий
active_pomodoros = {}


# ==================== ОБРАБОТЧИКИ КОМАНД ====================

@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Приветственное сообщение и начало работы"""
    await state.clear()
    user = await get_or_create_user(
        message.from_user.id, 
        message.from_user.username,
        message.from_user.full_name
    )
    
    greeting = f"""Привет! ☀️

Я твой помощник для мягкого и структурированного дня.

Я не буду говорить тебе "надо" или "ты должен".
Мы просто вместе пройдём по дню — как получится 💛

Как дела? На сколько процентов ты заряжен?"""
    
    await message.answer(greeting, reply_markup=get_energy_keyboard())
    await state.set_state(BotStates.waiting_energy)


@dp.message(Command("goal"))
async def cmd_goal(message: Message, state: FSMContext):
    """Установить главное дело дня"""
    todays_goal = await get_todays_goal(message.from_user.id)
    
    if todays_goal:
        text = f"""Твоя сегодняшняя цель: {todays_goal.goal_text}

Хочешь поменять её?"""
        await message.answer(text, reply_markup=get_goal_confirmation_keyboard())
    else:
        await message.answer("Так, какое главное дело на сегодня? 🎯", reply_markup=None)
        await state.set_state(BotStates.waiting_goal)


@dp.message(StateFilter(BotStates.waiting_goal))
async def process_goal(message: Message, state: FSMContext):
    """Обработка цели дня"""
    goal = await save_goal(message.from_user.id, message.text)
    
    text = f"""Отлично! Записал твою цель:
{goal.goal_text}

Я вечером напомню и спрошу, как прошло 🤝"""
    
    await message.answer(text, reply_markup=get_main_keyboard())
    await state.clear()


@dp.message(Command("focus"))
async def cmd_focus(message: Message, state: FSMContext):
    """Запустить Pomodoro таймер"""
    user_id = message.from_user.id
    
    # Проверяем, нет ли уже активного Pomodoro
    if user_id in active_pomodoros:
        await message.answer("У тебя уже есть активный таймер! ⏱️", reply_markup=get_main_keyboard())
        return
    
    # Проверяем режим тишины
    user_state = await get_user_state(user_id)
    if user_state.in_quiet_mode and user_state.quiet_mode_until > datetime.utcnow():
        await message.answer("Ты в режиме тишины. Отдыхай 😌", reply_markup=get_main_keyboard())
        return
    
    await message.answer("Поехали! 25 минут фокуса 🍅", reply_markup=None)
    await start_pomodoro(user_id, message.chat.id)


async def start_pomodoro(user_id: int, chat_id: int):
    """Запустить Pomodoro таймер"""
    active_pomodoros[user_id] = True
    
    # Рабочее время
    await asyncio.sleep(POMODORO_WORK_TIME)
    
    if user_id not in active_pomodoros:
        return
    
    await bot.send_message(chat_id, "Стоп! Перерыв 5 минут 🌿\n\nЧто-то налить? Воды попить? 🌊")
    
    # Время перерыва
    await asyncio.sleep(POMODORO_BREAK_TIME)
    
    if user_id not in active_pomodoros:
        return
    
    await bot.send_message(chat_id, "Перерыв окончен! Продолжим?", reply_markup=get_pomodoro_keyboard())


@dp.callback_query(F.data == "pomodoro_continue")
async def pomodoro_continue(callback: CallbackQuery):
    """Продолжить Pomodoro"""
    await callback.message.edit_text("Снова 25 минут фокуса 🍅")
    await start_pomodoro(callback.from_user.id, callback.message.chat.id)
    await callback.answer()


@dp.callback_query(F.data == "pomodoro_stop")
async def pomodoro_stop(callback: CallbackQuery):
    """Остановить Pomodoro"""
    user_id = callback.from_user.id
    if user_id in active_pomodoros:
        del active_pomodoros[user_id]
    
    await callback.message.edit_text("Таймер остановлен ✅\n\nОтличная работа! 💪")
    await callback.answer()


@dp.message(Command("note"))
async def cmd_note(message: Message, state: FSMContext):
    """Добавить заметку"""
    await message.answer("Что записать в твою внешнюю голову? 🧠", reply_markup=None)
    await state.set_state(BotStates.waiting_note)


@dp.message(StateFilter(BotStates.waiting_note))
async def process_note(message: Message, state: FSMContext):
    """Обработка заметки"""
    note = await save_note(message.from_user.id, message.text)
    
    await message.answer(f"✅ Запомнил:\n{note.text}", reply_markup=get_main_keyboard())
    await state.clear()


@dp.message(Command("notes"))
async def cmd_notes(message: Message, state: FSMContext):
    """Показать все заметки"""
    notes = await get_user_notes(message.from_user.id)
    
    if not notes:
        await message.answer("Заметок пока нет 🤷", reply_markup=get_main_keyboard())
        return
    
    text = "📝 Твои заметки:\n\n"
    for i, note in enumerate(notes, 1):
        text += f"{i}. {note.text}\n"
    
    await message.answer(text, reply_markup=get_main_keyboard())


@dp.message(Command("evening"))
async def cmd_evening(message: Message, state: FSMContext):
    """Вечерний чек-ин"""
    await message.answer("Итак, как прошёл день? 🌙\n\nЧто получилось сделать?", reply_markup=None)
    await state.set_state(BotStates.waiting_evening_worked)


@dp.message(StateFilter(BotStates.waiting_evening_worked))
async def process_evening_worked(message: Message, state: FSMContext):
    """Обработка первого вопроса чек-ина"""
    await state.update_data(what_worked=message.text)
    await message.answer("Что вымотало сегодня?")
    await state.set_state(BotStates.waiting_evening_tired)


@dp.message(StateFilter(BotStates.waiting_evening_tired))
async def process_evening_tired(message: Message, state: FSMContext):
    """Обработка второго вопроса чек-ина"""
    await state.update_data(what_tired=message.text)
    await message.answer("И последнее: что помогло немного сегодня? 💛")
    await state.set_state(BotStates.waiting_evening_helped)


@dp.message(StateFilter(BotStates.waiting_evening_helped))
async def process_evening_helped(message: Message, state: FSMContext):
    """Обработка третьего вопроса чек-ина"""
    data = await state.get_data()
    
    await save_evening_checkin(
        message.from_user.id,
        what_worked=data.get('what_worked'),
        what_tired=data.get('what_tired'),
        what_helped=message.text
    )
    
    # Проверяем главное дело дня
    todays_goal = await get_todays_goal(message.from_user.id)
    
    if todays_goal and not todays_goal.completed:
        await message.answer(
            f"💫 Спасибо за чек-ин!\n\n\nКстати, помнишь про цель:\n{todays_goal.goal_text}\n\nЧто с ней?", 
            reply_markup=get_goal_completion_keyboard()
        )
    else:
        text = """Спасибо за чек-ин! 💛

Ты молодец. Даже если что-то не получилось — 
просто дожить день уже достижение.

Спокойной ночи! 🌙"""
        await message.answer(text, reply_markup=get_main_keyboard())
    
    await state.clear()


@dp.callback_query(F.data == "goal_done")
async def goal_done(callback: CallbackQuery):
    """Цель выполнена"""
    goal = await get_todays_goal(callback.from_user.id)
    if goal:
        await complete_goal(goal.id, True)
    
    await callback.message.edit_text("Отлично! Ты справился! 🎉")
    await callback.answer()


@dp.callback_query(F.data == "goal_skip")
async def goal_skip(callback: CallbackQuery):
    """Цель не выполнена"""
    await callback.message.edit_text(
        "Ничего страшного 💛\n\nИногда просто не получается — и это нормально. "
        "Завтра другой день!"
    )
    await callback.answer()


@dp.message(Command("quiet"))
async def cmd_quiet(message: Message):
    """Режим тишины"""
    await set_quiet_mode(message.from_user.id, QUIET_MODE_DURATION)
    
    text = """Это твоё время перезагрузки 😌

Я подожду 30 минут и не буду беспокоить."""
    
    await message.answer(text, reply_markup=get_main_keyboard())
    
    # Планируем отключение тишины
    await asyncio.sleep(QUIET_MODE_DURATION)
    await disable_quiet_mode(message.from_user.id)
    await bot.send_message(message.chat.id, "Режим тишины завершён. Как дела? 👋")


@dp.message(Command("energy"))
async def cmd_energy(message: Message, state: FSMContext):
    """Статистика энергии"""
    stats = await get_energy_stats_week(message.from_user.id)
    
    if stats['days_count'] == 0:
        text = """Статистики пока нет 📊

Используй /start утром, чтобы начать отслеживать свой уровень энергии!"""
    else:
        avg = stats['avg_energy']
        days = stats['days_count']
        
        if avg < 40:
            emoji = "🔋"
            description = "низко"
        elif avg < 60:
            emoji = "⚡"
            description = "средне"
        else:
            emoji = "💪"
            description = "высоко"
        
        text = f"""Твоя энергия за неделю 📊

Средний уровень: {emoji} {avg}% ({description})
Отслеживалось дней: {days}"""
    
    await message.answer(text, reply_markup=get_main_keyboard())


# ==================== ОБРАБОТЧИКИ УТРЕННЕГО ДИАЛОГА ====================

@dp.message(StateFilter(BotStates.waiting_energy))
async def process_energy(message: Message, state: FSMContext):
    """Обработка выбора уровня энергии"""
    energy_map = {
        "🔋 меньше 40%": 40,
        "⚡ около 60%": 60,
        "💪 больше 80%": 80
    }
    
    energy_level = energy_map.get(message.text.lower())
    
    if not energy_level:
        await message.answer("Выбери один из вариантов выше! 👆", reply_markup=get_energy_keyboard())
        return
    
    # Сохраняем уровень энергии
    await save_energy_level(message.from_user.id, energy_level)
    
    # Предлагаем тип дня
    if energy_level < 40:
        day_type_text = "😌 Мягкий день"
        advice = """Сегодня мягкий день, хорошо? 

Можешь выбрать:"
• Зарядку на 5 минут
• Хороший завтрак
• Короткую прогулку
• Даже просто душ

Не надо "больших дел" — просто по чуть-чуть 🌿"""
    elif energy_level < 60:
        day_type_text = "🎯 Обычный день"
        advice = """Обычный день — значит, есть силы на что-то одно главное ✨

Выбери одно дело (не больше!), сфокусируйся на нём — 
и всё остальное подождёт. Остальные пункты — бонус."""
    else:
        day_type_text = "🚀 Активный день"
        advice = """Энергии много! Отлично 🌟

Сегодня можно взять несколько задач — 
но всё равно не перегружайся. 

Главное дело + 2-3 мелких — и уже супер!"""
    
    await message.answer(advice, reply_markup=get_main_keyboard())
    await state.clear()


# ==================== AI ОБРАБОТЧИК ====================

@dp.message()
async def handle_ai_message(message: Message):
    """Обработка сообщений с помощью AI (если не команда и не в состоянии)"""
    # Skip if it's a command or energy selection
    if message.text.startswith('/'):
        return
    
    # Skip button presses
    if message.text in ["🔋 Меньше 40%", "⚡ Около 60%", "💪 Больше 80%",
                       "😌 Мягкий день", "🎯 Обычный день", "🚀 Активный день"]:
        return
    
    # Get user's current energy level
    user_state = await get_user_state(message.from_user.id)
    energy = None  # Could fetch latest energy from DB
    
    # Process with AI
    try:
        response = await ai_service.process_message(message.text, message.from_user.id, energy)
        await message.answer(response, reply_markup=get_main_keyboard())
    except Exception as e:
        print(f"AI error: {e}")
        # Fallback to simple response
        await message.answer(
            "Понял тебя 💛\n\nИспользуй команды /goal, /focus, /note или /evening для работы со мной!",
            reply_markup=get_main_keyboard()
        )


# ==================== ЗАПУСК БОТА ====================

async def main():
    """Главная функция"""
    print("Запуск бота SDVGaid... 🤖")
    
    # Инициализация AI
    print(f"AI провайдер: {ai_service.current_provider.upper()} 🤖")
    
    # Инициализация БД
    await init_db()
    print("База данных инициализирована ✅")
    
    # Запуск планировщика
    scheduler.start()
    print("Планировщик запущен ⏰")
    
    # Запуск бота
    print("Бот запущен! 🚀")
    try:
        await dp.start_polling(bot)
    finally:
        scheduler.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nБот остановлен 👋")

