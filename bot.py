"""Главный файл Telegram-бота SDVGaid"""
# Standard library
import asyncio
import logging
from datetime import datetime, timedelta
import pytz

# Aiogram
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, StateFilter, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery, Voice

# Config and initialization
from config import BOT_TOKEN, POMODORO_WORK_TIME, POMODORO_BREAK_TIME, QUIET_MODE_DURATION
from database import init_db

# Database helpers - grouped by domain
from db_helpers import (
    # User
    get_or_create_user,
    # Goals
    save_energy_level, save_goal, get_todays_goal, complete_goal,
    # Notes
    save_note, get_user_notes, delete_note, delete_all_notes,
    # Evening check-in
    save_evening_checkin,
    # Energy stats
    get_energy_stats_week,
    # User state
    get_user_state, set_quiet_mode, disable_quiet_mode,
    # Reminders
    get_all_reminders, delete_reminder, complete_reminder,
    # Plan
    get_plan_items, add_plan_item, delete_plan_item, toggle_plan_item,
    # Rating and history
    set_day_rating, get_daily_summary, get_days_history
)

# UI
from keyboards import (
    get_energy_keyboard, get_day_type_keyboard, get_pomodoro_keyboard,
    get_main_keyboard, get_goal_confirmation_keyboard, get_goal_completion_keyboard,
    get_reminders_list_keyboard, get_reminder_keyboard, get_reminder_delete_confirm_keyboard,
    get_plan_list_keyboard, get_plan_item_keyboard, get_plan_delete_confirm_keyboard, get_cancel_keyboard
)

# Services
from ai_service import ai_service
from scheduler import ReminderScheduler
from ai_functions import FunctionHandler
from translations import translate, get_user_language
from bot_helpers import get_user_and_lang, get_lang_from_user_id

# Logger
logger = logging.getLogger(__name__)


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
    waiting_goal_pomodoros = State()  # Оценка цели в помидорах
    waiting_note = State()
    waiting_evening_worked = State()
    waiting_evening_tired = State()
    waiting_evening_helped = State()
    waiting_plan_item = State()
    waiting_reminder_text = State()
    waiting_day_rating = State()  # Ожидание оценки дня


# Словарь для хранения активных Pomodoro сессий
active_pomodoros = {}


# ==================== ОБРАБОТЧИКИ КОМАНД ====================

@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Welcome message and start"""
    await state.clear()
    
    # Get user and language
    user, lang = await get_user_and_lang(message.from_user)
    greeting = translate("greeting_simple", lang)
    
    await message.answer(greeting, reply_markup=get_main_keyboard(lang))


@dp.message(Command("help"))
async def cmd_help(message: Message, state: FSMContext):
    """Показать справку по командам"""
    await state.clear()
    
    help_text = """💬 Просто пиши мне, я пойму! 💛

🎯 Кнопки:
• 💚 Помощь сейчас — поддержка когда трудно
• 🎯 Главная цель — одно дело на сегодня
• 📋 План — задачи дня
• 🍅 Фокус — таймер 25 минут
• 📝 Заметки — сохранить мысль
• 💬 Помощь — эта справка

📝 Можно просто писать:
• "запиши купить молоко"
• "напомни позвонить через час"
• "добавь в план уборка"
• "я застрял с отчётом" → помогу разбить

🎤 Голосовой ввод работает везде!

💚 Помни: ты не обязан быть идеальным."""
    
    await message.answer(help_text, reply_markup=get_main_keyboard())


@dp.message(lambda m: m.text and "💚 Помощь сейчас" in m.text)
async def quick_help(message: Message, state: FSMContext):
    """Мгновенная помощь при стрессе/перегрузке"""
    await state.clear()
    
    # Проверяем контекст - есть ли задачи, цели
    from db_helpers import get_todays_goal, get_plan_items, get_user_notes
    
    user = await get_or_create_user(message.from_user.id, None, None)
    goal = await get_todays_goal(user.id)
    plan_items = await get_plan_items(user.id)
    completed_today = sum(1 for item in plan_items if item.completed)
    total_tasks = len(plan_items)
    
    # Персонализированная поддержка
    support_text = "💚 Чем могу помочь?\n\n"
    
    if not goal:
        support_text += "• Помочь выбрать одно дело на сегодня?\n"
    elif completed_today > 0:
        support_text += f"✅ У тебя уже {completed_today} задача выполнена! Это много 💛\n\n"
        support_text += f"• Продолжить работу?\n"
        support_text += f"• Отдохнуть?\n"
    elif total_tasks == 0:
        support_text += "• Добавить первую задачу?\n"
        support_text += "• Просто отдохнуть?\n"
    else:
        support_text += f"• Помочь начать ({total_tasks} задач в плане)\n"
        support_text += "• Разбить задачу на шаги?\n"
    
    support_text += "\n💚 Просто напиши что чувствуешь, я поддержу."
    
    # Inline кнопки для быстрых действий
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    quick_help_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎯 Поставить цель", callback_data="quick_goal")],
            [InlineKeyboardButton(text="📋 Добавить задачу", callback_data="quick_plan")],
            [InlineKeyboardButton(text="🍅 Запустить фокус", callback_data="quick_focus")],
            [InlineKeyboardButton(text="😌 Отдохнуть (тишина)", callback_data="quick_quiet")],
        ]
    )
    
    await message.answer(support_text, reply_markup=quick_help_keyboard)


@dp.message(Command("goal"))
@dp.message(lambda m: m.text and ("🎯 Главная цель" in m.text or "Главная цель" in m.text))
async def cmd_goal(message: Message, state: FSMContext):
    """Set daily goal"""
    user, lang = await get_user_and_lang(message.from_user)
    todays_goal = await get_todays_goal(user.id)
    
    # Get today's energy level to adapt suggestions
    from db_helpers import get_todays_energy
    energy = await get_todays_energy(user.id)
    
    # Adapt goal question based on energy
    if energy and energy < 40:
        goal_prompt = translate("goal_question_low_energy", lang)
    elif energy and energy >= 80:
        goal_prompt = translate("goal_question_high_energy", lang)
    else:
        goal_prompt = translate("goal_question", lang)
    
    if todays_goal:
        # Показываем цель с прогрессом помидоров
        text = f"""🎯 Твоя цель на сегодня:

{todays_goal.goal_text}"""
        
        if todays_goal.estimated_pomodoros:
            progress_emoji = "🎉" if todays_goal.completed_pomodoros >= todays_goal.estimated_pomodoros else "🍅"
            text += f"\n\n{progress_emoji} Помидоры: {todays_goal.completed_pomodoros}/{todays_goal.estimated_pomodoros}"
            if todays_goal.completed_pomodoros < todays_goal.estimated_pomodoros:
                remaining = todays_goal.estimated_pomodoros - todays_goal.completed_pomodoros
                text += f"\nОсталось: {remaining} помидоров"
        else:
            text += f"\n\n💡 Можешь добавить оценку в помидорах"
        
        if todays_goal.completed:
            text += "\n\n✅ Выполнено!"
        
        text += "\n\n" + translate("goal_change_question", lang)
        await message.answer(text, reply_markup=get_goal_confirmation_keyboard())
    else:
        # Show goal prompt with energy adaptation
        await message.answer(
            goal_prompt + "\n\n" + translate("goal_hint", lang),
            reply_markup=get_cancel_keyboard(lang)
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
        goal_text = message.text.strip()
        
        # Спрашиваем про помидоры
        await message.answer(
            f"Понял! 🎯\n\n{goal_text}\n\n"
            f"Сколько помидоров (25 минут) понадобится? 🍅\n\n"
            f"Можешь написать число или 'пропустить'",
            reply_markup=get_cancel_keyboard()
        )
        
        # Сохраняем текст цели во временном хранилище
        await state.update_data(goal_text=goal_text)
        await state.set_state(BotStates.waiting_goal_pomodoros)
        
    except Exception as e:
        logger.error(f"Error processing goal: {e}", exc_info=True)
        await message.answer("Упс, не получилось обработать 😅 Попробуй ещё раз?", reply_markup=get_main_keyboard())
        await state.clear()


@dp.message(StateFilter(BotStates.waiting_goal_pomodoros))
async def process_goal_pomodoros(message: Message, state: FSMContext):
    """Обработка оценки цели в помидорах"""
    # Обработка отмены
    if message.text and message.text.strip().lower() in ["❌ отмена", "отмена", "пропустить", "skip", "/cancel"]:
        data = await state.get_data()
        goal_text = data.get("goal_text", "")
        if goal_text:
            goal = await save_goal(message.from_user.id, goal_text)
            await message.answer(
                f"✅ Цель сохранена:\n\n{goal.goal_text}\n\n💡 Можешь позже добавить оценку в помидорах через /goal",
                reply_markup=get_main_keyboard()
            )
        await state.clear()
        return
    
    # Парсим число помидоров
    estimated_pomodoros = None
    try:
        text_lower = message.text.strip().lower()
        if any(word in text_lower for word in ["помидор", "томат", "pomodoro"]):
            # Извлекаем число
            import re
            numbers = re.findall(r'\d+', message.text)
            if numbers:
                estimated_pomodoros = int(numbers[0])
        else:
            # Просто число
            estimated_pomodoros = int(message.text.strip())
            
        if estimated_pomodoros and estimated_pomodoros > 0:
            if estimated_pomodoros > 20:
                await message.answer(
                    f"20 помидоров это уже 8+ часов! 💪\n\nМожет разобьём на несколько дней?\n\nНапиши число меньше или 'пропустить'",
                    reply_markup=get_cancel_keyboard()
                )
                return
    except (ValueError, AttributeError):
        # Не число - пропускаем
        estimated_pomodoros = None
    
    try:
        data = await state.get_data()
        goal_text = data.get("goal_text", "")
        
        if not goal_text:
            await message.answer("Что-то пошло не так 😅 Начни снова: /goal", reply_markup=get_main_keyboard())
            await state.clear()
            return
        
        goal = await save_goal(message.from_user.id, goal_text, estimated_pomodoros)
        
        if estimated_pomodoros:
            text = f"""✅ Цель сохранена! 🎯

