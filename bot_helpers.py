"""Helper functions for bot handlers"""

from db_helpers import get_or_create_user, get_user_language_code
from translations import translate, get_user_language


async def get_user_and_lang(telegram_user, telegram_id: int = None):
    """
    Get user and their language code.
    
    Args:
        telegram_user: Telegram user object (message.from_user or callback.from_user)
        telegram_id: Optional telegram_id (if telegram_user not available)
    
    Returns:
        tuple: (user object, language_code)
    """
    if telegram_id:
        user = await get_or_create_user(
            telegram_id,
            getattr(telegram_user, 'username', None),
            getattr(telegram_user, 'full_name', None),
            language_code=getattr(telegram_user, 'language_code', None) if telegram_user else None
        )
    else:
        user = await get_or_create_user(
            telegram_user.id,
            telegram_user.username,
            telegram_user.full_name,
            language_code=getattr(telegram_user, 'language_code', None)
        )
    
    lang = user.language_code if user.language_code else get_user_language(telegram_user)
    return user, lang


async def get_lang_from_user_id(user_id: int) -> str:
    """Get language code from user_id"""
    return await get_user_language_code(user_id)

