"""Evening check-in handlers - following Single Responsibility Principle"""
from aiogram.filters import Command, StateFilter
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
# dp and BotStates will be injected via register_handlers
dp = None
BotStates = None

def register_handlers(dp_instance, BotStatesClass):
    global dp, BotStates
    dp = dp_instance
    BotStates = BotStatesClass

from keyboards import (
    get_cancel_keyboard, get_main_keyboard, get_goal_completion_keyboard
)
from services.evening_service import EveningService
from services.goal_service import GoalService
from utils.validation import validate_message_text, check_cancel_command
from handlers.base import handle_cancel
from bot_helpers import get_user_and_lang
from translations import translate
import logging

logger = logging.getLogger(__name__)


@dp.message(Command("evening"))
async def cmd_evening(message: Message, state: FSMContext):
    """Start evening check-in"""
    user, lang = await get_user_and_lang(message.from_user)
    await message.answer(
        translate("evening_question", lang),
        reply_markup=get_cancel_keyboard(lang)
    )
    await state.set_state(BotStates.waiting_evening_worked)


@dp.message(StateFilter(BotStates.waiting_evening_worked))
@handle_cancel()
async def process_evening_worked(message: Message, state: FSMContext):
    """Process first evening question"""
    user, lang = await get_user_and_lang(message.from_user)
    
    # Check cancel
    if await check_cancel_command(message, state):
        return
    
    # Validate
    is_valid, error_msg = await validate_message_text(message, min_length=1, max_length=500)
    if not is_valid:
        await message.answer(error_msg, reply_markup=get_cancel_keyboard(lang))
        return
    
    try:
        await state.update_data(what_worked=message.text.strip())
        await message.answer(
            translate("evening_tired_question", lang),
            reply_markup=get_cancel_keyboard(lang)
        )
        await state.set_state(BotStates.waiting_evening_tired)
        
    except Exception as e:
        logger.error(f"Error in process_evening_worked: {e}", exc_info=True)
        await message.answer(translate("error_generic", lang), reply_markup=get_main_keyboard(lang))
        await state.clear()


@dp.message(StateFilter(BotStates.waiting_evening_tired))
@handle_cancel()
async def process_evening_tired(message: Message, state: FSMContext):
    """Process second evening question"""
    user, lang = await get_user_and_lang(message.from_user)
    
    # Check cancel
    if await check_cancel_command(message, state):
        return
    
    # Validate
    is_valid, error_msg = await validate_message_text(message, min_length=1, max_length=500)
    if not is_valid:
        await message.answer(error_msg, reply_markup=get_cancel_keyboard(lang))
        return
    
    try:
        await state.update_data(what_tired=message.text.strip())
        await message.answer(
            translate("evening_helped_question", lang),
            reply_markup=get_cancel_keyboard(lang)
        )
        await state.set_state(BotStates.waiting_evening_helped)
        
    except Exception as e:
        logger.error(f"Error in process_evening_tired: {e}", exc_info=True)
        await message.answer(translate("error_generic", lang), reply_markup=get_main_keyboard(lang))
        await state.clear()


@dp.message(StateFilter(BotStates.waiting_evening_helped))
@handle_cancel()
async def process_evening_helped(message: Message, state: FSMContext):
    """Process third evening question and save check-in"""
    user, lang = await get_user_and_lang(message.from_user)
    evening_service = EveningService()
    goal_service = GoalService()
    
    # Check cancel
    if await check_cancel_command(message, state):
        return
    
    # Validate
    is_valid, error_msg = await validate_message_text(message, min_length=1, max_length=500)
    if not is_valid:
        await message.answer(error_msg, reply_markup=get_cancel_keyboard(lang))
        return
    
    try:
        data = await state.get_data()
        
        # Save check-in
        await evening_service.save_checkin(
            user.id,
            message.from_user.id,
            what_worked=data.get('what_worked', ''),
            what_tired=data.get('what_tired', ''),
            what_helped=message.text.strip()
        )
        
        # Check if should ask about goal
        should_ask, goal = await evening_service.should_ask_about_goal(user.id)
        
        if should_ask and goal:
            await message.answer(
                translate("evening_thanks", lang) + "\n\n" +
                translate("goal_reminder", lang, text=goal.goal_text),
                reply_markup=get_goal_completion_keyboard()
            )
        else:
            # Ask for day rating
            await message.answer(
                translate("evening_thanks", lang) + "\n\n" +
                translate("rating_question_optional", lang),
                reply_markup=get_cancel_keyboard(lang)
            )
            await state.set_state(BotStates.waiting_day_rating)
        
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error in process_evening_helped: {e}", exc_info=True)
        await message.answer(translate("error_generic", lang), reply_markup=get_main_keyboard(lang))
        await state.clear()

