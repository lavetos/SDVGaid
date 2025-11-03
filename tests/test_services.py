"""Unit tests for services layer"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import pytz

from services.goal_service import GoalService
from services.plan_service import PlanService
from services.note_service import NoteService
from services.reminder_service import ReminderService
from services.energy_service import EnergyService
from services.evening_service import EveningService


# ==================== GOAL SERVICE TESTS ====================

@pytest.mark.asyncio
async def test_goal_service_get_goal_prompt_low_energy():
    """Test goal prompt adaptation for low energy"""
    with patch('services.goal_service.get_todays_energy', return_value=35):
        prompt = await GoalService.get_goal_prompt(1, 'en')
        assert "tiny" in prompt.lower() or "small" in prompt.lower()
    
    with patch('services.goal_service.get_todays_energy', return_value=35):
        prompt = await GoalService.get_goal_prompt(1, 'ru')
        assert "маленькое" in prompt.lower() or "маленьке" in prompt.lower()


@pytest.mark.asyncio
async def test_goal_service_get_goal_prompt_high_energy():
    """Test goal prompt adaptation for high energy"""
    with patch('services.goal_service.get_todays_energy', return_value=85):
        prompt = await GoalService.get_goal_prompt(1, 'en')
        assert "energy" in prompt.lower() or "few tasks" in prompt.lower()


@pytest.mark.asyncio
async def test_goal_service_format_goal_with_progress():
    """Test goal formatting with pomodoro progress"""
    mock_goal = MagicMock()
    mock_goal.goal_text = "Test goal"
    mock_goal.estimated_pomodoros = 3
    mock_goal.completed_pomodoros = 2
    mock_goal.completed = False
    
    def mock_translate(key, lang, **kwargs):
        if key == "goal_current":
            return f"🎯 Your goal today:\n\n{kwargs.get('text', '')}"
        elif key == "pomodoros_progress":
            return f"Pomodoros: {kwargs.get('completed', 0)}/{kwargs.get('estimated', 0)}"
        elif key == "pomodoros_remaining":
            return f"Remaining: {kwargs.get('count', 0)} pomodoros"
        elif key == "pomodoros_can_add":
            return "You can add pomodoro estimate"
        else:
            return key
    
    with patch('services.goal_service.translate', side_effect=mock_translate):
        formatted = await GoalService.format_goal_with_progress(mock_goal, 'en')
        
        assert "Test goal" in formatted
        assert "3" in formatted
        assert "2" in formatted


# ==================== PLAN SERVICE TESTS ====================

@pytest.mark.asyncio
async def test_plan_service_get_plan_summary():
    """Test plan summary generation"""
    mock_items = [
        MagicMock(completed=True),
        MagicMock(completed=False),
        MagicMock(completed=True),
    ]
    
    with patch('services.plan_service.get_plan_items', return_value=mock_items):
        with patch('services.plan_service.get_todays_energy', return_value=50):
            summary = await PlanService.get_plan_summary(1, 'en')
            
            assert summary['completed'] == 2
            assert summary['total'] == 3
            assert summary['items'] == mock_items


@pytest.mark.asyncio
async def test_plan_service_get_plan_summary_low_energy():
    """Test plan summary with energy note for low energy"""
    mock_items = [
        MagicMock(completed=False),
        MagicMock(completed=False),
        MagicMock(completed=False),
        MagicMock(completed=False),
    ]
    
    with patch('services.plan_service.get_plan_items', return_value=mock_items):
        with patch('services.plan_service.get_todays_energy', return_value=30):
            summary = await PlanService.get_plan_summary(1, 'en')
            
            assert "low energy" in summary['energy_note'].lower() or "low" in summary['energy_note'].lower()


@pytest.mark.asyncio
async def test_plan_service_format_plan_progress():
    """Test plan progress formatting"""
    text = await PlanService.format_plan_progress(2, 3, 'en')
    
    assert "2" in text
    assert "3" in text
    assert "plan" in text.lower()


# ==================== NOTE SERVICE TESTS ====================

@pytest.mark.asyncio
async def test_note_service_save():
    """Test note saving"""
    mock_note = MagicMock()
    mock_note.text = "Test note"
    
    with patch('services.note_service.save_note', return_value=mock_note):
        note = await NoteService.save(1, "Test note")
        assert note.text == "Test note"


@pytest.mark.asyncio
async def test_note_service_list_all():
    """Test listing all notes"""
    mock_notes = [MagicMock(), MagicMock()]
    
    with patch('services.note_service.get_user_notes', return_value=mock_notes):
        notes = await NoteService.list_all(1, limit=50)
        assert len(notes) == 2


@pytest.mark.asyncio
async def test_note_service_search():
    """Test note search"""
    mock_notes = [
        MagicMock(text="Buy milk"),
        MagicMock(text="Call mom"),
        MagicMock(text="Milk shop"),
    ]
    
    with patch('services.note_service.get_user_notes', return_value=mock_notes):
        results = await NoteService.search(1, "milk", limit=20)
        assert len(results) == 2
        assert all("milk" in note.text.lower() for note in results)


# ==================== ENERGY SERVICE TESTS ====================

@pytest.mark.asyncio
async def test_energy_service_get_advice_low():
    """Test energy advice for low energy"""
    advice = await EnergyService.get_advice(35, 'en')
    assert "low" in advice.lower() or "simple" in advice.lower()


@pytest.mark.asyncio
async def test_energy_service_get_advice_high():
    """Test energy advice for high energy"""
    advice = await EnergyService.get_advice(85, 'en')
    assert "high" in advice.lower() or "energy" in advice.lower()


# ==================== EVENING SERVICE TESTS ====================

@pytest.mark.asyncio
async def test_evening_service_should_ask_about_goal():
    """Test if should ask about goal"""
    mock_goal = MagicMock()
    mock_goal.completed = False
    
    with patch('services.evening_service.get_todays_goal', return_value=mock_goal):
        should_ask, goal = await EveningService.should_ask_about_goal(1)
        assert should_ask is True
        assert goal == mock_goal


@pytest.mark.asyncio
async def test_evening_service_should_not_ask_if_completed():
    """Test if should not ask when goal is completed"""
    mock_goal = MagicMock()
    mock_goal.completed = True
    
    with patch('services.evening_service.get_todays_goal', return_value=mock_goal):
        should_ask, goal = await EveningService.should_ask_about_goal(1)
        assert should_ask is False


# ==================== REMINDER SERVICE TESTS ====================

@pytest.mark.asyncio
async def test_reminder_service_list_all():
    """Test listing all reminders"""
    mock_reminders = [MagicMock(), MagicMock()]
    
    with patch('services.reminder_service.get_all_reminders', return_value=mock_reminders):
        reminders = await ReminderService.list_all(1, completed=False, limit=50)
        assert len(reminders) == 2


@pytest.mark.asyncio
async def test_reminder_service_create():
    """Test reminder creation"""
    mock_reminder = MagicMock()
    mock_reminder.id = 1
    when = datetime.now(pytz.UTC) + timedelta(hours=1)
    
    with patch('services.reminder_service.create_reminder', return_value=mock_reminder):
        with patch('services.reminder_service.get_user_language_code', return_value='en'):
            with patch('bot.scheduler') as mock_scheduler_instance:
                mock_scheduler_instance.add_reminder = AsyncMock()
                
                reminder = await ReminderService.create(1, "Test reminder", when, 123)
                
                assert reminder.id == 1
                mock_scheduler_instance.add_reminder.assert_called_once()

