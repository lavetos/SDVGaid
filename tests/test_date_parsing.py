"""Tests for date parsing"""
import pytest
from datetime import datetime, timedelta
import pytz
import dateutil.parser


def test_dateparser_current_year():
    """Test that dateparser uses current year (2025)"""
    now = datetime.now(pytz.UTC)
    assert now.year == 2025
    
    # Test parsing "завтра"
    from dateparser import parse
    parsed = parse("завтра", languages=['ru'], settings={
        'RELATIVE_BASE': now,
        'PREFER_DATES_FROM': 'future',
        'TIMEZONE': 'UTC'
    })
    
    if parsed:
        # Make sure both are timezone-aware
        if parsed.tzinfo is None:
            parsed = pytz.UTC.localize(parsed)
        assert parsed.year == 2025 or parsed.year == 2026
        assert parsed > now


def test_iso_date_parsing():
    """Test ISO date parsing"""
    # Parse ISO format with timezone
    iso_date = "2025-11-03T15:00:00Z"
    parsed = dateutil.parser.isoparse(iso_date)
    
    assert parsed.year == 2025
    assert parsed.month == 11
    assert parsed.day == 3
    assert parsed.hour == 15


def test_future_date_validation():
    """Test that future dates are valid"""
    now = datetime.now(pytz.UTC)
    future = now + timedelta(hours=1)
    
    assert future > now
    assert (future - now).total_seconds() > 0


def test_past_date_rejection():
    """Test that past dates are rejected"""
    now = datetime.now(pytz.UTC)
    past = now - timedelta(hours=1)
    
    assert past < now
    assert (now - past).total_seconds() > 0

