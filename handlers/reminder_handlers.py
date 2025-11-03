"""Reminder handlers - following Single Responsibility Principle"""
from aiogram import F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from datetime import datetime
# dp and BotStates will be injected via register_handlers
dp = None
BotStates = None

def register_handlers(dp_instance, BotStatesClass):
    global dp, BotStates
    dp = dp_instance
    BotStates = BotStatesClass

from keyboards import (
    get_cancel_keyboard, get_main_keyboard, get_reminders_list_keyboard,
    get_reminder_keyboard, get_reminder_delete_confirm_keyboard
)
from services.reminder_service import ReminderService
from handlers.base import handle_cancel
from bot_helpers import get_user_and_lang
from translations import translate
import logging

logger = logging.getLogger(__name__)


@dp.message(Command("reminders"))
async def cmd_reminders(message: Message):
    """Show all reminders"""
    try:
        user, lang = await get_user_and_lang(message.from_user)
        reminder_service = ReminderService()
        
        reminders = await reminder_service.list_all(user.id, completed=False, limit=50)
        
        if not reminders:
            await message.answer(
                translate("reminders_empty", lang),
                reply_markup=get_reminders_list_keyboard(reminders)
            )
            return
        
        text = translate("reminders_title", lang, count=len(reminders)) + "\n\n"
        for i, rem in enumerate(reminders[:5], 1):
            text += f"{i}. {rem.text}\n"
        
        await message.answer(text, reply_markup=get_reminders_list_keyboard(reminders))
        
    except Exception as e:
        logger.error(f"Error in /reminders: {e}", exc_info=True)
        user, lang = await get_user_and_lang(message.from_user)
        await message.answer(translate("error_generic", lang), reply_markup=get_main_keyboard(lang))


@dp.callback_query(F.data.startswith("rem_view_"))
async def callback_reminder_view(callback: CallbackQuery):
    """View reminder details"""
    try:
        reminder_id = int(callback.data.split("_")[2])
        user, lang = await get_user_and_lang(callback.from_user)
        reminder_service = ReminderService()
        
        reminders = await reminder_service.list_all(user.id, limit=1000)
        reminder = next((r for r in reminders if r.id == reminder_id), None)
        
        if not reminder:
            await callback.answer(translate("reminder_not_found", lang))
            return
        
        when_str = reminder.when_datetime.strftime("%d.%m.%Y %H:%M")
        text = translate("reminder_details", lang, text=reminder.text, when=when_str)
        
        await callback.message.edit_text(text, reply_markup=get_reminder_keyboard(reminder_id))
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in callback_reminder_view: {e}", exc_info=True)
        await callback.answer(translate("error_generic", lang), show_alert=True)


@dp.callback_query(F.data.startswith("rem_") and F.data.endswith("_done"))
async def callback_reminder_done(callback: CallbackQuery):
    """Mark reminder as completed"""
    try:
        reminder_id = int(callback.data.split("_")[1])
        user, lang = await get_user_and_lang(callback.from_user)
        reminder_service = ReminderService()
        
        success = await reminder_service.complete(reminder_id, user.id)
        
        if success:
            await callback.answer(translate("reminder_completed", lang))
            reminders = await reminder_service.list_all(user.id, completed=False, limit=50)
            await callback.message.edit_text(
                translate("reminder_completed_msg", lang),
                reply_markup=get_reminders_list_keyboard(reminders)
            )
        else:
            await callback.answer(translate("error_generic", lang))
            
    except Exception as e:
        logger.error(f"Error in callback_reminder_done: {e}", exc_info=True)
        await callback.answer(translate("error_generic", lang), show_alert=True)


@dp.callback_query(lambda c: c.data and c.data.startswith("rem_") and c.data.endswith("_delete_confirm"))
async def callback_reminder_delete_confirm(callback: CallbackQuery):
    """Confirm reminder deletion"""
    reminder_id = int(callback.data.split("_")[1])
    user, lang = await get_user_and_lang(callback.from_user)
    reminder_service = ReminderService()
    
    reminders = await reminder_service.list_all(user.id, limit=1000)
    reminder = next((r for r in reminders if r.id == reminder_id), None)
    
    if not reminder:
        await callback.answer(translate("reminder_not_found", lang))
        return
    
    await callback.message.edit_text(
        translate("reminder_delete_confirm", lang, text=reminder.text),
        reply_markup=get_reminder_delete_confirm_keyboard(reminder_id)
    )
    await callback.answer()


@dp.callback_query(lambda c: c.data and c.data.startswith("rem_") and c.data.endswith("_delete") and not c.data.endswith("_delete_confirm"))
async def callback_reminder_delete(callback: CallbackQuery):
    """Delete reminder"""
    try:
        reminder_id = int(callback.data.split("_")[1])
        user, lang = await get_user_and_lang(callback.from_user)
        reminder_service = ReminderService()
        
        success = await reminder_service.delete(reminder_id, user.id)
        
        if success:
            await callback.answer(translate("deleted", lang))
            reminders = await reminder_service.list_all(user.id, completed=False, limit=50)
            
            if reminders:
                text = translate("reminders_title", lang, count=len(reminders)) + "\n\n"
                for i, rem in enumerate(reminders[:5], 1):
                    text += f"{i}. {rem.text}\n"
                await callback.message.edit_text(text, reply_markup=get_reminders_list_keyboard(reminders))
            else:
                await callback.message.edit_text(
                    translate("reminders_empty_after_delete", lang),
                    reply_markup=get_reminders_list_keyboard(reminders)
                )
        else:
            await callback.answer(translate("error_generic", lang))
            
    except Exception as e:
        logger.error(f"Error in callback_reminder_delete: {e}", exc_info=True)
        await callback.answer(translate("error_generic", lang), show_alert=True)

