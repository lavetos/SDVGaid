"""Validation utilities following DRY principle"""
from typing import Optional, Tuple
from aiogram.types import Message
from bot_helpers import get_user_and_lang
from translations import translate
from keyboards import get_cancel_keyboard


async def validate_message_text(
    message: Message,
    min_length: int = 1,
    max_length: int = 200,
    allow_empty: bool = False
) -> Tuple[bool, Optional[str]]:
    """
    Validate message text.
    Returns (is_valid, error_message)
    """
    user, lang = await get_user_and_lang(message.from_user)
    
    if not message.text or not message.text.strip():
        if not allow_empty:
            return False, translate("text_required", lang)
        return True, None
    
    text = message.text.strip()
    text_len = len(text)
    
    if text_len < min_length:
        return False, translate("text_too_short", lang, min=min_length)
    
    if text_len > max_length:
        return False, translate("text_too_long", lang, max=max_length)
    
    return True, None


async def check_cancel_command(
    message: Message,
    state,
    cancel_keywords: Optional[list] = None
) -> bool:
    """
    Check if message is a cancel command.
    Returns True if cancelled, False otherwise.
    If cancelled, clears state and sends cancel message.
    """
    if cancel_keywords is None:
        cancel_keywords = ["❌ Отмена", "отмена", "Отмена", "/cancel", "/start", 
                          "cancel", "skip", "пропустить", "пропустити"]
    
    if message.text and message.text.strip().lower() in [kw.lower() for kw in cancel_keywords]:
        await state.clear()
        user, lang = await get_user_and_lang(message.from_user)
        from keyboards import get_main_keyboard
        await message.answer(
            translate("operation_cancelled", lang),
            reply_markup=get_main_keyboard(lang)
        )
        return True
    
    return False

