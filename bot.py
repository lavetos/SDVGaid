"""Главный файл Telegram-бота SDVGaid"""
import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, StateFilter, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery, Voice

logger = logging.getLogger(__name__)
from datetime import datetime
from config import BOT_TOKEN, POMODORO_WORK_TIME, POMODORO_BREAK_TIME, QUIET_MODE_DURATION
from database import init_db
from db_helpers import (
    get_or_create_user, save_energy_level, save_goal, get_todays_goal, 
    complete_goal, save_note, get_user_notes, delete_note, delete_all_notes,
    save_evening_checkin, get_energy_stats_week, get_user_state, 
    set_quiet_mode, disable_quiet_mode, get_all_reminders, delete_reminder, 
    complete_reminder, get_plan_items, add_plan_item, delete_plan_item, 
    toggle_plan_item
)
from datetime import datetime, timedelta
import pytz
from keyboards import (
    get_energy_keyboard, get_day_type_keyboard, get_pomodoro_keyboard,
    get_main_keyboard, get_goal_confirmation_keyboard, get_goal_completion_keyboard,
    get_reminders_list_keyboard, get_reminder_keyboard, get_reminder_delete_confirm_keyboard,
    get_plan_list_keyboard, get_plan_item_keyboard, get_plan_delete_confirm_keyboard, get_cancel_keyboard
)
from ai_service import ai_service
from scheduler import ReminderScheduler
from ai_functions import FunctionHandler


# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Инициализация планировщика
scheduler = ReminderScheduler(bot)

# Инициализация function handler с scheduler и bot
import ai_functions as af_module
af_module.function_handler = FunctionHandler(scheduler=scheduler, bot=bot)


# Состояния FSM
class BotStates(StatesGroup):
    waiting_energy = State()
    waiting_goal = State()
    waiting_note = State()
    waiting_evening_worked = State()
    waiting_evening_tired = State()
    waiting_evening_helped = State()
    waiting_plan_item = State()
    waiting_reminder_text = State()


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


@dp.message(Command("help"))
async def cmd_help(message: Message, state: FSMContext):
    """Показать справку по командам"""
    await state.clear()
    
    help_text = """📖 Справка по командам

🎯 Планирование:
• /goal — Главное дело на сегодня
• /plan — План на день (задачи)
• /focus — Таймер фокуса (25 мин)

⏰ Напоминания:
• /reminders — Все напоминания
• Просто напиши: напомни позвонить маме завтра в 15:00

📝 Заметки:
• /note — Добавить заметку
• /notes — Посмотреть все заметки

🌙 Вечер:
• /evening — Вечерний чек-ин

😌 Режим тишины:
• /quiet — 30 минут без уведомлений

📊 Статистика:
• /energy — Статистика энергии за неделю

🎤 Голосовой ввод:
• Можешь отправлять голосовые сообщения вместо текста!
• Работает для всех команд, где нужно ввести текст

💬 Совет: Можешь просто писать мне естественным языком, я пойму! 💛

Например:
• Добавь в план: купить молоко
• Напомни через час выпить воду
• Как разбить задачу на шаги?"""
    
    await message.answer(help_text, reply_markup=get_main_keyboard())


@dp.message(Command("goal"))
async def cmd_goal(message: Message, state: FSMContext):
    """Установить главное дело дня"""
    todays_goal = await get_todays_goal(message.from_user.id)
    
    if todays_goal:
        text = f"""Твоя сегодняшняя цель: {todays_goal.goal_text}

Хочешь поменять её?"""
        await message.answer(text, reply_markup=get_goal_confirmation_keyboard())
    else:
        await message.answer(
            "Так, какое главное дело на сегодня? 🎯\n\n"
            "Можешь написать текст или отправить голосовое сообщение 🎤\n\n"
            "(Или нажми ❌ Отмена)",
            reply_markup=get_cancel_keyboard()
        )
        await state.set_state(BotStates.waiting_goal)


