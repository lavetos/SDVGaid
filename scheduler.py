"""Scheduler for reminders and notifications"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from datetime import datetime, timedelta
from database import async_session
from sqlalchemy import select
from typing import Optional
import pytz
from config import USER_TIMEZONE


class ReminderScheduler:
    """Scheduler for bot reminders"""
    
    def __init__(self, bot):
        self.bot = bot
        self.scheduler = AsyncIOScheduler()
        self.timezone = pytz.timezone('UTC')  # Храним в UTC
        self.user_timezone = pytz.timezone(USER_TIMEZONE)  # Таймзона пользователя для отображения
    
    def start(self):
        """Start the scheduler"""
        self.scheduler.start()
        print("Scheduler started ⏰")
    
    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        print("Scheduler stopped ⏰")
    
    async def add_reminder(self, chat_id: int, text: str, when: datetime, lang_code: str = 'en'):
        """Add a reminder"""
        # Убеждаемся что дата timezone-aware
        if when.tzinfo is None:
            when = self.timezone.localize(when)
        else:
            when = when.astimezone(self.timezone)
        
        job_id = f"reminder_{chat_id}_{int(when.timestamp())}"
        
        self.scheduler.add_job(
            self.send_reminder,
            trigger=DateTrigger(run_date=when, timezone=self.timezone),
            id=job_id,
            args=[chat_id, text, lang_code],
            replace_existing=True
        )
        # Показываем время в таймзоне пользователя
        when_local = when.astimezone(self.user_timezone)
        print(f"⏰ Reminder scheduled: '{text}' at {when_local.strftime('%d.%m.%Y %H:%M:%S')} ({USER_TIMEZONE}) / {when.strftime('%d.%m.%Y %H:%M:%S')} (UTC)")
    
    async def send_reminder(self, chat_id: int, text: str, lang_code: str = 'en'):
        """Send reminder message - мягко, без давления для СДВГ, с заметными уведомлениями"""
        try:
            from translations import translate
            
            # Отправляем основное сообщение
            now_local = datetime.now(self.user_timezone)
            time_str = now_local.strftime("%H:%M")
            
            reminder_msg = translate("reminder_sent", lang_code, time=time_str, text=text)
            
            await self.bot.send_message(
                chat_id=chat_id,
                text=reminder_msg,
                parse_mode='HTML'
            )
            
            # Отправляем дополнительное уведомление через 2 секунды для большей заметности
            # (это не звонок, но делает уведомление более заметным)
            import asyncio
            await asyncio.sleep(2)
            await self.bot.send_message(
                chat_id=chat_id,
                text=f"💬 {text}",
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

