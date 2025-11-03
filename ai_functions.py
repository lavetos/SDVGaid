"""Function definitions for AI function calling"""

import json
from typing import Dict, Any, Optional
from datetime import datetime
from dateutil import parser as date_parser


# Function tools schema for OpenAI/Claude
FUNCTION_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_reminder",
            "description": "Создать напоминание на определённое время. ОБЯЗАТЕЛЬНО используй эту функцию когда пользователь просит напомнить что-то, поставить напоминание, или говорит о времени в будущем (через час, завтра, после обеда и т.д.).",
            "parameters": {
                "type": "object",
                "properties": {
                    "when_iso": {
                        "type": "string",
                        "description": f"Время в формате ISO 8601 в UTC. Текущая дата: {datetime.now().strftime('%Y-%m-%d')}. Пример: '2025-11-03T15:00:00Z'"
                    },
                    "text": {
                        "type": "string",
                        "description": "Текст напоминания"
                    },
                    "recurring": {
                        "type": "boolean",
                        "description": "Повторяющееся напоминание (ежедневно, еженедельно и т.д.)",
                        "default": False
                    }
                },
                "required": ["when_iso", "text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_note",
            "description": "Сохранить заметку или мысль в 'внешнюю голову' пользователя. ОБЯЗАТЕЛЬНО используй эту функцию когда пользователь просит записать, сохранить, не забыть что-то, или говорит фразы типа 'запиши', 'запомни', 'сохрани', 'не забудь', 'давай запиши', 'просто запиши', 'запиши мне'. Если в сообщении несколько вещей через 'и' (например, 'запиши X и Y'), вызови функцию несколько раз — по разу для каждой вещи. ВСЕГДА используй эту функцию когда видишь эти ключевые слова, даже если пользователь не закончил мысль.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Текст заметки"
                    }
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "start_focus_timer",
            "description": "Запустить 25-минутный Pomodoro таймер для фокуса на задаче. Используй когда пользователь хочет сфокусироваться или застрял с задачей.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "На чём сфокусироваться (краткое описание задачи)"
                    },
                    "duration": {
                        "type": "integer",
                        "description": "Длительность в минутах (по умолчанию 25)",
                        "default": 25
                    }
                },
                "required": ["topic"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "parse_time_ru",
            "description": "Распарсить свободный текст времени на русском языке ('завтра в 3 часа', 'после обеда', 'через час' и т.д.)",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Текст времени для парсинга"
                    }
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_energy_level",
            "description": "Получить текущий уровень энергии пользователя",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "break_down_task",
            "description": "Разбить большую задачу на маленькие шаги (микрошаги по 5-10 минут)",
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": "Задача для разбиения"
                    },
                    "steps": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "Массив шагов для выполнения задачи"
                    }
                },
                "required": ["task", "steps"]
            }
        }
    }
]


def get_function_tools_json() -> str:
    """Get function tools as JSON string"""
    return json.dumps(FUNCTION_TOOLS, ensure_ascii=False)


def get_function_schema() -> list:
    """Get function tools schema"""
    return FUNCTION_TOOLS


