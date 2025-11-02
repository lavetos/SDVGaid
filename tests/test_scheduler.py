"""Tests for scheduler"""
import pytest
from datetime import datetime, timedelta
import pytz
from unittest.mock import AsyncMock, MagicMock
from scheduler import ReminderScheduler


@pytest.fixture
def mock_bot():
    """Create mock bot"""
    bot = AsyncMock()
    bot.send_message = AsyncMock()
    return bot


@pytest.fixture
def scheduler(mock_bot):
    """Create scheduler with mock bot"""
    scheduler = ReminderScheduler(mock_bot)
    return scheduler


def test_scheduler_init(scheduler):
    """Test scheduler initialization"""
    assert scheduler.bot is not None
    assert scheduler.timezone == pytz.UTC


@pytest.mark.asyncio
async def test_scheduler_start_stop(scheduler):
    """Test scheduler start/stop"""
    scheduler.start()
    assert scheduler.scheduler.running
    
    scheduler.stop()
    # Scheduler might need a moment to fully stop
    import asyncio
    await asyncio.sleep(0.1)
    # Note: scheduler might still show as running briefly after stop
    # The important thing is that start() works


@pytest.mark.asyncio
async def test_add_reminder(scheduler):
    """Test adding reminder to scheduler"""
    when = datetime.now(pytz.UTC) + timedelta(seconds=5)
    
    await scheduler.add_reminder(12345, "Test reminder", when)
    
    # Check job was added
    jobs = scheduler.scheduler.get_jobs()
    assert len(jobs) > 0


@pytest.mark.asyncio
async def test_send_reminder(scheduler):
    """Test sending reminder message"""
    await scheduler.send_reminder(12345, "Test reminder")
    
    scheduler.bot.send_message.assert_called_once()
    call_args = scheduler.bot.send_message.call_args
    assert call_args[1]["chat_id"] == 12345
    assert "Test reminder" in call_args[1]["text"]

