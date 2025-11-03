"""Goal handlers - following Single Responsibility Principle"""
from aiogram import F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
# dp and BotStates will be injected via register_handlers
dp = None
BotStates = None

def register_handlers(dp_instance, BotStatesClass):
    global dp, BotStates
    dp = dp_instance
    BotStates = BotStatesClass
from keyboards import (
    get_cancel_keyboard, get_main_keyboard, get_goal_confirmation_keyboard
)
from services.goal_service import GoalService
from services.energy_service import EnergyService
from utils.voice_utils import process_voice_to_text
from utils.validation import validate_message_text, check_cancel_command
from handlers.base import handle_voice_message, validate_text, handle_cancel
from bot_helpers import get_user_and_lang
from translations import translate
import logging

logger = logging.getLogger(__name__)


@dp.message(Command("goal"))
@dp.message(lambda m: m.text and ("🎯 Главная цель" in m.text or "Главная цель" in m.text))
async def cmd_goal(message: Message, state: FSMContext):
    """Set daily goal"""
    user, lang = await get_user_and_lang(message.from_user)
    goal_service = GoalService()
    
    goal = await goal_service.get_user_goal(user.id)
    
    if goal:
        text = await goal_service.format_goal_with_progress(goal, lang)
        text += "\n\n" + translate("goal_change_question", lang)
        await message.answer(text, reply_markup=get_goal_confirmation_keyboard())
    else:
        goal_prompt = await goal_service.get_goal_prompt(user.id, lang)
        await message.answer(
            goal_prompt + "\n\n" + translate("goal_hint", lang),
            reply_markup=get_cancel_keyboard(lang)
        )
        await state.set_state(BotStates.waiting_goal)


@dp.message(StateFilter(BotStates.waiting_goal))
@handle_voice_message
@validate_text(min_length=1, max_length=200)
@handle_cancel()
async def process_goal(message: Message, state: FSMContext):
    """Process goal input"""
    user, lang = await get_user_and_lang(message.from_user)
    goal_service = GoalService()
    
    # Check cancel
    if await check_cancel_command(message, state):
        return
    
    # Validate
    is_valid, error_msg = await validate_message_text(message, min_length=1, max_length=200)
    if not is_valid:
        await message.answer(error_msg, reply_markup=get_cancel_keyboard(lang))
        return
    
    try:
        goal_text = message.text.strip()
        
        # Ask about pomodoros
        await message.answer(
            translate("goal_understood", lang, goal=goal_text) + "\n\n" +
            translate("pomodoros_question", lang) + "\n\n" +
            translate("pomodoros_can_skip", lang),
            reply_markup=get_cancel_keyboard(lang)
        )
        
        await state.update_data(goal_text=goal_text)
        await state.set_state(BotStates.waiting_goal_pomodoros)
        
    except Exception as e:
        logger.error(f"Error processing goal: {e}", exc_info=True)
        await message.answer(translate("error_generic", lang), reply_markup=get_main_keyboard(lang))
        await state.clear()


@dp.message(StateFilter(BotStates.waiting_goal_pomodoros))
@handle_cancel()
async def process_goal_pomodoros(message: Message, state: FSMContext):
    """Process pomodoro estimation"""
    user, lang = await get_user_and_lang(message.from_user)
    goal_service = GoalService()
    
    # Check cancel/skip
    cancel_keywords = ["❌ Отмена", "отмена", "пропустить", "skip", "/cancel"]
    if message.text and message.text.strip().lower() in [kw.lower() for kw in cancel_keywords]:
        data = await state.get_data()
        goal_text = data.get("goal_text", "")
        if goal_text:
            await goal_service.save_user_goal(user.id, goal_text)
            await message.answer(
                translate("goal_saved_no_pomodoros", lang, goal=goal_text),
                reply_markup=get_main_keyboard(lang)
            )
        await state.clear()
        return
    
    # Parse pomodoros
    try:
        pomodoros_text = message.text.strip()
        estimated_pomodoros = int(pomodoros_text)
        
        if estimated_pomodoros < 1 or estimated_pomodoros > 50:
            await message.answer(
                translate("pomodoros_invalid_range", lang),
                reply_markup=get_cancel_keyboard(lang)
            )
            return
        
        data = await state.get_data()
        goal_text = data.get("goal_text", "")
        
        if goal_text:
            goal = await goal_service.save_user_goal(user.id, goal_text, estimated_pomodoros)
            await message.answer(
                translate("goal_saved", lang, goal=goal.goal_text) + "\n\n" +
                translate("pomodoros_saved", lang, count=estimated_pomodoros),
                reply_markup=get_main_keyboard(lang)
            )
        
        await state.clear()
        
    except ValueError:
        await message.answer(
            translate("pomodoros_invalid_format", lang),
            reply_markup=get_cancel_keyboard(lang)
        )
    except Exception as e:
        logger.error(f"Error saving goal: {e}", exc_info=True)
        await message.answer(translate("error_generic", lang), reply_markup=get_main_keyboard(lang))
        await state.clear()


@dp.callback_query(F.data == "goal_confirm")
async def goal_confirm(callback: CallbackQuery):
    """Confirm current goal"""
    user, lang = await get_user_and_lang(callback.from_user)
    await callback.message.edit_text(
        translate("goal_confirmed", lang),
        reply_markup=None
    )
    await callback.message.answer(translate("good_night", lang), reply_markup=get_main_keyboard(lang))
    await callback.answer()


@dp.callback_query(F.data == "goal_done")
async def goal_done(callback: CallbackQuery):
    """Goal completed"""
    user, lang = await get_user_and_lang(callback.from_user)
    goal_service = GoalService()
    goal = await goal_service.get_user_goal(user.id)
    
    if goal:
        await goal_service.complete_user_goal(goal.id)
    
    await callback.message.edit_text(translate("goal_done_message", lang))
    await callback.answer()


@dp.callback_query(F.data == "goal_skip")
async def goal_skip(callback: CallbackQuery):
    """Goal not done"""
    user, lang = await get_user_and_lang(callback.from_user)
    await callback.message.edit_text(translate("goal_skip_message", lang))
    await callback.answer()
