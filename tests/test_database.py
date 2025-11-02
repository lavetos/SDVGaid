"""Tests for database operations"""
import pytest
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select
from database import Base, User, Reminder, DailyPlanItem, Note
from db_helpers import (
    get_or_create_user, create_reminder, get_all_reminders,
    add_plan_item, get_plan_items, save_note, get_user_notes,
    delete_note, delete_all_notes
)


@pytest.mark.asyncio
async def test_create_user():
    """Test user creation"""
    user = await get_or_create_user(999999, "testuser", "Test User")
    assert user.telegram_id == 999999
    assert user.username == "testuser"
    assert user.name == "Test User"
    
    # Test idempotency
    user2 = await get_or_create_user(999999, "testuser2", "Test User 2")
    assert user2.id == user.id  # Same user
    assert user2.username == "testuser"  # Original username preserved


@pytest.mark.asyncio
async def test_create_reminder():
    """Test reminder creation"""
    user = await get_or_create_user(999998, "testuser", "Test User")
    when = datetime.utcnow() + timedelta(hours=1)
    
    reminder = await create_reminder(user.id, "Test reminder", when)
    assert reminder.text == "Test reminder"
    assert reminder.user_id == user.id
    assert not reminder.completed


@pytest.mark.asyncio
async def test_get_reminders():
    """Test getting reminders"""
    user = await get_or_create_user(999997, "testuser", "Test User")
    when1 = datetime.utcnow() + timedelta(hours=1)
    when2 = datetime.utcnow() + timedelta(hours=2)
    
    await create_reminder(user.id, "Reminder 1", when1)
    await create_reminder(user.id, "Reminder 2", when2)
    
    reminders = await get_all_reminders(user.id, completed=False)
    assert len(reminders) >= 2
    texts = [r.text for r in reminders]
    assert "Reminder 1" in texts
    assert "Reminder 2" in texts


@pytest.mark.asyncio
async def test_add_plan_item():
    """Test adding plan item"""
    user = await get_or_create_user(999996, "testuser", "Test User")
    item = await add_plan_item(user.id, "Test task")
    assert item.text == "Test task"
    assert not item.completed


@pytest.mark.asyncio
async def test_get_plan_items():
    """Test getting plan items"""
    user = await get_or_create_user(999995, "testuser", "Test User")
    await add_plan_item(user.id, "Task 1")
    await add_plan_item(user.id, "Task 2")
    
    items = await get_plan_items(user.id)
    assert len(items) >= 2
    texts = [item.text for item in items]
    assert "Task 1" in texts
    assert "Task 2" in texts


@pytest.mark.asyncio
async def test_save_and_get_notes():
    """Test note operations"""
    user = await get_or_create_user(999994, "testuser", "Test User")
    note = await save_note(user.id, "Test note")
    assert note.text == "Test note"
    
    notes = await get_user_notes(user.id)
    assert len(notes) >= 1
    assert any(n.text == "Test note" for n in notes)


@pytest.mark.asyncio
async def test_delete_notes():
    """Test note deletion"""
    user = await get_or_create_user(999993, "testuser", "Test User")
    await save_note(user.id, "Note 1")
    await save_note(user.id, "Note 2")
    
    count = await delete_all_notes(user.id)
    assert count >= 2
    
    notes = await get_user_notes(user.id)
    assert len(notes) == 0

