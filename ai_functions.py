"""Function definitions for AI function calling"""

import json
from typing import Dict, Any
from datetime import datetime


# Function tools schema for OpenAI/Claude
FUNCTION_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_reminder",
            "description": "Создать напоминание на определённое время. Используй когда пользователь просит напомнить что-то.",
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
            "description": "Сохранить заметку или мысль в 'внешнюю голову' пользователя. Всегда используй когда нужно что-то запомнить.",
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
    
    def __init__(self):
        self.handlers = {
            "create_reminder": self.handle_create_reminder,
            "add_note": self.handle_add_note,
            "start_focus_timer": self.handle_start_focus_timer,
            "parse_time_ru": self.handle_parse_time,
            "get_energy_level": self.handle_get_energy,
            "break_down_task": self.handle_break_down,
        }
    
    async def handle_function_call(self, function_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle function call by name"""
        handler = self.handlers.get(function_name)
        if not handler:
            return {"error": f"Unknown function: {function_name}"}
        
        try:
            return await handler(arguments)
        except Exception as e:
            return {"error": str(e)}
    
    async def handle_create_reminder(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle create_reminder function call"""
        # This will be implemented with actual DB calls
        return {
            "success": True,
            "message": f"Напоминание создано: {args.get('text')} на {args.get('when_iso')}"
        }
    
    async def handle_add_note(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle add_note function call"""
        return {
            "success": True,
            "message": f"Заметка сохранена: {args.get('text')}"
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
        
        # Парсим время относительно текущей даты (2025 год)
        parsed_date = dateparser.parse(
            text,
            languages=['ru', 'en'],
            settings={
                'RELATIVE_BASE': datetime.now(),  # Используем текущую дату как базу
                'PREFER_DATES_FROM': 'future'  # Предпочитаем будущие даты
            }
        )
        
        if parsed_date:
            # Конвертируем в ISO формат для создания напоминания
            iso_date = parsed_date.isoformat() + 'Z' if parsed_date.tzinfo is None else parsed_date.astimezone().isoformat()
            return {
                "success": True,
                "parsed_date": iso_date,
                "formatted": parsed_date.strftime("%d.%m.%Y %H:%M"),
                "message": f"Распарсено: {parsed_date.strftime('%d.%m.%Y %H:%M')}"
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


# Global function handler instance
function_handler = FunctionHandler()

