"""Reminder service - handles all reminder-related business logic"""
from datetime import datetime
from typing import List, Optional
from db_helpers import (
    create_reminder, get_all_reminders, delete_reminder,
    complete_reminder, get_user_language_code
)
from bot import scheduler


class ReminderService:
    """Service for managing reminders"""
    
    @staticmethod
    async def create(user_id: int, text: str, when: datetime, chat_id: int):
        """Create reminder"""
        # Save to database
        reminder = await create_reminder(user_id, text, when.replace(tzinfo=None))
        
        # Get user language for reminder messages
        lang = await get_user_language_code(user_id)
        
        # Schedule - import from bot to avoid circular import
        from bot import scheduler
        await scheduler.add_reminder(chat_id, text, when, lang)
        
        return reminder
    
    @staticmethod
    async def list_all(user_id: int, completed: bool = False, limit: int = 50) -> List:
        """Get all reminders"""
        return await get_all_reminders(user_id, completed=completed, limit=limit)
    
    @staticmethod
    async def delete(reminder_id: int, user_id: int) -> bool:
        """Delete reminder"""
        return await delete_reminder(reminder_id, user_id)
    
    @staticmethod
    async def complete(reminder_id: int, user_id: int) -> bool:
        """Mark reminder as completed"""
        return await complete_reminder(reminder_id, user_id)

