"""Scheduler for reminders and notifications"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from datetime import datetime, timedelta
from database import async_session
from sqlalchemy import select
from typing import Optional
import pytz


class ReminderScheduler:
    """Scheduler for bot reminders"""
    
    def __init__(self, bot):
        self.bot = bot
        self.scheduler = AsyncIOScheduler()
        self.timezone = pytz.timezone('UTC')  # Can be configured per user
    
    def start(self):
        """Start the scheduler"""
        self.scheduler.start()
        print("Scheduler started ⏰")
    
    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        print("Scheduler stopped ⏰")
    
    async def add_reminder(self, chat_id: int, text: str, when: datetime):
        """Add a reminder"""
        job_id = f"reminder_{chat_id}_{when.timestamp()}"
        
        self.scheduler.add_job(
            self.send_reminder,
            trigger=DateTrigger(run_date=when, timezone=self.timezone),
            id=job_id,
            args=[chat_id, text],
            replace_existing=True
        )
        print(f"Reminder scheduled: {text} at {when} ⏰")
    
    async def send_reminder(self, chat_id: int, text: str):
        """Send reminder message"""
        try:
            await self.bot.send_message(
                chat_id=chat_id,
                text=f"📢 Напоминание:\n\n{text}\n\nЧто сделано? 💛",
                parse_mode='HTML'
            )
        except Exception as e:
            print(f"Error sending reminder: {e}")
    
    def schedule_evening_checkin(self, chat_id: int, hour: int = 20, minute: int = 0):
        """Schedule daily evening check-in"""
        self.scheduler.add_job(
            self.send_evening_checkin,
            trigger=CronTrigger(hour=hour, minute=minute, timezone=self.timezone),
            id=f"evening_{chat_id}",
            args=[chat_id],
            replace_existing=True
        )
        print(f"Evening check-in scheduled for {hour}:{minute:02d} ⏰")
    
    async def send_evening_checkin(self, chat_id: int):
        """Send evening check-in reminder"""
        try:
            await self.bot.send_message(
                chat_id=chat_id,
                text="🌙 Привет! Как прошёл день?\n\nВремя для вечернего чек-ина 💛",
                parse_mode='HTML'
            )
        except Exception as e:
            print(f"Error sending evening check-in: {e}")
    
    def cancel_job(self, job_id: str):
        """Cancel a scheduled job"""
        try:
            self.scheduler.remove_job(job_id)
        except Exception as e:
            print(f"Error canceling job: {e}")


# Global scheduler instance (will be initialized in bot.py)
scheduler: Optional[ReminderScheduler] = None

