"""Сервис для обработки голосовых сообщений"""
import os
import tempfile
from openai import OpenAI
from config import OPENAI_API_KEY
from aiogram.types import Message
import logging

logger = logging.getLogger(__name__)


class VoiceService:
    """Сервис для распознавания голоса"""
    
    def __init__(self):
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY required for voice recognition")
        self.client = OpenAI(api_key=OPENAI_API_KEY)
    
    async def download_voice_file(self, message: Message, bot) -> str:
        """Скачать голосовое сообщение во временный файл"""
        if not message.voice:
            raise ValueError("Message has no voice")
        
        voice_file = await bot.get_file(message.voice.file_id)
        
        # Создаем временный файл
        import tempfile
        import os
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, f"voice_{message.from_user.id}_{message.message_id}.ogg")
        
        # Скачиваем файл
        await bot.download_file(voice_file.file_path, destination=temp_path)
        
        return temp_path
    
    async def transcribe_voice(self, voice_path: str, language: str = "ru") -> str:
        """
        Распознать голосовое сообщение с помощью OpenAI Whisper
        
        Args:
            voice_path: Путь к файлу голосового сообщения
            language: Язык распознавания (по умолчанию 'ru')
        
        Returns:
            Распознанный текст
        """
        try:
            with open(voice_path, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language=language,
                    response_format="text"
                )
                return transcript.strip()
        except Exception as e:
            logger.error(f"Error transcribing voice: {e}")
            raise
        finally:
            # Удаляем временный файл
            try:
                if os.path.exists(voice_path):
                    os.remove(voice_path)
            except Exception as e:
                logger.warning(f"Could not delete temp file {voice_path}: {e}")
    
    async def process_voice_message(self, message: Message, bot) -> str:
        """
        Полный цикл обработки голосового сообщения:
        1. Скачать файл
        2. Распознать речь
        3. Вернуть текст
        
        Args:
            message: Telegram message с голосовым сообщением
            bot: Bot instance для скачивания файла
        
        Returns:
            Распознанный текст
        """
        if not message.voice:
            raise ValueError("Message has no voice")
        
        # Проверка длительности (Whisper работает с файлами до 25 MB)
        if message.voice.duration > 3600:  # 1 час максимум
            raise ValueError("Voice message too long (max 1 hour)")
        
        voice_path = await self.download_voice_file(message, bot)
        text = await self.transcribe_voice(voice_path)
        
        return text


# Глобальный экземпляр сервиса
voice_service = None

def get_voice_service() -> VoiceService:
    """Получить или создать экземпляр VoiceService"""
    global voice_service
    if voice_service is None:
        try:
            voice_service = VoiceService()
        except ValueError as e:
            logger.warning(f"Voice service not available: {e}")
            return None
    return voice_service

