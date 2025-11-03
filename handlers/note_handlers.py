"""Note handlers - following Single Responsibility Principle"""
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

from keyboards import get_cancel_keyboard, get_main_keyboard
from services.note_service import NoteService
from utils.voice_utils import process_voice_to_text
from utils.validation import validate_message_text, check_cancel_command
from handlers.base import handle_voice_message, validate_text, handle_cancel
from bot_helpers import get_user_and_lang
from translations import translate
import logging

logger = logging.getLogger(__name__)


@dp.message(Command("note"))
@dp.message(lambda m: m.text and ("📝 Заметки" in m.text or "Заметки" in m.text))
async def cmd_note(message: Message, state: FSMContext):
    """Add note"""
    user, lang = await get_user_and_lang(message.from_user)
    await message.answer(
        translate("note_question", lang),
        reply_markup=get_cancel_keyboard(lang)
    )
    await state.set_state(BotStates.waiting_note)


@dp.message(StateFilter(BotStates.waiting_note))
@handle_voice_message
@validate_text(min_length=1, max_length=500)
@handle_cancel()
async def process_note(message: Message, state: FSMContext):
    """Process note input"""
    user, lang = await get_user_and_lang(message.from_user)
    note_service = NoteService()
    
    # Check cancel
    if await check_cancel_command(message, state):
        return
    
    # Validate
    is_valid, error_msg = await validate_message_text(message, min_length=1, max_length=500)
    if not is_valid:
        await message.answer(error_msg, reply_markup=get_cancel_keyboard(lang))
        return
    
    try:
        note_text = message.text.strip()
        note = await note_service.save(user.id, note_text)
        
        await message.answer(
            translate("note_saved", lang, text=note.text),
            reply_markup=get_main_keyboard(lang)
        )
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error saving note: {e}", exc_info=True)
        await message.answer(translate("error_generic", lang), reply_markup=get_main_keyboard(lang))
        await state.clear()


@dp.message(Command("notes"))
async def cmd_notes(message: Message, state: FSMContext):
    """Show all notes"""
    user, lang = await get_user_and_lang(message.from_user)
    note_service = NoteService()
    
    notes = await note_service.list_all(user.id, limit=50)
    
    if not notes:
        await message.answer(
            translate("notes_empty", lang),
            reply_markup=get_main_keyboard(lang)
        )
        return
    
    # Show last 10 notes
    recent_notes = notes[:10]
    
    text = translate("notes_list_title", lang, recent=len(recent_notes), total=len(notes)) + "\n\n"
    
    for i, note in enumerate(recent_notes, 1):
        date_str = note.created_at.strftime("%d.%m %H:%M") if note.created_at else ""
        text += f"{i}. {note.text}"
        if date_str:
            text += f" ({date_str})"
        text += "\n"
    
    if len(notes) > 10:
        text += f"\n" + translate("notes_more", lang, count=len(notes) - 10) + "\n"
    
    text += "\n" + translate("notes_hint", lang)
    
    await message.answer(text, reply_markup=get_main_keyboard(lang))

