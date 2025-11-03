"""Конфигурация бота"""
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')

# Database configuration
# Автоматическое определение: PostgreSQL в облаке, SQLite локально
_DEFAULT_SQLITE_URL = 'sqlite+aiosqlite:///adhd_bot.db'
DATABASE_URL = os.getenv('DATABASE_URL', _DEFAULT_SQLITE_URL)

# Если установлен POSTGRES_URL или DATABASE_URL содержит postgres, используем PostgreSQL
POSTGRES_URL = os.getenv('POSTGRES_URL') or os.getenv('POSTGRES_PRISMA_URL') or os.getenv('DATABASE_PRISMA_URL')

if POSTGRES_URL:
    # PostgreSQL для production (облако)
    # Конвертируем postgres:// в postgresql+asyncpg://
    if POSTGRES_URL.startswith('postgres://'):
        POSTGRES_URL = POSTGRES_URL.replace('postgres://', 'postgresql+asyncpg://', 1)
    elif not POSTGRES_URL.startswith('postgresql'):
        POSTGRES_URL = f'postgresql+asyncpg://{POSTGRES_URL}'
    
    DATABASE_URL = POSTGRES_URL
    print("🗄️  Using PostgreSQL (production mode)")
elif DATABASE_URL.startswith('postgres'):
    # Уже правильный формат PostgreSQL
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql+asyncpg://', 1)
    elif not 'asyncpg' in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://', 1)
    print("🗄️  Using PostgreSQL")
else:
    # SQLite для локальной разработки
    print("💾 Using SQLite (local development)")

# AI configuration (optional)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не установлен! Создай файл .env с токеном бота.")

# Настройки Pomodoro
POMODORO_WORK_TIME = 25 * 60  # 25 минут в секундах
POMODORO_BREAK_TIME = 5 * 60  # 5 минут в секундах

# Настройки режима тишины
QUIET_MODE_DURATION = 30 * 60  # 30 минут в секундах

# Настройки таймзоны
# По умолчанию Испания (Europe/Madrid), можно переопределить через переменную окружения
USER_TIMEZONE = os.getenv('USER_TIMEZONE', 'Europe/Madrid')

