"""Base handlers and decorators following SOLID principles"""
from functools import wraps
from typing import Callable, Optional, Tuple
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from bot_helpers import get_user_and_lang
from translations import translate
import logging

logger = logging.getLogger(__name__)


class BaseHandler:
    """Base handler class following Template Method pattern"""
    
    async def handle(self, *args, **kwargs):
        """Template method - defines the algorithm structure"""
        try:
            # Get user and language
            user, lang = await self._get_user_and_lang(*args, **kwargs)
            
            # Pre-process
            await self.pre_process(user, lang, *args, **kwargs)
            
            # Execute handler
            result = await self.process(user, lang, *args, **kwargs)
            
            # Post-process
            await self.post_process(user, lang, result, *args, **kwargs)
            
            return result
        except Exception as e:
            logger.error(f"Error in {self.__class__.__name__}: {e}", exc_info=True)
            await self.handle_error(user if 'user' in locals() else None, 
                                   lang if 'lang' in locals() else 'en', 
                                   e, *args, **kwargs)
    
    async def _get_user_and_lang(self, *args, **kwargs) -> Tuple:
        """Get user and language from message/callback"""
        if args and isinstance(args[0], (Message, CallbackQuery)):
            obj = args[0]
            return await get_user_and_lang(obj.from_user)
        return None, 'en'
    
    async def pre_process(self, user, lang, *args, **kwargs):
        """Hook for pre-processing (can be overridden)"""
        pass
    
    async def process(self, user, lang, *args, **kwargs):
        """Main processing logic (must be overridden)"""
        raise NotImplementedError
    
    async def post_process(self, user, lang, result, *args, **kwargs):
        """Hook for post-processing (can be overridden)"""
        pass
    
    async def handle_error(self, user: Optional, lang: str, error: Exception, *args, **kwargs):
        """Error handling (can be overridden)"""
        from keyboards import get_main_keyboard
        if args and isinstance(args[0], (Message, CallbackQuery)):
            obj = args[0]
            if isinstance(obj, Message):
                await obj.answer(translate("error_generic", lang), reply_markup=get_main_keyboard(lang))
            elif isinstance(obj, CallbackQuery):
                await obj.answer(translate("error_generic", lang), show_alert=True)


def handle_voice_message(func: Callable) -> Callable:
    """Decorator to handle voice messages - converts to text"""
    @wraps(func)
    async def wrapper(message: Message, state: FSMContext, *args, **kwargs):
        if message.voice:
            from voice_service import get_voice_service
            from keyboards import get_cancel_keyboard
            from bot_helpers import get_user_and_lang
            
            user, lang = await get_user_and_lang(message.from_user)
            voice_service = get_voice_service()
            
            if not voice_service:
                await message.answer(
                    translate("voice_not_available", lang),
                    reply_markup=get_cancel_keyboard(lang)
                )
                return
            
            processing_msg = await message.answer(translate("voice_processing", lang))
            
            try:
                from bot import bot
                text = await voice_service.process_voice_message(message, bot)
                
                if text and text.strip():
                    message.text = text
                    await processing_msg.delete()
                    await message.answer(
                        translate("voice_recognized", lang, text=text),
                        reply_markup=None
                    )
                else:
                    await processing_msg.edit_text(
                        translate("voice_recognition_failed", lang),
                        reply_markup=get_cancel_keyboard(lang)
                    )
                    return
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
                return
            except Exception as e:
                logger.error(f"Voice recognition error: {e}")
                await processing_msg.edit_text(
                    translate("voice_processing_error", lang),
                    reply_markup=get_cancel_keyboard(lang)
                )
                return
        
        return await func(message, state, *args, **kwargs)
    
    return wrapper


def validate_text(
    min_length: int = 1,
    max_length: int = 200,
    allow_empty: bool = False
) -> Callable:
    """Decorator to validate message text"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(message: Message, state: FSMContext, *args, **kwargs):
            from keyboards import get_cancel_keyboard
            from bot_helpers import get_user_and_lang
            
            user, lang = await get_user_and_lang(message.from_user)
            
            if not message.text or not message.text.strip():
                if not allow_empty:
                    await message.answer(
                        translate("text_required", lang),
                        reply_markup=get_cancel_keyboard(lang)
                    )
                    return
            else:
                text_len = len(message.text.strip())
                if text_len < min_length:
                    await message.answer(
                        translate("text_too_short", lang, min=min_length),
                        reply_markup=get_cancel_keyboard(lang)
                    )
                    return
                if text_len > max_length:
                    await message.answer(
                        translate("text_too_long", lang, max=max_length),
                        reply_markup=get_cancel_keyboard(lang)
                    )
                    return
            
            return await func(message, state, *args, **kwargs)
        
        return wrapper
    return decorator


def handle_cancel(cancel_keywords: Optional[list] = None) -> Callable:
    """Decorator to handle cancel command"""
    if cancel_keywords is None:
        cancel_keywords = ["❌ Отмена", "отмена", "Отмена", "/cancel", "/start", "cancel", "skip", "пропустить"]
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(message: Message, state: FSMContext, *args, **kwargs):
            from keyboards import get_main_keyboard, get_cancel_keyboard
            from bot_helpers import get_user_and_lang
            
            if message.text and message.text.strip() in cancel_keywords:
                await state.clear()
                user, lang = await get_user_and_lang(message.from_user)
                cancel_msg = translate("operation_cancelled", lang)
                await message.answer(cancel_msg, reply_markup=get_main_keyboard(lang))
                return
            
            return await func(message, state, *args, **kwargs)
        
        return wrapper
    return decorator


async def with_user_and_lang(func: Callable, *args, **kwargs):
    """Helper to get user and lang before function call"""
    if args and isinstance(args[0], (Message, CallbackQuery)):
        obj = args[0]
        user, lang = await get_user_and_lang(obj.from_user)
        return await func(user, lang, *args, **kwargs)
    return await func(*args, **kwargs)