{goal.goal_text}

🍅 Оценка: {estimated_pomodoros} помидоров ({estimated_pomodoros * 25} минут)

Прогресс: 0/{estimated_pomodoros} 🍅
Начни первый помидор: /focus"""
        else:
            text = f"""✅ Цель сохранена! 🎯

{goal.goal_text}

💡 Можешь позже добавить оценку в помидорах"""
        
        await message.answer(text, reply_markup=get_main_keyboard())
    except Exception as e:
        logger.error(f"Error saving goal: {e}", exc_info=True)
        await message.answer("Упс, не получилось сохранить 😅 Попробуй ещё раз?", reply_markup=get_main_keyboard())
    finally:
        await state.clear()


@dp.message(Command("focus"))
@dp.message(lambda m: m.text and ("🍅 Фокус" in m.text or "Фокус" in m.text))
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
    
    # Проверяем есть ли цель или задачи
    from db_helpers import get_todays_goal, get_plan_items
    user = await get_or_create_user(user_id, None, None)
    goal = await get_todays_goal(user.id)
    plan_items = await get_plan_items(user.id, completed=False)
    
    focus_text = "Поехали! 25 минут фокуса 🍅"
    if goal:
        focus_text += f"\n\n🎯 На чём сфокусируемся?\n{goal.goal_text}"
    elif plan_items:
        first_task = plan_items[0]
        focus_text += f"\n\n📋 Начинаем с:\n{first_task.text}"
    
    await message.answer(focus_text, reply_markup=None)
    await start_pomodoro(user_id, message.chat.id)


async def start_pomodoro(user_id: int, chat_id: int):
    """Запустить Pomodoro таймер"""
    active_pomodoros[user_id] = True
    
    # Увеличиваем счетчик помидоров для цели
    from db_helpers import increment_goal_pomodoro, get_todays_goal
    user = await get_or_create_user(user_id, None, None)
    goal = await get_todays_goal(user.id)
    
    # Рабочее время
    await asyncio.sleep(POMODORO_WORK_TIME)
    
    if user_id not in active_pomodoros:
        return
    
    # Обновляем прогресс помидоров
    if goal and goal.estimated_pomodoros:
        await increment_goal_pomodoro(user.id)
        goal = await get_todays_goal(user.id)  # Обновляем данные
    
    # Показываем прогресс
    progress_msg = "Стоп! Перерыв 5 минут 🌿\n\n"
    if goal and goal.estimated_pomodoros:
        progress_msg += f"🍅 Прогресс: {goal.completed_pomodoros}/{goal.estimated_pomodoros} помидоров\n\n"
        if goal.completed_pomodoros >= goal.estimated_pomodoros:
            progress_msg += "🎉 Все помидоры выполнены!\n\n"
    
    progress_msg += "Что-то налить? Воды попить? 🌊"
    
    await bot.send_message(chat_id, progress_msg)
    
    # Время перерыва
    await asyncio.sleep(POMODORO_BREAK_TIME)
    
    if user_id not in active_pomodoros:
        return
    
    # Предлагаем продолжить
    continue_msg = "Перерыв окончен ⏰\n\nПродолжаем?"
    if goal and goal.estimated_pomodoros and goal.completed_pomodoros < goal.estimated_pomodoros:
        remaining = goal.estimated_pomodoros - goal.completed_pomodoros
        continue_msg += f"\n\n🍅 Осталось {remaining} помидоров"
    
    await bot.send_message(chat_id, continue_msg, reply_markup=get_pomodoro_keyboard())


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
@dp.message(lambda m: m.text and ("📝 Заметки" in m.text or "Заметки" in m.text))
async def cmd_note(message: Message, state: FSMContext):
    """Добавить заметку"""
    await message.answer(
        "Что записать? 📝\n\n"
        "Можешь написать или отправить голосовое 🎤",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(BotStates.waiting_note)


@dp.message(StateFilter(BotStates.waiting_note))
async def process_note(message: Message, state: FSMContext):
    """Обработка заметки"""
    try:
        # Обработка отмены (ПЕРВЫМ ДЕЛОМ)
        cancel_texts = ["❌ Отмена", "отмена", "Отмена", "/cancel", "/start"]
        if message.text and message.text.strip() in cancel_texts:
            await state.clear()
            await message.answer("Окей, заметку можно добавить позже 💛", reply_markup=get_main_keyboard())
            return
        
        # Обработка команд - очищаем состояние и позволяем команде обработаться
        if message.text and message.text.startswith('/'):
            await state.clear()
            return
        
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
                        await processing_msg.edit_text("Не удалось распознать речь 😅\n\nПопробуй ещё раз или нажми ❌ Отмена", reply_markup=get_cancel_keyboard())
                        return
                except Exception as e:
                    logger.error(f"Voice recognition error in note: {e}", exc_info=True)
                    await processing_msg.edit_text("Не удалось обработать голос 😅\n\nПопробуй написать текст или нажми ❌ Отмена", reply_markup=get_cancel_keyboard())
                    return
            else:
                await message.answer("Голосовой ввод недоступен. Напиши текст 📝\n\nИли нажми ❌ Отмена", reply_markup=get_cancel_keyboard())
                return
        
        # Валидация
        if not message.text or not message.text.strip():
            await message.answer("Пожалуйста, напиши текст заметки 📝\n\nИли отправь голосовое сообщение 🎤\n\nИли нажми ❌ Отмена", reply_markup=get_cancel_keyboard())
            return
        
        if len(message.text.strip()) > 500:
            await message.answer("Заметка слишком длинная (макс. 500 символов) 📝\n\nПопробуй короче или нажми ❌ Отмена", reply_markup=get_cancel_keyboard())
            return
        
        # Сохраняем заметку
        note = await save_note(message.from_user.id, message.text.strip())
        await message.answer(f"✅ Запомнил:\n\n{note.text}", reply_markup=get_main_keyboard())
        
    except Exception as e:
        logger.error(f"Error in process_note: {e}", exc_info=True)
        await message.answer("Упс, не получилось сохранить 😅 Попробуй ещё раз?", reply_markup=get_main_keyboard())
    finally:
        await state.clear()


@dp.message(Command("notes"))
async def cmd_notes(message: Message, state: FSMContext):
    """Показать все заметки"""
    user = await get_or_create_user(message.from_user.id, None, None)
    notes = await get_user_notes(user.id)
    
    if not notes:
        await message.answer(
            "Заметок пока нет 📝\n\n"
            "✨ Просто напиши: 'запиши купить молоко'\n"
            "Или используй кнопку '📝 Заметки'\n\n"
            "💡 Заметки — это твоя внешняя память. Записывай что угодно!",
            reply_markup=get_main_keyboard()
        )
        return
    
    # Показываем последние 10 заметок (чтобы не перегружать)
    recent_notes = notes[:10]
    
    text = f"📝 Твои заметки (последние {len(recent_notes)} из {len(notes)}):\n\n"
    for i, note in enumerate(recent_notes, 1):
        # Форматируем дату
        date_str = note.created_at.strftime("%d.%m %H:%M") if note.created_at else ""
        text += f"{i}. {note.text}"
        if date_str:
            text += f" ({date_str})"
        text += "\n"
    
    if len(notes) > 10:
        text += f"\n... и ещё {len(notes) - 10} заметок\n"
    
    text += "\n💡 Напиши 'найди <слово>' для поиска по заметкам"
    text += "\n🗑 Для удаления напиши: 'удали все заметки'"
    
    await message.answer(text, reply_markup=get_main_keyboard())


@dp.message(Command("evening"))
async def cmd_evening(message: Message, state: FSMContext):
    """Evening check-in"""
    user, lang = await get_user_and_lang(message.from_user)
    await message.answer(
        translate("evening_question", lang),
        reply_markup=get_cancel_keyboard(lang)
    )
    await state.set_state(BotStates.waiting_evening_worked)


@dp.message(StateFilter(BotStates.waiting_evening_worked))
async def process_evening_worked(message: Message, state: FSMContext):
    """Обработка первого вопроса чек-ина"""
    try:
        # Обработка отмены
        cancel_texts = ["❌ Отмена", "отмена", "Отмена", "/cancel", "/start"]
        if message.text and message.text.strip() in cancel_texts:
            await state.clear()
            await message.answer("Окей, чек-ин можно сделать позже 💛", reply_markup=get_main_keyboard())
            return
        
        # Обработка команд
        if message.text and message.text.startswith('/'):
            await state.clear()
            return
        
        # Валидация
        if not message.text or not message.text.strip():
            await message.answer("Пожалуйста, напиши что получилось сделать 📝\n\nИли нажми ❌ Отмена", reply_markup=get_cancel_keyboard())
            return
        
        await state.update_data(what_worked=message.text.strip())
        await message.answer("Что вымотало сегодня?", reply_markup=get_cancel_keyboard())
        await state.set_state(BotStates.waiting_evening_tired)
    except Exception as e:
        logger.error(f"Error in process_evening_worked: {e}", exc_info=True)
        await state.clear()
        await message.answer("Упс, что-то пошло не так 😅 Попробуй /evening ещё раз", reply_markup=get_main_keyboard())


@dp.message(StateFilter(BotStates.waiting_evening_tired))
async def process_evening_tired(message: Message, state: FSMContext):
    """Обработка второго вопроса чек-ина"""
    try:
        # Обработка отмены
        cancel_texts = ["❌ Отмена", "отмена", "Отмена", "/cancel", "/start"]
        if message.text and message.text.strip() in cancel_texts:
            await state.clear()
            await message.answer("Окей, чек-ин можно сделать позже 💛", reply_markup=get_main_keyboard())
            return
        
        # Обработка команд
        if message.text and message.text.startswith('/'):
            await state.clear()
            return
        
        # Валидация
        if not message.text or not message.text.strip():
            await message.answer("Пожалуйста, напиши что вымотало 📝\n\nИли нажми ❌ Отмена", reply_markup=get_cancel_keyboard())
            return
        
        await state.update_data(what_tired=message.text.strip())
        await message.answer("И последнее: что помогло немного сегодня? 💛", reply_markup=get_cancel_keyboard())
        await state.set_state(BotStates.waiting_evening_helped)
    except Exception as e:
        logger.error(f"Error in process_evening_tired: {e}", exc_info=True)
        await state.clear()
        await message.answer("Упс, что-то пошло не так 😅 Попробуй /evening ещё раз", reply_markup=get_main_keyboard())


@dp.message(StateFilter(BotStates.waiting_evening_helped))
async def process_evening_helped(message: Message, state: FSMContext):
    """Обработка третьего вопроса чек-ина"""
    try:
        # Обработка отмены
        cancel_texts = ["❌ Отмена", "отмена", "Отмена", "/cancel", "/start"]
        if message.text and message.text.strip() in cancel_texts:
            await state.clear()
            await message.answer("Окей, чек-ин можно сделать позже 💛", reply_markup=get_main_keyboard())
            return
        
        # Обработка команд
        if message.text and message.text.startswith('/'):
            await state.clear()
            return
        
        # Валидация
        if not message.text or not message.text.strip():
            await message.answer("Пожалуйста, напиши что помогло 📝\n\nИли нажми ❌ Отмена", reply_markup=get_cancel_keyboard())
            return
        
        data = await state.get_data()
        
        user, lang = await get_user_and_lang(message.from_user)
        
        await save_evening_checkin(
            message.from_user.id,
            what_worked=data.get('what_worked', ''),
            what_tired=data.get('what_tired', ''),
            what_helped=message.text.strip()
        )
        
        # Проверяем главное дело дня
        todays_goal = await get_todays_goal(user.id)
        
        if todays_goal and not todays_goal.completed:
            await message.answer(
                translate("evening_thanks", lang) + f"\n\n💬 {translate('goal_question', lang)}\n{todays_goal.goal_text}\n\n" + translate("goal_question", lang), 
                reply_markup=get_goal_completion_keyboard()
            )
        else:
            # Ask for day rating
            await message.answer(
                translate("evening_thanks", lang),
                reply_markup=get_cancel_keyboard(lang)
            )
    except Exception as e:
        logger.error(f"Error in process_evening_helped: {e}", exc_info=True)
        await message.answer("Упс, не получилось сохранить чек-ин 😅 Попробуй ещё раз?", reply_markup=get_main_keyboard())
    finally:
        await state.clear()


@dp.message(StateFilter(BotStates.waiting_day_rating))
async def process_day_rating(message: Message, state: FSMContext):
    """Обработка оценки дня"""
    try:
        # Обработка отмены
        cancel_texts = ["❌ Отмена", "отмена", "Отмена", "/cancel", "/start", "пропустить", "skip"]
        if message.text and message.text.strip().lower() in cancel_texts:
            await state.clear()
            user = await get_or_create_user(message.from_user.id, None, None)
            todays_goal = await get_todays_goal(user.id)
            
            if todays_goal and not todays_goal.completed:
                await message.answer(
                    f"💫 Спасибо за чек-ин!\n\nКстати, помнишь про цель:\n{todays_goal.goal_text}\n\nЧто с ней?", 
                    reply_markup=get_goal_completion_keyboard()
                )
            else:
                await message.answer(
                    "Спасибо за чек-ин! 💛\n\nСпокойной ночи! 🌙",
                    reply_markup=get_main_keyboard()
                )
            return
        
        # Парсим оценку
        rating = None
        try:
            rating_text = message.text.strip()
            rating = int(rating_text)
            if rating < 1 or rating > 10:
                await message.answer(
                    "Оценка должна быть от 1 до 10 😊\n\nПопробуй ещё раз или напиши 'пропустить'",
                    reply_markup=get_cancel_keyboard()
                )
                return
        except (ValueError, AttributeError):
            await message.answer(
                "Пожалуйста, напиши число от 1 до 10 😊\n\nНапример: 7\n\nИли напиши 'пропустить'",
                reply_markup=get_cancel_keyboard()
            )
            return
        
        # Сохраняем оценку
        user = await get_or_create_user(message.from_user.id, None, None)
        await set_day_rating(user.id, date=None, rating=rating)
        
        # Генерируем сообщение в зависимости от оценки
        if rating >= 8:
            rating_msg = f"🎉 Отлично! Оценка {rating}/10"
        elif rating >= 6:
            rating_msg = f"👍 Хорошо! Оценка {rating}/10"
        elif rating >= 4:
            rating_msg = f"💛 Нормально! Оценка {rating}/10"
        else:
            rating_msg = f"💙 Сложно, но ты справился! Оценка {rating}/10"
        
        # Проверяем главное дело дня
        todays_goal = await get_todays_goal(user.id)
        
        final_text = f"{rating_msg}\n\nСпасибо за чек-ин! 💛"
        
        if todays_goal and not todays_goal.completed:
            final_text += f"\n\nКстати, помнишь про цель:\n{todays_goal.goal_text}\n\nЧто с ней?"
            await message.answer(final_text, reply_markup=get_goal_completion_keyboard())
        else:
            final_text += "\n\nСпокойной ночи! 🌙"
            await message.answer(final_text, reply_markup=get_main_keyboard())
        
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error in process_day_rating: {e}", exc_info=True)
        await state.clear()
        user, lang = await get_user_and_lang(message.from_user)
        await message.answer(translate("error_generic", lang), reply_markup=get_main_keyboard(lang))


@dp.message(Command("rating"))
async def cmd_rating(message: Message, state: FSMContext):
    """Rate today"""
    user, lang = await get_user_and_lang(message.from_user)
    today_goal = await get_todays_goal(user.id)
    
    if today_goal and today_goal.day_rating:
        await message.answer(
            translate("already_rated", lang, rating=today_goal.day_rating),
            reply_markup=get_cancel_keyboard(lang)
        )
    else:
        await message.answer(
            translate("rating_question", lang),
            reply_markup=get_cancel_keyboard(lang)
        )
    
    await state.set_state(BotStates.waiting_day_rating)


@dp.message(Command("history"))
async def cmd_history(message: Message, state: FSMContext):
    """Show days history"""
    user, lang = await get_user_and_lang(message.from_user)
    days = await get_days_history(user.id, limit=30)
    
    if not days:
        await message.answer(
            translate("history_empty", lang),
            reply_markup=get_main_keyboard()
        )
        return
    
    # Показываем короткий формат по умолчанию
    text = translate("history_title", lang) + "\n\n"
    for i, day in enumerate(days[:10], 1):  # Показываем первые 10
        date_str = day['date'].strftime("%d.%m") if isinstance(day['date'], datetime) else str(day['date'])
        rating_str = f"⭐ {day['rating']}/10" if day['rating'] else "—"
        plan_str = f"📋 {day['plan_completed']}/{day['plan_count']}" if day['plan_count'] > 0 else ""
        goal_str = "✅" if day.get('goal_completed') else "⭕" if day.get('goal') else ""
        pomodoros_str = f"🍅 {day['pomodoros']}" if day.get('pomodoros') else ""
        
        text += f"{i}. {date_str} {rating_str}"
        if plan_str:
            text += f" {plan_str}"
        if pomodoros_str:
            text += f" {pomodoros_str}"
        text += f" {goal_str}\n"
    
    if len(days) > 10:
        text += translate("history_more", lang, count=len(days) - 10)
    
    text += "\n\n" + translate("history_hint", lang)
    
    await message.answer(text, reply_markup=get_main_keyboard())
    await state.update_data(history_format="short")


@dp.callback_query(F.data == "goal_confirm")
async def goal_confirm(callback: CallbackQuery):
    """Подтвердить текущую цель"""
    user = await get_or_create_user(callback.from_user.id, None, None)
    goal = await get_todays_goal(user.id)
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
    user = await get_or_create_user(callback.from_user.id, None, None)
    goal = await get_todays_goal(user.id)
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
    """Handle energy level selection"""
    user, lang = await get_user_and_lang(message.from_user)
    
    # Map energy buttons using translations
    energy_map = {
        translate("energy_less_40", lang).lower(): 40,
        translate("energy_around_60", lang).lower(): 60,
        translate("energy_more_80", lang).lower(): 80,
    }
    
    # Check exact match and lowercase
    energy_level = energy_map.get(message.text.lower())
    
    if not energy_level:
        await message.answer(
            translate("energy_select_above", lang),
            reply_markup=get_energy_keyboard(lang)
        )
        return
    
    # Save energy level
    await save_energy_level(user.id, energy_level)
    
    # Give adaptive advice based on energy
    if energy_level < 40:
        advice = translate("energy_low_advice", lang)
    elif energy_level < 60:
        advice = translate("energy_medium_advice", lang)
    else:
        advice = translate("energy_high_advice", lang)
    
    await message.answer(
        translate("energy_saved", lang, level=energy_level) + "\n\n" + advice,
        reply_markup=get_main_keyboard(lang)
    )
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
        logger.error(f"Error in /reminders: {e}", exc_info=True)
        await message.answer("Упс, не получилось загрузить напоминания 😅 Попробуй ещё раз?", reply_markup=get_main_keyboard())


@dp.callback_query(F.data.startswith("rem_view_"))
async def callback_reminder_view(callback: CallbackQuery):
    """Просмотр напоминания"""
    try:
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
    except Exception as e:
        logger.error(f"Error in callback_reminder_view: {e}", exc_info=True)
        await callback.answer("Ошибка ⚠️", show_alert=True)


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
    try:
        reminder_id = int(callback.data.split("_")[1])
        success = await complete_reminder(reminder_id, callback.from_user.id)
        
        if success:
            await callback.answer("✅ Выполнено!")
            # Refresh list
            reminders = await get_all_reminders(callback.from_user.id, completed=False)
            await callback.message.edit_text("Напоминание выполнено ✅", reply_markup=get_reminders_list_keyboard(reminders))
        else:
            await callback.answer("Ошибка ⚠️")
    except Exception as e:
        logger.error(f"Error in callback_reminder_done: {e}", exc_info=True)
        await callback.answer("Ошибка ⚠️", show_alert=True)


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
    try:
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
    except Exception as e:
        logger.error(f"Error in callback_reminder_delete: {e}", exc_info=True)
        await callback.answer("Ошибка ⚠️", show_alert=True)


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
    try:
        # Обработка отмены (ПЕРВЫМ ДЕЛОМ - проверяем разные варианты)
        cancel_texts = ["❌ Отмена", "отмена", "Отмена", "/cancel", "/start"]
        if message.text and message.text.strip() in cancel_texts:
            logger.info(f"User {message.from_user.id} cancelled reminder creation")
            await state.clear()
            await message.answer("Окей, напоминание можно добавить позже 💛", reply_markup=get_main_keyboard())
            return
        
        # Обработка команд - очищаем состояние и позволяем команде обработаться
        if message.text and message.text.startswith('/'):
            await state.clear()
            # Позволяем команде обработаться обычным обработчиком
            return
        
        # Обработка голосового сообщения
        if message.voice:
            from voice_service import get_voice_service
            voice_service = get_voice_service()
            if voice_service:
                processing_msg = await message.answer("🎤 Распознаю голос... ⏳")
                try:
                    text = await voice_service.process_voice_message(message, bot)
                    if text and text.strip():
                        # Удаляем сообщение об обработке
                        await processing_msg.delete()
                        # Показываем распознанный текст
                        await message.answer(f"✍️ Распознано: {text}", reply_markup=None)
                        # Устанавливаем текст для дальнейшей обработки
                        message.text = text
                        logger.info(f"Voice recognized for reminder: {text}")
                    else:
                        await processing_msg.edit_text("Не удалось распознать речь 😅\n\nПопробуй ещё раз или нажми ❌ Отмена", reply_markup=get_cancel_keyboard())
                        return
                except Exception as e:
                    logger.error(f"Voice recognition error: {e}", exc_info=True)
                    await processing_msg.edit_text("Не удалось обработать голос 😅\n\nПопробуй написать текст или нажми ❌ Отмена", reply_markup=get_cancel_keyboard())
                    return
            else:
                await message.answer("Голосовой ввод недоступен. Напиши текст 📝\n\nИли нажми ❌ Отмена", reply_markup=get_cancel_keyboard())
                return
        
        # Валидация - проверяем наличие текста
        if not message.text or not message.text.strip():
            await message.answer("Пожалуйста, напиши текст напоминания ⏰\n\nИли отправь голосовое сообщение 🎤\n\nИли нажми ❌ Отмена", reply_markup=get_cancel_keyboard())
            return
        
        # Обрабатываем через AI, который создаст напоминание
        reminder_text = message.text.strip()
        logger.info(f"Processing reminder request: {reminder_text} for user {message.from_user.id}")
        
        # Добавляем контекст, чтобы AI точно понял, что нужно создать напоминание
        # Исправляем возможные опечатки в распознанном тексте
        reminder_text_normalized = reminder_text.replace("поминание", "напоминание").replace("Поминание", "Напоминание")
        
        # Добавляем явный контекст для AI - он должен использовать функцию create_reminder
        ai_prompt = f"Пользователь хочет создать напоминание: {reminder_text_normalized}. Используй функцию create_reminder для создания напоминания."
        
        processing_ai_msg = await message.answer("⏳ Обрабатываю...", reply_markup=None)
        try:
            response = await ai_service.process_message(ai_prompt, message.from_user.id, None)
            await processing_ai_msg.delete()
            await message.answer(response, reply_markup=get_main_keyboard())
            logger.info(f"Reminder processing completed. Response: {response[:100]}")
                
        except Exception as e:
            logger.error(f"Error in AI processing for reminder: {e}", exc_info=True)
            await processing_ai_msg.delete()
            raise  # Re-raise to be caught by outer try-except
        
    except Exception as e:
        logger.error(f"Error in process_reminder_text: {e}", exc_info=True)
        await message.answer(
            "Упс, не получилось создать напоминание 😅\n\nПопробуй ещё раз или используй команду /reminders",
            reply_markup=get_main_keyboard()
        )
    finally:
        # Всегда очищаем состояние после обработки
        await state.clear()


# ==================== DAILY PLAN ====================

@dp.message(Command("plan"))
@dp.message(lambda m: m.text and ("📋 План" in m.text or "План" in m.text))
async def cmd_plan(message: Message, state: FSMContext):
    """Show daily plan"""
    try:
        user, lang = await get_user_and_lang(message.from_user)
        items = await get_plan_items(user.id, completed=None)
        
        # Get energy to suggest appropriate number of tasks
        from db_helpers import get_todays_energy
        energy = await get_todays_energy(user.id)
        
        # Initialize energy_note
        energy_note = ""
        
        if not items:
            # Adapt suggestion based on energy
            if energy and energy < 40:
                suggestion = translate("plan_empty_low_energy", lang)
            elif energy and energy >= 80:
                suggestion = translate("plan_empty_high_energy", lang)
            else:
                suggestion = translate("plan_empty", lang)
            
            await message.answer(
                suggestion,
                reply_markup=get_plan_list_keyboard(items)
            )
            # Не устанавливаем состояние здесь - пользователь должен нажать кнопку
        else:
            # Add energy-based comment if needed
            if energy and energy < 40 and len(items) > 2:
                energy_note = "\n\n" + translate("plan_energy_note_low", lang)
            elif energy and energy >= 80 and len(items) < 3:
                energy_note = "\n\n" + translate("plan_energy_note_high", lang)
            
            completed = sum(1 for item in items if item.completed)
            # Показываем прогресс визуально
            progress_emoji = "🎉" if completed == len(items) else "💪" if completed > 0 else "✨"
            text = translate("plan_title", lang) + f"\n\n{progress_emoji} {translate('plan_completed', lang)}: {completed}/{len(items)}\n"
            
            # Если есть прогресс - хвалим!
            if completed > 0:
                if completed == len(items):
                    text += translate("plan_all_done", lang) + "\n\n"
                elif completed >= len(items) / 2:
                    text += translate("plan_half_done", lang, count=completed) + "\n\n"
                else:
                    text += translate("plan_some_done", lang, count=completed) + "\n\n"
            
            text += energy_note
            
            await message.answer(text, reply_markup=get_plan_list_keyboard(items))
    except Exception as e:
        logger.error(f"Error in /plan: {e}", exc_info=True)
        user, lang = await get_user_and_lang(message.from_user)
        await message.answer(translate("error_generic", lang), reply_markup=get_main_keyboard(lang))


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
        task_text = message.text.strip()
        
        # Если задача большая (более 5 слов), можем предложить разбить
        user = await get_or_create_user(message.from_user.id, None, None)
        word_count = len(task_text.split())
        if word_count > 5:  # Большая задача
            # Добавляем как есть, но можем предложить разбить позже
            item = await add_plan_item(user.id, task_text)
            await message.answer(
                f"✅ Добавлено в план:\n\n{item.text}\n\n"
                f"💡 Если задача большая, можешь написать 'разбей эту задачу' и я помогу разделить на шаги",
                reply_markup=get_main_keyboard()
            )
        else:
            item = await add_plan_item(user.id, task_text)
            await message.answer(f"✅ Добавлено в план:\n\n{item.text}", reply_markup=get_main_keyboard())
    except Exception as e:
        logger.error(f"Error adding plan item: {e}", exc_info=True)
        await message.answer("Упс, не получилось добавить 😅 Попробуй ещё раз?", reply_markup=get_main_keyboard())
    finally:
        await state.clear()


@dp.callback_query(F.data == "plan_add")
async def callback_plan_add(callback: CallbackQuery, state: FSMContext):
    """Добавить пункт в план"""
    await callback.message.edit_text("Что добавим? 📋", reply_markup=None)
    await bot.send_message(
        callback.from_user.id,
        "Напиши задачу или отправь голосовое 🎤",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(BotStates.waiting_plan_item)
    await callback.answer()


@dp.callback_query(F.data.startswith("quick_"))
async def callback_quick_help(callback: CallbackQuery, state: FSMContext):
    """Обработка быстрых действий из помощи"""
    action = callback.data.replace("quick_", "")
    
    if action == "goal":
        await callback.message.edit_text("Какое главное дело на сегодня? 🎯", reply_markup=None)
        await bot.send_message(
            callback.from_user.id,
            "Одно дело — и всё хорошо. Напиши или отправь голосовое 🎤",
            reply_markup=get_cancel_keyboard()
        )
        await state.set_state(BotStates.waiting_goal)
    elif action == "plan":
        await callback.message.edit_text("Что добавим в план? 📋", reply_markup=None)
        await bot.send_message(
            callback.from_user.id,
            "Напиши задачу или отправь голосовое 🎤",
            reply_markup=get_cancel_keyboard()
        )
        await state.set_state(BotStates.waiting_plan_item)
    elif action == "focus":
        # Запускаем фокус
        user_id = callback.from_user.id
        if user_id not in active_pomodoros:
            await callback.message.edit_text("Поехали! 25 минут фокуса 🍅", reply_markup=None)
            await start_pomodoro(user_id, callback.from_user.id)
        else:
            await callback.answer("У тебя уже есть активный таймер! ⏱️")
            return
    elif action == "quiet":
        # Режим тишины
        from db_helpers import set_quiet_mode
        await set_quiet_mode(callback.from_user.id, 30 * 60)  # 30 минут
        await callback.message.edit_text("😌 Режим тишины включен на 30 минут\n\nОтдыхай 💛", reply_markup=None)
    
    await callback.answer()


@dp.callback_query(F.data == "plan_list")
async def callback_plan_list(callback: CallbackQuery):
    """Список плана"""
    user = await get_or_create_user(callback.from_user.id, None, None)
    items = await get_plan_items(user.id, completed=None)
    
    if not items:
        await callback.message.edit_text("План пуст 📋", reply_markup=get_plan_list_keyboard(items))
    else:
        completed = sum(1 for item in items if item.completed)
        progress_emoji = "🎉" if completed == len(items) else "💪" if completed > 0 else "✨"
        text = f"План на день 📋\n\n{progress_emoji} Выполнено: {completed}/{len(items)}"
        await callback.message.edit_text(text, reply_markup=get_plan_list_keyboard(items))
    
    await callback.answer()


@dp.callback_query(F.data.startswith("plan_view_"))
async def callback_plan_item_view(callback: CallbackQuery):
    """Просмотр пункта плана"""
    item_id = int(callback.data.split("_")[2])
    user = await get_or_create_user(callback.from_user.id, None, None)
    items = await get_plan_items(user.id)
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
    try:
        item_id = int(callback.data.split("_")[1])
        user = await get_or_create_user(callback.from_user.id, None, None)
        success = await toggle_plan_item(item_id, user.id)
        
        if success:
            await callback.answer("✅ Обновлено!")
            items = await get_plan_items(user.id, completed=None)
            completed_count = sum(1 for i in items if i.completed)
            total_count = len(items)
            progress_text = f"Выполнено: {completed_count}/{total_count}"
            if total_count > 0:
                percentage = int((completed_count / total_count) * 100)
                if percentage >= 100:
                    progress_text += " 🎉 Отлично!"
                elif percentage >= 75:
                    progress_text += " 💪 Почти всё!"
                elif percentage >= 50:
                    progress_text += " 👍 Хорошо!"
            await callback.message.edit_text(
                f"План обновлен 📋\n\n{progress_text}", 
                reply_markup=get_plan_list_keyboard(items)
            )
        else:
            await callback.answer("Ошибка ⚠️", show_alert=True)
    except Exception as e:
        logger.error(f"Error in callback_plan_item_done: {e}", exc_info=True)
        await callback.answer("Ошибка ⚠️", show_alert=True)


@dp.callback_query(lambda c: c.data and c.data.startswith("plan_") and c.data.endswith("_delete_confirm"))
async def callback_plan_delete_confirm(callback: CallbackQuery):
    """Подтверждение удаления пункта плана"""
    item_id = int(callback.data.split("_")[1])
    user = await get_or_create_user(callback.from_user.id, None, None)
    items = await get_plan_items(user.id)
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
    try:
        item_id = int(callback.data.split("_")[1])
        user = await get_or_create_user(callback.from_user.id, None, None)
        success = await delete_plan_item(item_id, user.id)
        
        if success:
            await callback.answer("🗑️ Удалено")
            items = await get_plan_items(user.id, completed=None)
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
    except Exception as e:
        logger.error(f"Error in callback_plan_item_delete: {e}", exc_info=True)
        await callback.answer("Ошибка ⚠️", show_alert=True)


# ==================== ГОЛОСОВЫЕ СООБЩЕНИЯ ====================

@dp.message(F.voice, StateFilter(None))
async def handle_voice_message(message: Message):
    """Обработка голосовых сообщений (когда не в состоянии)"""
    from voice_service import get_voice_service
    
    voice_service = get_voice_service()
    if not voice_service:
        await message.answer(
            "🎤 Голосовой ввод недоступен (нужно установить faster-whisper)\n\n"
            "Установи: pip install faster-whisper\n\n"
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
        from aiogram.fsm.context import FSMContext
        # Получаем state из storage
        from aiogram.fsm.storage.memory import MemoryStorage
        state = FSMContext(storage=storage, key=message.chat.id, user=message.from_user.id)
        await handle_ai_message(message, state)
        
    except ValueError as e:
        error_msg = str(e)
        if "too long" in error_msg.lower():
            await processing_msg.edit_text(
                "Голосовое сообщение слишком длинное (макс. 5 минут) ⏰\n\n"
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
        logger.error(f"Error processing voice: {e}", exc_info=True)
        await processing_msg.edit_text(
            "Упс, что-то пошло не так с голосом 😅\n\n"
            "Попробуй ещё раз или напиши текст",
            reply_markup=get_main_keyboard()
        )


# ==================== AI ОБРАБОТЧИК ====================

@dp.message(StateFilter(None))  # Only process when no active state  
async def handle_ai_message(message: Message, state: FSMContext):
    """Обработка сообщений с помощью AI (если не команда и не в состоянии)"""
    # Skip if no text
    if not message.text:
        return
    
    # Обработка запросов истории
    text_lower = message.text.lower() if message.text else ""
    
    # "детали" + дата для подробной информации о дне
    if text_lower.startswith("детали "):
        user = await get_or_create_user(message.from_user.id, None, None)
        date_text = message.text[len("детали "):].strip()
        
        # Парсим дату
        from dateparser import parse as parse_date
        parsed_date = parse_date(date_text, languages=['ru', 'en'])
        
        if not parsed_date:
            await message.answer(
                "Не понял дату 🤔\n\nПопробуй формат: 'детали 01.11' или 'детали вчера'",
                reply_markup=get_main_keyboard()
            )
            return
        
        summary = await get_daily_summary(user.id, parsed_date)
        
        date_str = parsed_date.strftime("%d.%m.%Y")
        text = f"📊 Детали дня {date_str}:\n\n"
        
        if summary['goal']:
            goal_emoji = "✅" if summary['goal'].completed else "⭕"
            text += f"🎯 Цель: {goal_emoji} {summary['goal'].goal_text}\n"
            if summary['goal'].estimated_pomodoros:
                text += f"🍅 Помидоры: {summary['goal'].completed_pomodoros or 0}/{summary['goal'].estimated_pomodoros}\n"
            if summary['goal'].day_rating:
                text += f"⭐ Оценка: {summary['goal'].day_rating}/10\n"
        else:
            text += "🎯 Цель: не установлена\n"
        
        if summary['plan_items']:
            completed = sum(1 for item in summary['plan_items'] if item.completed)
            text += f"\n📋 План: {completed}/{len(summary['plan_items'])}\n"
            for item in summary['plan_items'][:5]:
                item_emoji = "✅" if item.completed else "⭕"
                text += f"  {item_emoji} {item.text}\n"
            if len(summary['plan_items']) > 5:
                text += f"  ... и ещё {len(summary['plan_items']) - 5} задач\n"
        else:
            text += "\n📋 План: нет задач\n"
        
        if summary['checkin']:
            text += f"\n💬 Чек-ин:\n"
            if summary['checkin'].what_worked:
                text += f"Сделал: {summary['checkin'].what_worked}\n"
            if summary['checkin'].what_tired:
                text += f"Вымотало: {summary['checkin'].what_tired}\n"
            if summary['checkin'].what_helped:
                text += f"Помогло: {summary['checkin'].what_helped}\n"
        
        await message.answer(text, reply_markup=get_main_keyboard())
        return
    
    # "длинно" для полного формата истории
    if text_lower in ["длинно", "полный формат", "полная история"]:
        user = await get_or_create_user(message.from_user.id, None, None)
        days = await get_days_history(user.id, limit=30)
        
        if not days:
            await message.answer("Истории пока нет 📊", reply_markup=get_main_keyboard())
            return
        
        text = "📊 Полная история дней:\n\n"
        for i, day in enumerate(days[:15], 1):  # Показываем первые 15
            date_str = day['date'].strftime("%d.%m.%Y") if isinstance(day['date'], datetime) else str(day['date'])
            
            text += f"━━━━━━━━━━━━━━━━━━━━\n"
            text += f"📅 {date_str}\n"
            
            if day['rating']:
                rating_emojis = "⭐" * min(day['rating'], 10)
                text += f"Оценка: {rating_emojis} {day['rating']}/10\n"
            
            if day.get('goal'):
                goal_status = "✅" if day.get('goal_completed') else "⭕"
                text += f"Цель: {goal_status} {day['goal'][:50]}\n"
            
            if day['plan_count'] > 0:
                text += f"План: {day['plan_completed']}/{day['plan_count']} выполнено\n"
            
            if day.get('pomodoros'):
                text += f"Помидоры: {day['pomodoros']}\n"
            
            text += "\n"
        
        if len(days) > 15:
            text += f"... и ещё {len(days) - 15} дней"
        
        await message.answer(text, reply_markup=get_main_keyboard())
        return
    
    # Skip all commands - command handlers should process these first
    # This is a safety check in case command handlers don't catch them
    if message.text.startswith('/'):
        return
    
    # Обработка кнопок энергии вне состояния (если пользователь нажал кнопку вне диалога энергии)
    try:
        user, lang = await get_user_and_lang(message.from_user)
        energy_map = {
            translate("energy_less_40", lang).lower(): 40,
            translate("energy_around_60", lang).lower(): 60,
            translate("energy_more_80", lang).lower(): 80,
        }
        
        if message.text.lower() in energy_map:
            energy_level = energy_map.get(message.text.lower())
            if energy_level:
                await save_energy_level(user.id, energy_level)
                await message.answer(
                    translate("energy_saved", lang, level=energy_level) + " 💛\n\n" + translate("continue_working", lang),
                    reply_markup=get_main_keyboard(lang)
                )
                return
    except Exception as e:
        logger.error(f"Error handling energy button: {e}", exc_info=True)
    
    # Skip other button presses
    if message.text in ["😌 Мягкий день", "🎯 Обычный день", "🚀 Активный день",
                       "❌ Отмена", "отмена", "Отмена"]:
        return
    
    # Handle note deletion commands directly
    text_lower = message.text.lower() if message.text else ""
    if any(phrase in text_lower for phrase in ["удали все заметки", "очисти заметки", "удалить все заметки", "очистить заметки", "все"]):
        user = await get_or_create_user(message.from_user.id, None, None)
        count = await delete_all_notes(user.id)
        if count > 0:
            await message.answer(f"✅ Удалено {count} заметок", reply_markup=get_main_keyboard())
        else:
            await message.answer("Заметок не было 🤷", reply_markup=get_main_keyboard())
        return
    
    # Поиск по заметкам
    if text_lower.startswith("найди ") or text_lower.startswith("найти ") or text_lower.startswith("поиск "):
        user = await get_or_create_user(message.from_user.id, None, None)
        notes = await get_user_notes(user.id)
        
        if not notes:
            await message.answer("Заметок пока нет 📝", reply_markup=get_main_keyboard())
            return
        
        # Извлекаем поисковый запрос
        search_query = message.text.lower()
        for prefix in ["найди ", "найти ", "поиск "]:
            if search_query.startswith(prefix):
                search_query = search_query[len(prefix):].strip()
                break
        
        if not search_query:
            await message.answer("Что искать? 🔍\n\nНапиши: 'найди <слово>'", reply_markup=get_main_keyboard())
            return
        
        # Простой поиск по ключевым словам
        matching_notes = []
        for note in notes:
            if search_query in note.text.lower():
                matching_notes.append(note)
        
        if not matching_notes:
            await message.answer(f"Не нашёл заметок с '{search_query}' 🔍\n\nПопробуй другое слово?", reply_markup=get_main_keyboard())
            return
        
        # Показываем результаты (макс. 5)
        result_text = f"🔍 Найдено {len(matching_notes)} заметок:\n\n"
        for i, note in enumerate(matching_notes[:5], 1):
            date_str = note.created_at.strftime("%d.%m") if note.created_at else ""
            result_text += f"{i}. {note.text}"
            if date_str:
                result_text += f" ({date_str})"
            result_text += "\n"
        
        if len(matching_notes) > 5:
            result_text += f"\n... и ещё {len(matching_notes) - 5} заметок"
        
        await message.answer(result_text, reply_markup=get_main_keyboard())
        return
    
    # Обработка напоминаний (до AI, чтобы AI точно понимал что нужно создать напоминание)
    reminder_keywords = ["напомни", "напомни мне", "поставь напоминание", "напомни мне через", "напомни через"]
    if any(keyword in text_lower for keyword in reminder_keywords):
        # Если есть упоминание времени - это точно напоминание
        time_indicators = ["через", "в ", "завтра", "после", "перед", "сегодня в", "завтра в"]
        if any(indicator in text_lower for indicator in time_indicators):
            # Отправляем в AI с явным контекстом
            # Но сначала проверяем что это не команда заметки одновременно
            if not any(note_kw in text_lower for note_kw in ["запиши", "запомни", "сохрани"]):
                # Это точно напоминание - обработаем через AI с явным контекстом
                processing_msg = await message.answer("⏳ Создаю напоминание...", reply_markup=None)
                try:
                    reminder_prompt = f"Пользователь хочет создать напоминание. ОБЯЗАТЕЛЬНО используй функцию create_reminder. Текст: {message.text}"
                    response = await ai_service.process_message(reminder_prompt, message.from_user.id, None)
                    await processing_msg.delete()
                    await message.answer(response, reply_markup=get_main_keyboard())
                    return
                except Exception as e:
                    logger.error(f"Error creating reminder via AI: {e}", exc_info=True)
                    await processing_msg.delete()
                    # Fallback - отправляем в общий AI обработчик ниже
    
    # Прямая обработка фраз для создания заметок (перед AI)
    # Варианты: запиши/запишем, запомни/запомним, сохрани/сохраним
    note_keywords = ["запиши", "запишем", "запомни", "запомним", "сохрани", "сохраним", 
                     "не забудь", "добавь заметку", "запиши заметку", 
                     "давай просто запиши", "просто запиши", "запиши мне", "давай запиши",
                     "давай запишем", "просто запишем"]
    
    # Обработка неполных команд типа "давай просто запиши" без продолжения
    # Проверяем если сообщение ТОЧНО равно команде запиши
    if text_lower.strip() in ["давай просто запиши", "просто запиши", "запиши", "запомни", "сохрани", "давай запиши", "давай запишем"]:
        await message.answer(
            "Что записать? 📝\n\n"
            "Напиши что нужно сохранить, например:\n"
            "• сделать работу\n"
            "• купить молоко\n"
            "• записаться к врачу\n\n"
            "Или используй команду /note",
            reply_markup=get_main_keyboard()
        )
        return
    
    if any(keyword in text_lower for keyword in note_keywords):
        # Убираем "да не" в начале - пользователь может написать "да не давай запиши" но иметь в виду "всё же запиши"
        # Или просто игнорируем "да не" для целей сохранения
        original_text = message.text
        if text_lower.startswith("да не"):
            # Убираем "да не" но оставляем остальное
            original_text = message.text[len("да не"):].strip()
            text_lower = original_text.lower()
        
        # Извлекаем текст для заметки (всё что после ключевого слова)
        note_text = original_text
        
        # Находим самое длинное совпадение ключевого слова (для "давай просто запиши" перед "запиши")
        matched_keyword = None
        max_len = 0
        for keyword in note_keywords:
            if keyword in text_lower:
                if len(keyword) > max_len:
                    max_len = len(keyword)
                    matched_keyword = keyword
        
        if matched_keyword:
            idx = text_lower.find(matched_keyword)
            if idx != -1:
                # Берём текст после ключевого слова
                after_keyword = original_text[idx + len(matched_keyword):].strip()
                
                # Убираем пробелы и знаки препинания в начале
                after_keyword = after_keyword.lstrip(" ,").strip()
                
                # Убираем местоимения в начале: "ее", "его", "её"
                # Специальный случай: "ее запишем" - "ее" идет ПЕРЕД "запишем"
                # Но если "ее" идет ПОСЛЕ "запишем", убираем его
                for pronoun in ["ее ", "его ", "её "]:
                    if after_keyword.lower().startswith(pronoun):
                        after_keyword = after_keyword[len(pronoun):].strip()
                        break
                
                # Если после этого что-то осталось
                if after_keyword:
                    note_text = after_keyword
                else:
                    # Если ничего не осталось после ключевого слова
                    # Проверяем что было ДО ключевого слова
                    before_keyword = original_text[:idx].strip()
                    
                    # Случай "ее запишем и X" - "ее" идет ПЕРЕД "запишем", после "запишем" идет " и X"
                    # В этом случае after_keyword будет пустым, но мы должны взять текст ПОСЛЕ "запишем"
                    text_after_keyword = original_text[idx + len(matched_keyword):].strip()
                    
                    if text_after_keyword and "и" in text_after_keyword.lower():
                        # Есть текст после ключевого слова с "и" - обработаем его ниже
                        note_text = text_after_keyword
                    elif before_keyword.lower().endswith("ее") and "и" in text_lower:
                        # Случай "давай просто ее запишем и X" - пропускаем "ее", сохраняем X
                        # Это будет обработано ниже при разбиении по "и"
                        note_text = original_text[idx + len(matched_keyword):].strip()
                        if not note_text:
                            await message.answer(
                                "Что записать? 📝\n\n"
                                "Напиши что нужно сохранить, например:\n"
                                "• сделать работу\n"
                                "• купить молоко\n\n"
                                "Или используй команду /note",
                                reply_markup=get_main_keyboard()
                            )
                            return
                    else:
                        # Если ничего не осталось после ключевого слова - это неполная команда
                        await message.answer(
                            "Что записать? 📝\n\n"
                            "Напиши что нужно сохранить, например:\n"
                            "• сделать работу\n"
                            "• купить молоко\n\n"
                            "Или используй команду /note",
                            reply_markup=get_main_keyboard()
                        )
                        return
        
        # Если есть "и" в тексте, разделяем на несколько заметок
        # Обрабатываем разные варианты: "и", "и записаться", "и запиши", запятые
        parts = []
        
        # Специальные случаи - обрабатываем "и записаться" ПЕРВЫМ ДЕЛОМ
        if " и записаться" in note_text.lower() or note_text.lower().startswith("и записаться"):
            # Обрабатываем случай "и записаться к урологу" или "сделать работу и записаться к урологу"
            if note_text.lower().startswith("и записаться"):
                # Весь текст это "и записаться к урологу"
                after_and = note_text[len("и записаться"):].strip()
                if after_and:
                    if after_and.startswith("к ") or after_and.startswith("на "):
                        parts.append(f"записаться {after_and}")
                    else:
                        parts.append(f"записаться к {after_and}")
                else:
                    parts.append("записаться к врачу")
            else:
                # Есть текст перед "и записаться"
                and_idx = note_text.lower().find(" и записаться")
                if and_idx != -1:
                    # Часть перед "и записаться"
                    before_and = note_text[:and_idx].strip()
                    # Убираем местоимения и служебные слова
                    before_and_clean = before_and
                    for word in ["ее", "его", "её", "давай", "просто", "да", "не"]:
                        if before_and_clean.lower().strip() == word:
                            before_and_clean = ""
                            break
                    
                    if before_and_clean and before_and_clean.strip() not in ["ее", "его", "её"]:
                        parts.append(before_and_clean.strip())
                    
                    # Часть после "и записаться"
                    after_and = note_text[and_idx + len(" и записаться"):].strip()
                    if after_and:
                        if after_and.startswith("к ") or after_and.startswith("на "):
                            parts.append(f"записаться {after_and}")
                        else:
                            parts.append(f"записаться к {after_and}")
                    else:
                        parts.append("записаться к врачу")
            
            # Если ничего не добавили, используем исходный текст
            if not parts:
                parts = [note_text]
        elif " и " in note_text:
            # Разделяем по " и " и обрабатываем каждую часть
            temp_parts = [p.strip() for p in note_text.split(" и ") if p.strip()]
            for part in temp_parts:
                # Если часть начинается с "записаться", добавляем как есть
                if part.lower().startswith("записаться"):
                    parts.append(part)
                else:
                    parts.append(part)
        elif "," in note_text:
            # Разделяем по запятым
            parts = [p.strip() for p in note_text.split(",") if p.strip()]
        else:
            parts = [note_text]
        
        # Сохраняем каждую часть как отдельную заметку
        # Проверяем нужно ли сохранять несколько заметок
        should_save_directly = len(parts) > 1
        
        if should_save_directly:
            saved_count = 0
            saved_parts = []
            for part in parts:
                if part and len(part.strip()) > 0 and part.strip() != "ее" and part.strip() != "его":
                    try:
                        from db_helpers import save_note, get_or_create_user
                        user = await get_or_create_user(message.from_user.id, None, None)
                        await save_note(user.id, part.strip())
                        saved_count += 1
                        saved_parts.append(part.strip())
                    except Exception as e:
                        logger.error(f"Error saving note '{part}': {e}", exc_info=True)
            
            if saved_count > 0:
                if saved_count == 1:
                    await message.answer(f"✅ Заметка сохранена: {saved_parts[0]}", reply_markup=get_main_keyboard())
                else:
                    notes_list = "\n".join([f"• {part}" for part in saved_parts])
                    await message.answer(f"✅ Сохранено {saved_count} заметок:\n\n{notes_list}\n\nПосмотреть все: /notes", reply_markup=get_main_keyboard())
                return
            # Если не получилось сохранить, продолжаем обработку через AI ниже
        
        # Одна заметка или не удалось разделить
        if note_text and len(note_text.strip()) > 0:
            # Фильтруем пустые заметки и местоимения
            if note_text.strip() not in ["ее", "его", "её", "его", "и"]:
                try:
                    from db_helpers import save_note, get_or_create_user
                    user = await get_or_create_user(message.from_user.id, None, None)
                    await save_note(user.id, note_text.strip())
                    await message.answer(f"✅ Заметка сохранена: {note_text.strip()}\n\nПосмотреть все: /notes", reply_markup=get_main_keyboard())
                    return
                except Exception as e:
                    logger.error(f"Error saving note '{note_text}': {e}", exc_info=True)
                    # Продолжаем обработку через AI
    
    # Get user's current energy level
    user_state = await get_user_state(message.from_user.id)
    energy = None  # Could fetch latest energy from DB
    
    # Process with AI
    try:
        # Добавляем контекст для AI если есть ключевые слова заметок
        ai_prompt = message.text
        
        # Если сообщение похоже на задачу без команды (например, "сделать тест план для фичи")
        # но нет явной команды "запиши", предлагаем варианты через AI
        task_patterns = ["сделать ", "подготовить ", "написать ", "выполнить ", "тест план", "отчёт", "план для"]
        is_task_like = any(pattern in text_lower for pattern in task_patterns)
        
        # Проверяем напоминания
        reminder_keywords_check = ["напомни", "напомни мне", "поставь напоминание"]
        time_indicators_check = ["через", "в ", "завтра", "после", "перед", "сегодня в", "завтра в", "через минуту", "через час"]
        
        if any(keyword in text_lower for keyword in reminder_keywords_check) and any(indicator in text_lower for indicator in time_indicators_check):
            # Это точно напоминание
            ai_prompt = f"Пользователь хочет создать напоминание. ОБЯЗАТЕЛЬНО используй функцию create_reminder. Текст запроса: {message.text}"
        elif any(keyword in text_lower for keyword in note_keywords):
            ai_prompt = f"Пользователь хочет сохранить заметку. ОБЯЗАТЕЛЬНО используй функцию add_note несколько раз если есть 'и' в тексте. Текст: {message.text}"
        elif is_task_like and len(text_lower.split()) <= 8:
            # Короткое сообщение похожее на задачу - предлагаем сохранить
            ai_prompt = f"Пользователь упомянул задачу '{message.text}'. Предложи сохранить её как заметку или создать напоминание. Используй функцию add_note если пользователь согласится сохранить."
        
        try:
            response = await ai_service.process_message(ai_prompt, message.from_user.id, energy)
            
            # Проверяем, создал ли AI заметку или напоминание
            if "заметка сохранена" in response.lower() or "напоминание создано" in response.lower() or "✅" in response:
                await message.answer(response, reply_markup=get_main_keyboard())
            elif "указанное время уже прошло" in response.lower():
                # Проблема с парсингом времени - попробуем исправить
                await message.answer(response + "\n\n💡 Попробуй указать время точнее, например:\n• через 10 секунд\n• через 5 минут\n• завтра в 15:00", reply_markup=get_main_keyboard())
            else:
                # Если AI не создал заметку, но была команда "запиши", пробуем создать напрямую
                if any(keyword in text_lower for keyword in ["запиши", "запомни", "сохрани"]) and "запиши" not in response.lower():
                    # Пробуем извлечь текст для заметки
                    note_text = message.text
                    for keyword in ["запиши", "запомни", "сохрани"]:
                        if keyword in text_lower:
                            idx = text_lower.find(keyword)
                            if idx != -1:
                                after_keyword = message.text[idx + len(keyword):].strip().lstrip("и, ").strip()
                                if after_keyword and len(after_keyword) > 2:  # Минимум 3 символа
                                    note_text = after_keyword
                                    break
                    
                    if note_text and note_text != message.text and len(note_text.strip()) > 2:
                        try:
                            from db_helpers import save_note, get_or_create_user
                            user = await get_or_create_user(message.from_user.id, None, None)
                            await save_note(user.id, note_text.strip())
                            await message.answer(f"✅ Заметка сохранена: {note_text.strip()}\n\nПосмотреть все заметки: /notes", reply_markup=get_main_keyboard())
                            return
                        except Exception as e:
                            logger.error(f"Fallback note save error: {e}", exc_info=True)
                
                await message.answer(response, reply_markup=get_main_keyboard())
        except Exception as ai_error:
            logger.error(f"AI processing error: {ai_error}", exc_info=True)
            # Если AI упал, но была команда "запиши", пробуем сохранить напрямую
            if any(keyword in text_lower for keyword in ["запиши", "запомни", "сохрани"]):
                try:
                    note_text = message.text
                    for keyword in ["запиши", "запомни", "сохрани"]:
                        if keyword in text_lower:
                            idx = text_lower.find(keyword)
                            if idx != -1:
                                after_keyword = message.text[idx + len(keyword):].strip().lstrip("и, ").strip()
                                if after_keyword and len(after_keyword) > 2:
                                    note_text = after_keyword
                                    break
                    
                    if note_text and note_text != message.text and len(note_text.strip()) > 2:
                        from db_helpers import save_note, get_or_create_user
                        user = await get_or_create_user(message.from_user.id, None, None)
                        await save_note(user.id, note_text.strip())
                        await message.answer(f"✅ Заметка сохранена: {note_text.strip()}\n\nПосмотреть все заметки: /notes", reply_markup=get_main_keyboard())
                        return
                except Exception as e:
                    logger.error(f"Fallback note save after AI error: {e}", exc_info=True)
            
            await message.answer(
                "Упс, что-то пошло не так 😅\n\n💡 Попробуй:\n• Написать короче\n• Использовать команды: /goal, /plan, /note, /reminders\n• Или просто: 'запиши купить молоко'\n\n💛",
                reply_markup=get_main_keyboard()
            )
            
    except Exception as e:
        logger.error(f"AI error in handle_ai_message: {e}", exc_info=True)
        
        # Fallback: если была команда "запиши", пробуем сохранить напрямую
        if any(keyword in text_lower for keyword in ["запиши", "запомни", "сохрани", "давай просто запиши"]):
            note_text = message.text
            for keyword in ["запиши", "запомни", "сохрани", "давай просто запиши"]:
                if keyword in text_lower:
                    idx = text_lower.find(keyword)
                    if idx != -1:
                        after_keyword = message.text[idx + len(keyword):].strip().lstrip("и, ").strip()
                        if after_keyword:
                            note_text = after_keyword
                            break
            
            try:
                from db_helpers import save_note, get_or_create_user
                user = await get_or_create_user(message.from_user.id, None, None)
                await save_note(user.id, note_text.strip())
                await message.answer(f"✅ Заметка сохранена: {note_text.strip()}\n\nПосмотреть все заметки: /notes", reply_markup=get_main_keyboard())
                return
            except Exception as e2:
                logger.error(f"Final fallback error: {e2}", exc_info=True)
        
        # Final fallback
        await message.answer(
            "Понял тебя 💛\n\nПопробуй:\n"
            "• /note — сохранить заметку\n"
            "• /goal — цель на сегодня\n"
            "• Или просто напиши: 'запиши купить молоко'",
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
                logger.info(f"✅ Загружено {count} активных напоминаний в планировщик ⏰")
            else:
                logger.info("ℹ️  Активных напоминаний нет")
    except Exception as e:
        logger.error(f"⚠️  Ошибка загрузки напоминаний: {e}", exc_info=True)


# ==================== ЗАПУСК БОТА ====================

async def main():
    """Главная функция"""
    print("Запуск бота SDVGaid... 🤖")
    
    # Register new handlers
    try:
        from handlers.register import register_all_handlers
        register_all_handlers()
        print("Новые обработчики зарегистрированы ✅")
    except Exception as e:
        print(f"Предупреждение: не удалось зарегистрировать новые обработчики: {e}")
    
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

