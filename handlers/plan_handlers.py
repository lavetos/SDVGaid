"""Plan handlers - following Single Responsibility Principle"""
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
    get_cancel_keyboard, get_main_keyboard, get_plan_list_keyboard
)
from services.plan_service import PlanService
from utils.voice_utils import process_voice_to_text
from utils.validation import validate_message_text, check_cancel_command
from handlers.base import handle_voice_message, validate_text, handle_cancel
from bot_helpers import get_user_and_lang
from translations import translate
import logging

logger = logging.getLogger(__name__)


@dp.message(Command("plan"))
@dp.message(lambda m: m.text and ("📋 План" in m.text or "План" in m.text))
async def cmd_plan(message: Message, state: FSMContext):
    """Show daily plan"""
    try:
        user, lang = await get_user_and_lang(message.from_user)
        plan_service = PlanService()
        
        summary = await plan_service.get_plan_summary(user.id, lang)
        
        if summary['empty_msg']:
            await message.answer(
                summary['empty_msg'],
                reply_markup=get_plan_list_keyboard(summary['items'])
            )
        else:
            text = await plan_service.format_plan_progress(
                summary['completed'],
                summary['total'],
                lang
            )
            text += summary['energy_note']
            
            await message.answer(text, reply_markup=get_plan_list_keyboard(summary['items']))
            
    except Exception as e:
        logger.error(f"Error in /plan: {e}", exc_info=True)
        user, lang = await get_user_and_lang(message.from_user)
        await message.answer(translate("error_generic", lang), reply_markup=get_main_keyboard(lang))


@dp.message(StateFilter(BotStates.waiting_plan_item))
@handle_voice_message
@validate_text(min_length=1, max_length=200)
@handle_cancel()
async def process_plan_item(message: Message, state: FSMContext):
    """Process plan item input"""
    user, lang = await get_user_and_lang(message.from_user)
    plan_service = PlanService()
    
    # Check cancel
    if await check_cancel_command(message, state):
        return
    
    # Validate
    is_valid, error_msg = await validate_message_text(message, min_length=1, max_length=200)
    if not is_valid:
        await message.answer(error_msg, reply_markup=get_cancel_keyboard(lang))
        return
    
    try:
        task_text = message.text.strip()
        item = await plan_service.add_item(user.id, task_text)
        
        word_count = len(task_text.split())
        if word_count > 5:
            await message.answer(
                translate("plan_item_added_large", lang, text=item.text),
                reply_markup=get_main_keyboard(lang)
            )
        else:
            await message.answer(
                translate("plan_item_added", lang, text=item.text),
                reply_markup=get_main_keyboard(lang)
            )
        
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error adding plan item: {e}", exc_info=True)
        await message.answer(translate("error_generic", lang), reply_markup=get_main_keyboard(lang))
        await state.clear()


@dp.callback_query(F.data == "plan_add")
async def callback_plan_add(callback: CallbackQuery, state: FSMContext):
    """Add plan item"""
    user, lang = await get_user_and_lang(callback.from_user)
    
    await callback.message.edit_text(translate("plan_add_question", lang), reply_markup=None)
    await callback.message.answer(
        translate("plan_add_hint", lang),
        reply_markup=get_cancel_keyboard(lang)
    )
    await state.set_state(BotStates.waiting_plan_item)
    await callback.answer()


@dp.callback_query(F.data == "plan_list")
async def callback_plan_list(callback: CallbackQuery):
    """Show plan list"""
    user, lang = await get_user_and_lang(callback.from_user)
    plan_service = PlanService()
    
    items = await plan_service.get_items(user.id, completed=None)
    
    if not items:
        await callback.message.edit_text(
            translate("plan_empty", lang),
            reply_markup=get_plan_list_keyboard(items)
        )
    else:
        summary = await plan_service.get_plan_summary(user.id, lang)
        text = await plan_service.format_plan_progress(
            summary['completed'],
            summary['total'],
            lang
        )
        await callback.message.edit_text(text, reply_markup=get_plan_list_keyboard(items))
    
    await callback.answer()


@dp.callback_query(F.data.startswith("plan_") and F.data.endswith("_done"))
async def callback_plan_item_done(callback: CallbackQuery):
    """Toggle plan item completion"""
    try:
        item_id = int(callback.data.split("_")[1])
        user, lang = await get_user_and_lang(callback.from_user)
        plan_service = PlanService()
        
        success = await plan_service.toggle_item(item_id, user.id)
        
        if success:
            await callback.answer(translate("updated", lang))
            summary = await plan_service.get_plan_summary(user.id, lang)
            
            completed_count = summary['completed']
            total_count = summary['total']
            
            progress_text = translate("plan_completed", lang) + f": {completed_count}/{total_count}"
            if total_count > 0:
                percentage = int((completed_count / total_count) * 100)
                if percentage >= 100:
                    progress_text += " 🎉 " + translate("excellent", lang)
                elif percentage >= 75:
                    progress_text += " 💪 " + translate("almost_done", lang)
                elif percentage >= 50:
                    progress_text += " 👍 " + translate("good", lang)
            
            await callback.message.edit_text(
                translate("plan_updated", lang) + "\n\n" + progress_text,
                reply_markup=get_plan_list_keyboard(summary['items'])
            )
        else:
            await callback.answer(translate("error_generic", lang), show_alert=True)
            
    except Exception as e:
        logger.error(f"Error in callback_plan_item_done: {e}", exc_info=True)
        await callback.answer(translate("error_generic", lang), show_alert=True)


@dp.callback_query(lambda c: c.data and c.data.startswith("plan_") and c.data.endswith("_delete_confirm"))
async def callback_plan_delete_confirm(callback: CallbackQuery):
    """Confirm plan item deletion"""
    item_id = int(callback.data.split("_")[1])
    user, lang = await get_user_and_lang(callback.from_user)
    plan_service = PlanService()
    
    items = await plan_service.get_items(user.id)
    item = next((i for i in items if i.id == item_id), None)
    
    if not item:
        await callback.answer(translate("item_not_found", lang))
        return
    
    from keyboards import get_plan_delete_confirm_keyboard
    await callback.message.edit_text(
        translate("plan_delete_confirm", lang, text=item.text),
        reply_markup=get_plan_delete_confirm_keyboard(item_id)
    )
    await callback.answer()


@dp.callback_query(lambda c: c.data and c.data.startswith("plan_") and c.data.endswith("_delete") and not c.data.endswith("_delete_confirm"))
async def callback_plan_item_delete(callback: CallbackQuery):
    """Delete plan item"""
    try:
        item_id = int(callback.data.split("_")[1])
        user, lang = await get_user_and_lang(callback.from_user)
        plan_service = PlanService()
        
        success = await plan_service.delete_item(item_id, user.id)
        
        if success:
            await callback.answer(translate("deleted", lang))
            summary = await plan_service.get_plan_summary(user.id, lang)
            
            if summary['items']:
                completed = summary['completed']
                await callback.message.edit_text(
                    translate("plan_item_deleted", lang) + "\n\n" +
                    translate("plan_completed", lang) + f": {completed}/{summary['total']}",
                    reply_markup=get_plan_list_keyboard(summary['items'])
                )
            else:
                await callback.message.edit_text(
                    translate("plan_item_deleted", lang) + "\n\n" +
                    translate("plan_empty_after_delete", lang),
                    reply_markup=get_plan_list_keyboard(summary['items'])
                )
        else:
            await callback.answer(translate("error_generic", lang))
            
    except Exception as e:
        logger.error(f"Error in callback_plan_item_delete: {e}", exc_info=True)
        await callback.answer(translate("error_generic", lang), show_alert=True)
