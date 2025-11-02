# Tests for SDVGaid Bot

Automated test suite for verifying bot functionality.

## Test Structure

- `test_database.py` - database operations tests
- `test_ai_functions.py` - AI functions and handlers tests
- `test_scheduler.py` - reminder scheduler tests
- `test_date_parsing.py` - date and time parsing tests
- `test_config.py` - configuration tests

## Running Tests

### All tests
```bash
pytest tests/ -v
```

### Specific file
```bash
pytest tests/test_database.py -v
```

### Specific test
```bash
pytest tests/test_database.py::test_create_user -v
```

### With code coverage (if pytest-cov is installed)
```bash
pytest tests/ --cov=. --cov-report=term-missing
```

### Using script
```bash
./run_tests.sh
```

## Requirements

- `pytest>=7.4.0`
- `pytest-asyncio>=0.21.0`
- All dependencies from `requirements.txt`

## Notes

- Database tests use the real database from configuration (or you can configure a separate test database)
- AI function tests work without real API (mocks)
- Scheduler is tested with bot mocks

