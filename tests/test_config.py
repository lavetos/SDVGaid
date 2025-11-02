"""Tests for configuration"""
import os
import pytest
from config import BOT_TOKEN, DATABASE_URL


def test_bot_token_required():
    """Test that BOT_TOKEN is required"""
    # This should be set in .env
    assert BOT_TOKEN is not None
    assert len(BOT_TOKEN) > 0


def test_database_url_default():
    """Test database URL default"""
    # Should have default value
    assert DATABASE_URL is not None
    assert "sqlite" in DATABASE_URL or "postgresql" in DATABASE_URL.lower()


def test_database_url_format():
    """Test database URL format"""
    # Should be valid SQLAlchemy URL
    assert "://" in DATABASE_URL