@dp.message(StateFilter(BotStates.waiting_goal))
async def process_goal(message: Message, state: FSMContext):
    """Обработка цели дня"""
    # Обработка голосового сообщения
    if message.voice:
        from voice_service import get_voice_service
        voice_service = get_voice_service()
        if voice_service:
            processing_msg = await message.answer("🎤 Распознаю голос... ⏳")
            try:
                text = await voice_service.process_voice_message(message, bot)
                if text and text.strip():
                    message.text = text
                    await processing_msg.delete()
                    await message.answer(f"✍️ Распознано: {text}", reply_markup=None)
                else:
                    await processing_msg.edit_text("Не удалось распознать речь 😅\n\nПопробуй ещё раз", reply_markup=get_cancel_keyboard())
                    return
            except Exception as e:
                logger.error(f"Voice recognition error: {e}")
                await processing_msg.edit_text("Не удалось обработать голос 😅\n\nПопробуй написать текст", reply_markup=get_cancel_keyboard())
                return
        else:
            await message.answer("Голосовой ввод недоступен. Напиши текст 📝", reply_markup=get_cancel_keyboard())
            return
    
    # Обработка отмены
    if message.text and message.text.strip() in ["❌ Отмена", "отмена", "Отмена", "/cancel", "/start"]:
        await state.clear()
        await message.answer("Окей, цель можно поставить позже 💛", reply_markup=get_main_keyboard())
        return
    
    # Валидация
    if not message.text or not message.text.strip():
        await message.answer("Пожалуйста, напиши текст цели 🎯\n\nИли отправь голосовое сообщение 🎤\n\nИли нажми ❌ Отмена", reply_markup=get_cancel_keyboard())
        return
    
    if len(message.text.strip()) > 200:
        await message.answer("Цель слишком длинная (макс. 200 символов) 📝\n\nПопробуй короче или нажми ❌ Отмена", reply_markup=get_cancel_keyboard())
        return
    
    try:
        goal = await save_goal(message.from_user.id, message.text.strip())
        
        text = f"""✅ Готово! Записал:

{goal.goal_text}

Я вечером напомню и спрошу, как прошло 🤝"""
        
        await message.answer(text, reply_markup=get_main_keyboard())
    except Exception as e:
        print(f"Error saving goal: {e}")
        await message.answer("Упс, не получилось сохранить 😅 Попробуй ещё раз?", reply_markup=get_main_keyboard())
    finally:
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
    await message.answer(
        "Что записать в твою внешнюю голову? 🧠\n\n"
        "Можешь написать текст или отправить голосовое сообщение 🎤\n\n"
        "(Или нажми ❌ Отмена)",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(BotStates.waiting_note)


@dp.message(StateFilter(BotStates.waiting_note))
async def process_note(message: Message, state: FSMContext):
    """Обработка заметки"""
    # Обработка отмены
    if message.text and message.text.strip() in ["❌ Отмена", "отмена", "Отмена", "/cancel", "/start"]:
        await state.clear()
        await message.answer("Окей, заметку можно добавить позже 💛", reply_markup=get_main_keyboard())
        return
    
    # Валидация
    if not message.text or not message.text.strip():
        await message.answer("Пожалуйста, напиши текст заметки 📝\n\nИли нажми ❌ Отмена", reply_markup=get_cancel_keyboard())
        return
    
    if len(message.text.strip()) > 500:
        await message.answer("Заметка слишком длинная (макс. 500 символов) 📝\n\nПопробуй короче или нажми ❌ Отмена", reply_markup=get_cancel_keyboard())
        return
    
    try:
        note = await save_note(message.from_user.id, message.text.strip())
        await message.answer(f"✅ Запомнил:\n\n{note.text}", reply_markup=get_main_keyboard())
    except Exception as e:
        print(f"Error saving note: {e}")
        await message.answer("Упс, не получилось сохранить 😅 Попробуй ещё раз?", reply_markup=get_main_keyboard())
    finally:
        await state.clear()


@dp.message(Command("notes"))
async def cmd_notes(message: Message, state: FSMContext):
    """Показать все заметки"""
    notes = await get_user_notes(message.from_user.id)
    
    if not notes:
        await message.answer(
            "Заметок пока нет 📝\n\n"
            "✨ Используй /note чтобы сохранить мысль или идею\n"
            "Или просто напиши мне что-нибудь, и я запомню!",
            reply_markup=get_main_keyboard()
        )
        return
    
    text = f"📝 Твои заметки ({len(notes)}):\n\n"
    for i, note in enumerate(notes, 1):
        text += f"{i}. {note.text}\n"
    
    text += "\n\nДля удаления напиши: 'удали все заметки' или 'очисти заметки'"
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


@dp.callback_query(F.data == "goal_confirm")
async def goal_confirm(callback: CallbackQuery):
    """Подтвердить текущую цель"""
    goal = await get_todays_goal(callback.from_user.id)
    if goal:
        await callback.message.edit_text(
            f"Отлично! Остаёмся с целью:\n\n{goal.goal_text}\n\nУдачи! 💪",
            reply_markup=get_main_keyboard()
        )
    else:
        await callback.message.edit_text("Цель не найдена 🤷", reply_markup=get_main_keyboard())
    await callback.answer()


@dp.callback_query(F.data == "goal_edit")
async def goal_edit(callback: CallbackQuery, state: FSMContext):
    """Изменить цель"""
    await callback.message.edit_text("Так, какое главное дело на сегодня? 🎯", reply_markup=None)
    await state.set_state(BotStates.waiting_goal)
    await callback.answer()


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
    # Проверяем текст кнопки (с заглавной буквы) и варианты с маленькой
    energy_map = {
        "🔋 меньше 40%": 40,
        "🔋 Меньше 40%": 40,
        "⚡ около 60%": 60,
        "⚡ Около 60%": 60,
        "💪 больше 80%": 80,
        "💪 Больше 80%": 80
    }
    
    # Проверяем сначала точное совпадение, потом нижний регистр
    energy_level = energy_map.get(message.text) or energy_map.get(message.text.lower())
    
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


# ==================== REMINDERS ====================

@dp.message(Command("reminders"))
async def cmd_reminders(message: Message):
    """Показать все напоминания"""
    try:
        reminders = await get_all_reminders(message.from_user.id, completed=False)
        
        if not reminders:
            # Показываем кнопку "Добавить" даже если напоминаний нет
            await message.answer(
                "Напоминаний пока нет 📭\n\n"
                "✨ Можешь добавить напоминание:\n"
                "• Нажми кнопку '➕ Добавить' ниже\n"
                "• Или просто напиши: 'напомни позвонить маме завтра в 15:00'",
                reply_markup=get_reminders_list_keyboard(reminders)
            )
            return
        
        text = f"Напоминания ({len(reminders)}) ⏰\n\n"
        for i, rem in enumerate(reminders[:5], 1):
            text += f"{i}. {rem.text}\n"
        
        await message.answer(text, reply_markup=get_reminders_list_keyboard(reminders))
    except Exception as e:
        print(f"Error in /reminders: {e}")
        await message.answer(f"Ошибка: {e}", reply_markup=get_main_keyboard())


@dp.callback_query(F.data.startswith("rem_view_"))
async def callback_reminder_view(callback: CallbackQuery):
    """Просмотр напоминания"""
    reminder_id = int(callback.data.split("_")[2])
    reminders = await get_all_reminders(callback.from_user.id)
    reminder = next((r for r in reminders if r.id == reminder_id), None)
    
    if not reminder:
        await callback.answer("Напоминание не найдено")
        return
    
    from datetime import datetime
    when_str = reminder.when_datetime.strftime("%d.%m.%Y %H:%M")
    text = f"⏰ Напоминание\n\n{reminder.text}\n\nКогда: {when_str}"
    
    await callback.message.edit_text(text, reply_markup=get_reminder_keyboard(reminder_id))
    await callback.answer()


@dp.callback_query(F.data.startswith("rem_list_"))
async def callback_reminders_list(callback: CallbackQuery):
    """Список напоминаний"""
    page = int(callback.data.split("_")[2])
    reminders = await get_all_reminders(callback.from_user.id, completed=False)
    
    if not reminders:
        await callback.message.edit_text("Напоминаний нет 📭", reply_markup=get_main_keyboard())
        await callback.answer()
        return
    
    text = f"Напоминания ({len(reminders)}) ⏰\n\n"
    await callback.message.edit_text(text, reply_markup=get_reminders_list_keyboard(reminders, page))
    await callback.answer()


@dp.callback_query(F.data.startswith("rem_") and F.data.endswith("_done"))
async def callback_reminder_done(callback: CallbackQuery):
    """Отметить напоминание выполненным"""
    reminder_id = int(callback.data.split("_")[1])
    success = await complete_reminder(reminder_id, callback.from_user.id)
    
    if success:
        await callback.answer("✅ Выполнено!")
        # Refresh list
        reminders = await get_all_reminders(callback.from_user.id, completed=False)
        await callback.message.edit_text("Напоминание выполнено ✅", reply_markup=get_reminders_list_keyboard(reminders))
    else:
        await callback.answer("Ошибка ⚠️")


@dp.callback_query(lambda c: c.data and c.data.startswith("rem_") and c.data.endswith("_delete_confirm"))
async def callback_reminder_delete_confirm(callback: CallbackQuery):
    """Подтверждение удаления напоминания"""
    reminder_id = int(callback.data.split("_")[1])
    reminders = await get_all_reminders(callback.from_user.id)
    reminder = next((r for r in reminders if r.id == reminder_id), None)
    
    if not reminder:
        await callback.answer("Напоминание не найдено")
        return
    
    await callback.message.edit_text(
        f"❓ Точно удалить напоминание?\n\n{reminder.text}",
        reply_markup=get_reminder_delete_confirm_keyboard(reminder_id)
    )
    await callback.answer()


@dp.callback_query(lambda c: c.data and c.data.startswith("rem_") and c.data.endswith("_delete") and not c.data.endswith("_delete_confirm"))
async def callback_reminder_delete(callback: CallbackQuery):
    """Удалить напоминание"""
    reminder_id = int(callback.data.split("_")[1])
    success = await delete_reminder(reminder_id, callback.from_user.id)
    
    if success:
        await callback.answer("🗑️ Удалено")
        reminders = await get_all_reminders(callback.from_user.id, completed=False)
        if reminders:
            await callback.message.edit_text("✅ Напоминание удалено", reply_markup=get_reminders_list_keyboard(reminders))
        else:
            await callback.message.edit_text(
                "✅ Напоминание удалено\n\n"
                "Напоминаний больше нет 📭\n"
                "Хочешь добавить новое?",
                reply_markup=get_reminders_list_keyboard(reminders)
            )
    else:
        await callback.answer("Ошибка ⚠️")


@dp.callback_query(F.data == "rem_add")
async def callback_reminder_add(callback: CallbackQuery, state: FSMContext):
    """Добавить напоминание"""
    await callback.message.edit_text("Напиши текст напоминания и время.\n\nНапример: 'Позвонить маме завтра в 15:00' или 'Выпить воду через час'", reply_markup=None)
    await bot.send_message(
        callback.from_user.id,
        "📝 Напиши напоминание:\n\n"
        "Или отправь голосовое сообщение 🎤\n\n"
        "(Или нажми ❌ Отмена)",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(BotStates.waiting_reminder_text)
    await callback.answer()


@dp.message(StateFilter(BotStates.waiting_reminder_text))
async def process_reminder_text(message: Message, state: FSMContext):
    """Обработка текста напоминания через AI"""
    # Обработка голосового сообщения
    if message.voice:
        from voice_service import get_voice_service
        voice_service = get_voice_service()
        if voice_service:
            processing_msg = await message.answer("🎤 Распознаю голос... ⏳")
            try:
                text = await voice_service.process_voice_message(message, bot)
                if text and text.strip():
                    message.text = text
                    await processing_msg.delete()
                    await message.answer(f"✍️ Распознано: {text}", reply_markup=None)
                else:
                    await processing_msg.edit_text("Не удалось распознать речь 😅\n\nПопробуй ещё раз", reply_markup=get_cancel_keyboard())
                    return
            except Exception as e:
                logger.error(f"Voice recognition error: {e}")
                await processing_msg.edit_text("Не удалось обработать голос 😅\n\nПопробуй написать текст", reply_markup=get_cancel_keyboard())
                return
        else:
            await message.answer("Голосовой ввод недоступен. Напиши текст 📝", reply_markup=get_cancel_keyboard())
            return
    
    # Обработка отмены
    if message.text and message.text.strip() in ["❌ Отмена", "отмена", "Отмена", "/cancel", "/start"]:
        await state.clear()
        await message.answer("Окей, напоминание можно добавить позже 💛", reply_markup=get_main_keyboard())
        return
    
    if message.text and message.text.startswith('/'):
        await state.clear()
        return
    
    # Валидация
    if not message.text or not message.text.strip():
        await message.answer("Пожалуйста, напиши текст напоминания ⏰\n\nИли отправь голосовое сообщение 🎤\n\nИли нажми ❌ Отмена", reply_markup=get_cancel_keyboard())
        return
    
    # Обрабатываем через AI, который создаст напоминание
    try:
        await message.answer("⏳ Обрабатываю...", reply_markup=None)
        response = await ai_service.process_message(message.text.strip(), message.from_user.id, None)
        await message.answer(response, reply_markup=get_main_keyboard())
    except Exception as e:
        print(f"Error processing reminder: {e}")
        await message.answer(
            "Упс, не получилось создать напоминание 😅\n\nПопробуй ещё раз или используй команду /reminders",
            reply_markup=get_main_keyboard()
        )
    finally:
        await state.clear()


# ==================== DAILY PLAN ====================

@dp.message(Command("plan"))
async def cmd_plan(message: Message, state: FSMContext):
    """Показать план на день"""
    try:
        items = await get_plan_items(message.from_user.id, completed=None)
        
        if not items:
            await message.answer(
                "План пуст 📋\n\n"
                "✨ Начни свой день с простых задач:\n"
                "• Нажми '➕ Добавить пункт'\n"
                "• Или напиши: 'Добавь в план: купить молоко'",
                reply_markup=get_plan_list_keyboard(items)
            )
            # Не устанавливаем состояние здесь - пользователь должен нажать кнопку
        else:
            completed = sum(1 for item in items if item.completed)
            text = f"План на день 📋\n\nВыполнено: {completed}/{len(items)}\n\n"
            await message.answer(text, reply_markup=get_plan_list_keyboard(items))
    except Exception as e:
        print(f"Error in /plan: {e}")
        await message.answer(f"Ошибка: {e}", reply_markup=get_main_keyboard())


@dp.message(StateFilter(BotStates.waiting_plan_item))
async def process_plan_item(message: Message, state: FSMContext):
    """Обработка добавления пункта в план"""
    # Обработка голосового сообщения
    if message.voice:
        from voice_service import get_voice_service
        voice_service = get_voice_service()
        if voice_service:
            processing_msg = await message.answer("🎤 Распознаю голос... ⏳")
            try:
                text = await voice_service.process_voice_message(message, bot)
                if text and text.strip():
                    message.text = text
                    await processing_msg.delete()
                    await message.answer(f"✍️ Распознано: {text}", reply_markup=None)
                else:
                    await processing_msg.edit_text("Не удалось распознать речь 😅\n\nПопробуй ещё раз", reply_markup=get_cancel_keyboard())
                    return
            except Exception as e:
                logger.error(f"Voice recognition error: {e}")
                await processing_msg.edit_text("Не удалось обработать голос 😅\n\nПопробуй написать текст", reply_markup=get_cancel_keyboard())
                return
        else:
            await message.answer("Голосовой ввод недоступен. Напиши текст 📝", reply_markup=get_cancel_keyboard())
            return
    
    # Обработка отмены
    if message.text and message.text.strip() in ["❌ Отмена", "отмена", "Отмена", "/cancel", "/start"]:
        await state.clear()
        await message.answer("Окей, план можно дополнить позже 💛", reply_markup=get_main_keyboard())
        return
    
    if message.text and message.text.startswith('/'):
        await state.clear()
        return
    
    # Валидация
    if not message.text or not message.text.strip():
        await message.answer("Пожалуйста, напиши задачу 📝\n\nИли отправь голосовое сообщение 🎤\n\nИли нажми ❌ Отмена", reply_markup=get_cancel_keyboard())
        return
    
    if len(message.text.strip()) > 200:
        await message.answer("Задача слишком длинная (макс. 200 символов) 📝\n\nПопробуй короче или нажми ❌ Отмена", reply_markup=get_cancel_keyboard())
        return
    
    try:
        item = await add_plan_item(message.from_user.id, message.text.strip())
        await message.answer(f"✅ Добавлено в план:\n\n{item.text}", reply_markup=get_main_keyboard())
    except Exception as e:
        print(f"Error adding plan item: {e}")
        await message.answer("Упс, не получилось добавить 😅 Попробуй ещё раз?", reply_markup=get_main_keyboard())
    finally:
        await state.clear()


@dp.callback_query(F.data == "plan_add")
async def callback_plan_add(callback: CallbackQuery, state: FSMContext):
    """Добавить пункт в план"""
    await callback.message.edit_text("Что добавим в план? 📋\n\n(Или нажми ❌ Отмена)", reply_markup=None)
    await bot.send_message(
        callback.from_user.id,
        "Напиши задачу:\n\n"
        "Или отправь голосовое сообщение 🎤\n\n"
        "(Или нажми ❌ Отмена)",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(BotStates.waiting_plan_item)
    await callback.answer()


@dp.callback_query(F.data == "plan_list")
async def callback_plan_list(callback: CallbackQuery):
    """Список плана"""
    items = await get_plan_items(callback.from_user.id, completed=None)
    
    if not items:
        await callback.message.edit_text("План пуст 📋", reply_markup=get_plan_list_keyboard(items))
    else:
        completed = sum(1 for item in items if item.completed)
        text = f"План на день 📋\n\nВыполнено: {completed}/{len(items)}"
        await callback.message.edit_text(text, reply_markup=get_plan_list_keyboard(items))
    
    await callback.answer()


@dp.callback_query(F.data.startswith("plan_view_"))
async def callback_plan_item_view(callback: CallbackQuery):
    """Просмотр пункта плана"""
    item_id = int(callback.data.split("_")[2])
    items = await get_plan_items(callback.from_user.id)
    item = next((i for i in items if i.id == item_id), None)
    
    if not item:
        await callback.answer("Пункт не найден")
        return
    
    text = f"{'✅' if item.completed else '⭕'} Пункт плана\n\n{item.text}"
    await callback.message.edit_text(text, reply_markup=get_plan_item_keyboard(item_id))
    await callback.answer()


@dp.callback_query(F.data.startswith("plan_") and F.data.endswith("_done"))
async def callback_plan_item_done(callback: CallbackQuery):
    """Переключить выполненность"""
    item_id = int(callback.data.split("_")[1])
    success = await toggle_plan_item(item_id, callback.from_user.id)
    
    if success:
        await callback.answer("✅ Обновлено!")
        items = await get_plan_items(callback.from_user.id, completed=None)
        await callback.message.edit_text(f"План обновлен 📋\n\nВыполнено: {sum(1 for i in items if i.completed)}/{len(items)}", reply_markup=get_plan_list_keyboard(items))
    else:
        await callback.answer("Ошибка ⚠️")


@dp.callback_query(lambda c: c.data and c.data.startswith("plan_") and c.data.endswith("_delete_confirm"))
async def callback_plan_delete_confirm(callback: CallbackQuery):
    """Подтверждение удаления пункта плана"""
    item_id = int(callback.data.split("_")[1])
    items = await get_plan_items(callback.from_user.id)
    item = next((i for i in items if i.id == item_id), None)
    
    if not item:
        await callback.answer("Пункт не найден")
        return
    
    await callback.message.edit_text(
        f"❓ Точно удалить задачу?\n\n{item.text}",
        reply_markup=get_plan_delete_confirm_keyboard(item_id)
    )
    await callback.answer()


@dp.callback_query(lambda c: c.data and c.data.startswith("plan_") and c.data.endswith("_delete") and not c.data.endswith("_delete_confirm"))
async def callback_plan_item_delete(callback: CallbackQuery):
    """Удалить пункт"""
    item_id = int(callback.data.split("_")[1])
    success = await delete_plan_item(item_id, callback.from_user.id)
    
    if success:
        await callback.answer("🗑️ Удалено")
        items = await get_plan_items(callback.from_user.id, completed=None)
        if items:
            completed = sum(1 for i in items if i.completed)
            await callback.message.edit_text(
                f"✅ Задача удалена\n\nПлан: {completed}/{len(items)} выполнено",
                reply_markup=get_plan_list_keyboard(items)
            )
        else:
            await callback.message.edit_text(
                "✅ Задача удалена\n\nПлан пуст 📋\n"
                "Хочешь добавить задачу?",
                reply_markup=get_plan_list_keyboard(items)
            )
    else:
        await callback.answer("Ошибка ⚠️")


# ==================== ГОЛОСОВЫЕ СООБЩЕНИЯ ====================

@dp.message(F.voice, StateFilter(None))
async def handle_voice_message(message: Message):
    """Обработка голосовых сообщений (когда не в состоянии)"""
    from voice_service import get_voice_service
    
    voice_service = get_voice_service()
    if not voice_service:
        await message.answer(
            "🎤 Голосовой ввод недоступен (не настроен OpenAI API)\n\n"
            "Напиши текст вместо этого 💛",
            reply_markup=get_main_keyboard()
        )
        return
    
    # Показываем, что обрабатываем
    processing_msg = await message.answer("🎤 Распознаю голос... ⏳", reply_markup=None)
    
    try:
        # Распознаем голос
        text = await voice_service.process_voice_message(message, bot)
        
        if not text or not text.strip():
            await processing_msg.edit_text(
                "Не удалось распознать речь 😅\n\n"
                "Попробуй ещё раз или напиши текст",
                reply_markup=get_main_keyboard()
            )
            return
        
        # Удаляем сообщение об обработке
        await processing_msg.delete()
        
        # Отправляем распознанный текст
        await message.answer(f"✍️ Распознано: {text}", reply_markup=None)
        
        # Обрабатываем как обычное текстовое сообщение
        message.text = text
        await handle_ai_message(message)
        
    except ValueError as e:
        error_msg = str(e)
        if "too long" in error_msg.lower():
            await processing_msg.edit_text(
                "Голосовое сообщение слишком длинное (макс. 1 час) ⏰\n\n"
                "Попробуй короче или напиши текст",
                reply_markup=get_main_keyboard()
            )
        else:
            await processing_msg.edit_text(
                "Не удалось обработать голосовое сообщение 😅\n\n"
                "Попробуй ещё раз или напиши текст",
                reply_markup=get_main_keyboard()
            )
    except Exception as e:
        logger.error(f"Error processing voice: {e}")
        await processing_msg.edit_text(
            "Упс, что-то пошло не так с голосом 😅\n\n"
            "Попробуй ещё раз или напиши текст",
            reply_markup=get_main_keyboard()
        )


# ==================== AI ОБРАБОТЧИК ====================

@dp.message(StateFilter(None))  # Only process when no active state  
async def handle_ai_message(message: Message):
    """Обработка сообщений с помощью AI (если не команда и не в состоянии)"""
    # Skip if no text
    if not message.text:
        return
    
    # Skip all commands - command handlers should process these first
    # This is a safety check in case command handlers don't catch them
    if message.text.startswith('/'):
        return
    
    # Skip button presses and keyboard commands
    if message.text in ["🔋 Меньше 40%", "⚡ Около 60%", "💪 Больше 80%",
                       "😌 Мягкий день", "🎯 Обычный день", "🚀 Активный день"]:
        return
    
    # Handle note deletion commands directly
    text_lower = message.text.lower() if message.text else ""
    if any(phrase in text_lower for phrase in ["удали все заметки", "очисти заметки", "удалить все заметки", "очистить заметки", "все"]):
        count = await delete_all_notes(message.from_user.id)
        if count > 0:
            await message.answer(f"✅ Удалено {count} заметок", reply_markup=get_main_keyboard())
        else:
            await message.answer("Заметок не было 🤷", reply_markup=get_main_keyboard())
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


# ==================== ЗАГРУЗКА СУЩЕСТВУЮЩИХ НАПОМИНАНИЙ ====================

async def load_existing_reminders():
    """Загрузить существующие напоминания из БД в планировщик"""
    try:
        from database import async_session, Reminder, User
        from sqlalchemy import select
        
        async with async_session() as session:
            # Получаем все активные напоминания с информацией о пользователе
            result = await session.execute(
                select(Reminder, User.telegram_id)
                .join(User, Reminder.user_id == User.id)
                .where(Reminder.completed == False)
                .where(Reminder.when_datetime > datetime.utcnow())
            )
            
            reminders_with_users = result.all()
            
            count = 0
            for row in reminders_with_users:
                reminder = row[0]  # Reminder object
                telegram_id = row[1]  # User.telegram_id
                
                # Конвертируем в timezone-aware datetime
                when = pytz.UTC.localize(reminder.when_datetime) if reminder.when_datetime.tzinfo is None else reminder.when_datetime
                await scheduler.add_reminder(telegram_id, reminder.text, when)
                count += 1
            
            if count > 0:
                print(f"✅ Загружено {count} активных напоминаний в планировщик ⏰")
            else:
                print("ℹ️  Активных напоминаний нет")
    except Exception as e:
        import traceback
        print(f"⚠️  Ошибка загрузки напоминаний: {e}")
        traceback.print_exc()


# ==================== ЗАПУСК БОТА ====================

async def main():
    """Главная функция"""
    print("Запуск бота SDVGaid... 🤖")
    
    # Инициализация AI
    print(f"AI провайдер: {ai_service.current_provider.upper()} 🤖")
    
    # Инициализация БД
    await init_db()
    print("База данных инициализирована ✅")
    
    # Загружаем существующие напоминания в планировщик
    await load_existing_reminders()
    
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

