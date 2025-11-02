"""Конфигурация бота"""
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite+aiosqlite:///adhd_bot.db')

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

