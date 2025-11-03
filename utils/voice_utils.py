"""Voice processing utilities"""
from typing import Optional
from aiogram.types import Message
import logging

logger = logging.getLogger(__name__)


async def process_voice_to_text(
    message: Message,
    bot,
    user,
    lang: str
) -> Optional[str]:
    """
    Process voice message and convert to text.
    Returns text or None if failed.
    """
    from voice_service import get_voice_service
    from translations import translate
    from keyboards import get_cancel_keyboard
    
    voice_service = get_voice_service()
    
    if not voice_service:
        await message.answer(
            translate("voice_not_available", lang),
            reply_markup=get_cancel_keyboard(lang)
        )
        return None
    
    processing_msg = await message.answer(translate("voice_processing", lang))
    
    try:
        text = await voice_service.process_voice_message(message, bot)
        
        if text and text.strip():
            await processing_msg.delete()
            from translations import translate
            await message.answer(
                translate("voice_recognized", lang, text=text),
                reply_markup=None
            )
            return text.strip()
        else:
            await processing_msg.edit_text(
                translate("voice_recognition_failed", lang),
                reply_markup=get_cancel_keyboard(lang)
            )
            return None
            
    except ValueError as e:
        error_msg = str(e)
        if "too long" in error_msg.lower():
            await processing_msg.edit_text(
                translate("voice_too_long", lang),
                reply_markup=get_cancel_keyboard(lang)
            )
        else:
            await processing_msg.edit_text(
                translate("voice_processing_error", lang),
                reply_markup=get_cancel_keyboard(lang)
            )
        return None
        
    except Exception as e:
        logger.error(f"Voice recognition error: {e}")
        await processing_msg.edit_text(
            translate("voice_processing_error", lang),
            reply_markup=get_cancel_keyboard(lang)
        )
        return None

