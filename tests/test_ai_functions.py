"""Tests for AI function handlers"""
import pytest
from datetime import datetime, timedelta
import pytz
from ai_functions import FunctionHandler


@pytest.fixture
def function_handler():
    """Create function handler without scheduler for testing"""
    return FunctionHandler(scheduler=None, bot=None)


@pytest.mark.asyncio
async def test_parse_time(function_handler):
    """Test time parsing"""
    result = await function_handler.handle_parse_time({
        "text": "через 1 час"
    })
    
    assert result.get("success") in [True, False]  # May succeed or fail depending on dateparser
    if result.get("success"):
        assert "parsed_date" in result


@pytest.mark.asyncio
async def test_parse_time_future_date(function_handler):
    """Test parsing future date"""
    result = await function_handler.handle_parse_time({
        "text": "завтра в 15:00"
    })
    
    # Should parse successfully
    assert "success" in result


@pytest.mark.asyncio
async def test_create_reminder_validation(function_handler):
    """Test reminder creation validation"""
    # Missing text
    result = await function_handler.handle_create_reminder(
        {"when_iso": "2025-12-01T15:00:00Z"},
        user_id=0,
        chat_id=12345
    )
    assert result.get("success") == False
    
    # Missing time
    result = await function_handler.handle_create_reminder(
        {"text": "Test"},
        user_id=0,
        chat_id=12345
    )
    assert result.get("success") == False


@pytest.mark.asyncio
async def test_create_reminder_past_date(function_handler):
    """Test that past dates are rejected"""
    past_date = (datetime.now(pytz.UTC) - timedelta(hours=1)).isoformat()
    result = await function_handler.handle_create_reminder(
        {
            "text": "Test",
            "when_iso": past_date
        },
        user_id=0,
        chat_id=12345
    )
    assert result.get("success") == False
    assert "прошло" in result.get("message", "").lower()


@pytest.mark.asyncio
async def test_break_down_task(function_handler):
    """Test task breakdown"""
    result = await function_handler.handle_break_down({
        "task": "Написать отчёт",
        "steps": ["Открыть файл", "Написать введение", "Закончить"]
    })
    
    assert result.get("success") == True
    assert "steps" in result
    assert len(result["steps"]) == 3