class FunctionHandler:
    """Handle function calls from AI"""
    
    def __init__(self, scheduler=None, bot=None):
        self.scheduler = scheduler
        self.bot = bot
        self.handlers = {
            "create_reminder": self.handle_create_reminder,
            "add_note": self.handle_add_note,
            "start_focus_timer": self.handle_start_focus_timer,
            "parse_time_ru": self.handle_parse_time,
            "get_energy_level": self.handle_get_energy,
            "break_down_task": self.handle_break_down,
        }
    
    async def handle_function_call(self, function_name: str, arguments: Dict[str, Any], user_id: int = 0, chat_id: int = 0) -> Dict[str, Any]:
        """Handle function call by name"""
        handler = self.handlers.get(function_name)
        if not handler:
            return {"error": f"Unknown function: {function_name}"}
        
        try:
            # Для create_reminder и add_note передаём user_id и chat_id
            if function_name in ["create_reminder", "add_note"]:
                return await handler(arguments, user_id, chat_id)
            return await handler(arguments)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"error": str(e)}
    
    async def handle_create_reminder(self, args: Dict[str, Any], user_id: int = 0, chat_id: int = 0) -> Dict[str, Any]:
        """Handle create_reminder function call"""
        from db_helpers import create_reminder, get_or_create_user
        from datetime import datetime
        import dateutil.parser
        import pytz
        
        text = args.get('text', '')
        when_iso = args.get('when_iso', '')
        
        if not text or not when_iso:
            return {
                "success": False,
                "message": "Не указан текст или время напоминания"
            }
        
        try:
            # Парсим ISO дату (ожидается UTC)
            when_datetime = dateutil.parser.isoparse(when_iso)
            
            # Если времяzone не указан, считаем что UTC
            if when_datetime.tzinfo is None:
                when_datetime = pytz.UTC.localize(when_datetime)
            
            # Конвертируем в UTC для хранения
            when_datetime_utc = when_datetime.astimezone(pytz.UTC)
            
            # Проверяем что время в будущем
            now_utc = datetime.now(pytz.UTC)
            if when_datetime_utc < now_utc:
                return {
                    "success": False,
                    "message": f"Указанное время уже прошло: {when_datetime_utc.strftime('%d.%m.%Y %H:%M')}"
                }
            
            # Получаем или создаём пользователя для получения внутреннего ID
            user = await get_or_create_user(chat_id, None, None)
            
            # Сохраняем в БД (используем внутренний user.id, не telegram_id)
            reminder = await create_reminder(user.id, text, when_datetime_utc.replace(tzinfo=None))
            
            # Получаем язык пользователя
            from db_helpers import get_user_language_code
            lang_code = await get_user_language_code(user.id)
            
            # Добавляем в планировщик
            if self.scheduler and self.bot:
                # Scheduler сам обработает timezone, но передаем timezone-aware datetime
                await self.scheduler.add_reminder(chat_id, text, when_datetime_utc, lang_code)
            
            # Показываем время в таймзоне пользователя
            from config import USER_TIMEZONE
            from translations import translate
            user_tz = pytz.timezone(USER_TIMEZONE)
            when_local = when_datetime_utc.astimezone(user_tz)
            formatted_date_local = when_local.strftime("%d.%m.%Y %H:%M")
            
            # Вычисляем через сколько времени будет напоминание
            time_diff = when_datetime_utc - now_utc
            if time_diff.total_seconds() < 60:
                time_until = translate("in_seconds", lang_code, seconds=int(time_diff.total_seconds()))
            elif time_diff.total_seconds() < 3600:
                time_until = translate("in_minutes", lang_code, minutes=int(time_diff.total_seconds() / 60))
            else:
                hours = int(time_diff.total_seconds() / 3600)
                minutes = int((time_diff.total_seconds() % 3600) / 60)
                if minutes > 0:
                    time_until = translate("in_hours_minutes", lang_code, hours=hours, minutes=minutes)
                else:
                    time_until = translate("in_hours", lang_code, hours=hours)
            
            return {
                "success": True,
                "reminder_id": reminder.id,
                "message": translate("reminder_created", lang_code, text=text, time=formatted_date_local, time_until=time_until)
            }
        except Exception as e:
            import traceback
            print(f"Error creating reminder: {e}")
            traceback.print_exc()
            return {
                "success": False,
                "message": f"Ошибка создания напоминания: {str(e)}"
            }
    
    async def handle_add_note(self, args: Dict[str, Any], user_id: int = 0, chat_id: int = 0) -> Dict[str, Any]:
        """Handle add_note function call"""
        from db_helpers import save_note, get_or_create_user
        
        text = args.get('text', '')
        if not text or not text.strip():
            return {
                "success": False,
                "message": "Текст заметки не указан"
            }
        
        try:
            # Получаем или создаём пользователя
            user = await get_or_create_user(chat_id, None, None)
            
            # Сохраняем заметку
            await save_note(user.id, text.strip())
            
            return {
                "success": True,
                "message": f"✅ Заметка сохранена: {text.strip()}"
            }
        except Exception as e:
            import traceback
            print(f"Error adding note: {e}")
            traceback.print_exc()
            return {
                "success": False,
                "message": f"Не удалось сохранить заметку: {str(e)}"
            }
    
    async def handle_start_focus_timer(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle start_focus_timer function call"""
        duration = args.get('duration', 25)
        topic = args.get('topic', 'фокус')
        return {
            "success": True,
            "message": f"Запустил фокус на {duration} минут: {topic}",
            "duration": duration,
            "topic": topic
        }
    
    async def handle_parse_time(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle parse_time_ru function call"""
        import dateparser
        from datetime import datetime
        
        text = args.get('text', '')
        
        # Парсим время относительно текущей даты
        # Для относительных времен ("через минуту", "через 10 секунд") используем текущее время
        import pytz
        from datetime import timedelta
        from config import USER_TIMEZONE
        
        # Получаем текущее время в таймзоне пользователя
        user_tz = pytz.timezone(USER_TIMEZONE)
        now_local_naive = datetime.now()  # Naive datetime для dateparser
        now_local = user_tz.localize(now_local_naive.replace(tzinfo=None))  # Timezone-aware для вычислений
        now_utc = datetime.now(pytz.UTC)
        
        # Специальная обработка для "через X секунд/минут/часов"
        if "через" in text.lower():
            # Парсим относительное время начиная с СЕЙЧАС (используем naive для dateparser)
            parsed_date = dateparser.parse(
                text,
                languages=['ru', 'en'],
                settings={
                    'RELATIVE_BASE': now_local_naive,  # Базовое время - СЕЙЧАС (naive)
                    'PREFER_DATES_FROM': 'future',  # Предпочитаем будущие даты
                    'STRICT_PARSING': False,
                    'TIMEZONE': USER_TIMEZONE  # Используем таймзону пользователя
                }
            )
        else:
            # Для абсолютных времен используем обычный парсинг
            parsed_date = dateparser.parse(
                text,
                languages=['ru', 'en'],
                settings={
                    'RELATIVE_BASE': now_local_naive,
                    'PREFER_DATES_FROM': 'future',
                    'TIMEZONE': USER_TIMEZONE
                }
            )
        
        # Если парсинг не удался и это "через X", пробуем ручной парсинг
        if not parsed_date and "через" in text.lower():
            # Простой парсинг для "через N секунд/минут"
            import re
            match = re.search(r'через\s+(\d+)\s+(секунд[ыу]?|минут[ыу]?|час[аов]?)', text.lower())
            if match:
                value = int(match.group(1))
                unit = match.group(2)
                if 'секунд' in unit:
                    parsed_date = now_local + timedelta(seconds=value)
                elif 'минут' in unit:
                    parsed_date = now_local + timedelta(minutes=value)
                elif 'час' in unit:
                    parsed_date = now_local + timedelta(hours=value)
                else:
                    parsed_date = None
        
        if parsed_date:
            # Делаем timezone-aware если не указан
            if parsed_date.tzinfo is None:
                # Используем таймзону пользователя из конфига
                import pytz
                from config import USER_TIMEZONE
                local_tz = pytz.timezone(USER_TIMEZONE)
                parsed_date = local_tz.localize(parsed_date)
            
            # Конвертируем в UTC
            parsed_date_utc = parsed_date.astimezone(pytz.UTC)
            
            # Проверяем что время в будущем
            if parsed_date_utc < now_utc:
                return {
                    "success": False,
                    "message": f"Указанное время уже прошло: {parsed_date_utc.strftime('%d.%m.%Y %H:%M')}. Попробуй 'через 10 секунд' или 'через 1 минуту'."
                }
            
            # Конвертируем в ISO формат для создания напоминания
            iso_date = parsed_date_utc.isoformat()
            return {
                "success": True,
                "parsed_date": iso_date,
                "formatted": parsed_date_utc.strftime("%d.%m.%Y %H:%M"),
                "message": f"Распарсено: {parsed_date_utc.strftime('%d.%m.%Y %H:%M')}"
            }
        else:
            return {
                "success": False,
                "message": f"Не удалось распарсить время: {text}"
            }
    
    async def handle_get_energy(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get_energy_level function call"""
        return {
            "success": True,
            "message": "Уровень энергии получен"
        }
    
    async def handle_break_down(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle break_down_task function call"""
        steps = args.get('steps', [])
        return {
            "success": True,
            "message": f"Задача разбита на {len(steps)} шагов",
            "steps": steps
        }


# Global function handler instance (will be initialized with scheduler in bot.py)
function_handler: Optional[FunctionHandler] = None

