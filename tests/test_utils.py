"""Unit tests for utility functions"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from aiogram.types import Message, User

from utils.validation import validate_message_text, check_cancel_command


@pytest.mark.asyncio
async def test_validate_message_text_valid():
    """Test validation of valid text"""
    mock_message = MagicMock(spec=Message)
    mock_message.text = "Valid text here"
    mock_message.from_user = MagicMock(spec=User)
    mock_message.from_user.id = 123
    mock_message.from_user.language_code = 'en'
    
    with patch('utils.validation.get_user_and_lang', return_value=(None, 'en')):
        is_valid, error = await validate_message_text(mock_message, min_length=1, max_length=200)
        assert is_valid is True
        assert error is None


@pytest.mark.asyncio
async def test_validate_message_text_too_long():
    """Test validation of too long text"""
    mock_message = MagicMock(spec=Message)
    mock_message.text = "x" * 300
    mock_message.from_user = MagicMock(spec=User)
    mock_message.from_user.id = 123
    mock_message.from_user.language_code = 'en'
    
    with patch('utils.validation.get_user_and_lang', return_value=(None, 'en')):
        is_valid, error = await validate_message_text(mock_message, min_length=1, max_length=200)
        assert is_valid is False
        assert "long" in error.lower() or "200" in error


@pytest.mark.asyncio
async def test_validate_message_text_empty():
    """Test validation of empty text"""
    mock_message = MagicMock(spec=Message)
    mock_message.text = ""
    mock_message.from_user = MagicMock(spec=User)
    mock_message.from_user.id = 123
    mock_message.from_user.language_code = 'en'
    
    with patch('utils.validation.get_user_and_lang', return_value=(None, 'en')):
        is_valid, error = await validate_message_text(mock_message, min_length=1, max_length=200)
        assert is_valid is False
        assert error is not None


@pytest.mark.asyncio
async def test_check_cancel_command_cancels():
    """Test cancel command detection"""
    mock_message = MagicMock(spec=Message)
    mock_message.text = "❌ Отмена"
    mock_message.from_user = MagicMock(spec=User)
    mock_message.from_user.id = 123
    mock_message.from_user.language_code = 'en'
    
    mock_state = MagicMock()
    mock_state.clear = AsyncMock()
    
    with patch('utils.validation.get_user_and_lang', return_value=(None, 'en')):
        with patch('utils.validation.get_main_keyboard', return_value=None):
            with patch.object(mock_message, 'answer', new_callable=AsyncMock):
                result = await check_cancel_command(mock_message, mock_state)
                assert result is True
                mock_state.clear.assert_called_once()

