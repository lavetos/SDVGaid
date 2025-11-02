#!/bin/bash
# Run all tests

echo "🧪 Running SDVGaid Bot Tests"
echo "================================"

# Activate virtual environment if exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run pytest
pytest tests/ -v --tb=short

# Show coverage if pytest-cov is installed
if python -c "import pytest_cov" 2>/dev/null; then
    pytest tests/ --cov=. --cov-report=term-missing
fi

