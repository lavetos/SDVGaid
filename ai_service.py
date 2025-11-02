"""AI service for OpenAI/Claude integration"""
import os
import json
from typing import Optional, List, Dict, Any
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None
try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None
from prompts import get_conversation_history, get_low_energy_prompt, get_high_energy_prompt
from ai_functions import get_function_schema
import ai_functions as af_module


class AIService:
    """Service for AI interactions"""
    
    def __init__(self):
        self.openai_client = None
        self.claude_client = None
        self.current_provider = None
        
        # Try OpenAI first
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key and OpenAI:
            try:
                self.openai_client = OpenAI(api_key=openai_key)
                self.current_provider = 'openai'
            except Exception as e:
                print(f"OpenAI init error: {e}")
        else:
            # Try Claude
            claude_key = os.getenv('ANTHROPIC_API_KEY')
            if claude_key and Anthropic:
                try:
                    self.claude_client = Anthropic(api_key=claude_key)
                    self.current_provider = 'claude'
                except Exception as e:
                    print(f"Claude init error: {e}")
        
        if not self.current_provider:
            raise ValueError(
                "❌ AI provider is required!\n"
                "Set OPENAI_API_KEY or ANTHROPIC_API_KEY in .env file.\n"
                "Get keys from: https://platform.openai.com or https://console.anthropic.com"
            )
    
    async def process_message(self, user_message: str, user_id: int, energy_level: Optional[int] = None) -> str:
        """
        Process user message with AI
        
        Args:
            user_message: User's message
            user_id: Telegram user ID
            energy_level: Optional current energy level (40, 60, 80)
        
        Returns:
            AI response
        """
        
        try:
            if self.current_provider == 'openai':
                return await self._process_openai(user_message, user_id, energy_level)
            elif self.current_provider == 'claude':
                return await self._process_claude(user_message, user_id, energy_level)
        except Exception as e:
            print(f"AI error: {e}")
            return "Упс, что-то пошло не так 😅 Попробуй ещё раз или используй обычные команды!"
    
    async def _process_openai(self, user_message: str, user_id: int, energy_level: Optional[int]) -> str:
        """Process with OpenAI"""
        messages = get_conversation_history()
        
        # Add energy level context if available
        if energy_level:
            if energy_level < 40:
                messages.append({"role": "system", "content": get_low_energy_prompt()})
            elif energy_level > 80:
                messages.append({"role": "system", "content": get_high_energy_prompt()})
        
        # Add user message
        messages.append({"role": "user", "content": user_message})
        
        # Get function tools
        tools = get_function_schema()
        
        # Call OpenAI
        response = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",  # Cheaper model
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=0.7,
            max_tokens=500
        )
        
        choice = response.choices[0]
        message = choice.message
        
        # Handle function calls
        if message.tool_calls:
            return await self._handle_tool_calls(message.tool_calls, messages, user_id)
        
        # Return text response
        return message.content
    
    async def _process_claude(self, user_message: str, user_id: int, energy_level: Optional[int]) -> str:
        """Process with Claude"""
        messages = get_conversation_history()
        
        # Add energy level context if available
        if energy_level:
            if energy_level < 40:
                messages.append({"role": "system", "content": get_low_energy_prompt()})
            elif energy_level > 80:
                messages.append({"role": "system", "content": get_high_energy_prompt()})
        
        # Add user message
        messages.append({"role": "user", "content": user_message})
        
        # Call Claude
        # Note: Claude's tools are slightly different, adapt as needed
        response = self.claude_client.messages.create(
            model="claude-3-haiku-20240307",  # Cheapest Claude model
            max_tokens=500,
            messages=[msg for msg in messages if msg["role"] != "system"],  # System messages handled differently
            system=get_conversation_history()[0]["content"]
        )
        
        return response.content[0].text
    
    async def _handle_tool_calls(self, tool_calls: List[Any], messages: List[Dict], user_id: int) -> str:
        """Handle tool/function calls from AI"""
        results = []
        
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            
            # Call function handler
            function_handler = af_module.function_handler
            if not function_handler:
                result = {"error": "Function handler not initialized"}
            else:
                # Для create_reminder нужен chat_id (telegram user_id)
                # user_id - это внутренний ID из БД, chat_id - это telegram user_id
                chat_id = user_id  # В нашей схеме они совпадают
                result = await function_handler.handle_function_call(function_name, arguments, user_id, chat_id)
            results.append(result)
            
            # Add result back to conversation
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": function_name,
                "content": json.dumps(result)
            })
        
        # If we got a successful result with actions, return user-friendly message
        if len(results) == 1:
            result = results[0]
            if result.get("success"):
                return result.get("message", "Готово! ✅")
        
        # Otherwise, get AI to summarize
        messages.append({"role": "user", "content": "Пользователь попросил..."})
        
        if self.current_provider == 'openai':
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.7,
                max_tokens=300
            )
            return response.choices[0].message.content
        
        return "Готово! ✅"
    
    async def breakdown_task(self, task_description: str) -> List[str]:
        """Break down a task into microsteps"""
        prompt = f"Разбей эту задачу на 3-5 простых шагов (каждый ≤10 минут):\n\n{task_description}\n\nВерни только список шагов, каждый с новой строки, без нумерации."
        
        try:
            response = await self.process_message(prompt, 0)
            # Parse response into list
            steps = [step.strip() for step in response.split('\n') if step.strip() and not step.strip().startswith('*')]
            return steps[:5]  # Max 5 steps
        except Exception as e:
            print(f"Error breaking down task: {e}")
            return [
                "1) Открой файл",
                "2) Сделай первый шаг",
                "3) Продолжай маленькими шагами"
            ]
    
    async def reframe_criticism(self, user_message: str) -> str:
        """Reframe user's self-criticism into support"""
        prompt = f"Пользователь говорит:\n{user_message}\n\nПереформулируй это в мягкую поддержку без самокритики. Коротко (2-3 предложения)."
        
        try:
            return await self.process_message(prompt, 0)
        except Exception as e:
            print(f"Error reframing: {e}")
            return "Ты не обязан быть идеальным 💛"


# Global AI service instance
ai_service = AIService()

