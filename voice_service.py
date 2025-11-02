"""Сервис для обработки голосовых сообщений (полностью бесплатно через faster-whisper)"""
import os
import tempfile
import logging
from aiogram.types import Message

logger = logging.getLogger(__name__)

try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    logger.warning("faster-whisper not installed. Voice recognition will be disabled.")


class VoiceService:
    """Сервис для распознавания голоса (полностью бесплатно, локально)"""
    
    def __init__(self):
        if not WHISPER_AVAILABLE:
            raise ValueError("faster-whisper not installed. Install with: pip install faster-whisper")
        
        # Используем base модель - баланс между скоростью и качеством
        # Модели: tiny, base, small, medium, large-v2, large-v3
        # base - быстрая и достаточно точная для русского языка (~150 MB)
        # При первом запуске модель скачается автоматически
        try:
            self.model = WhisperModel("base", device="cpu", compute_type="int8")
            logger.info("✅ Whisper model loaded (base, CPU) - полностью бесплатно!")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise
    
    async def download_voice_file(self, message: Message, bot) -> str:
        """Скачать голосовое сообщение во временный файл"""
        if not message.voice:
            raise ValueError("Message has no voice")
        
        voice_file = await bot.get_file(message.voice.file_id)
        
        # Создаем временный файл в системной temp директории
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, f"voice_{message.from_user.id}_{message.message_id}.ogg")
        
        # Скачиваем файл
        await bot.download_file(voice_file.file_path, destination=temp_path)
        
        return temp_path
    
    async def transcribe_voice(self, voice_path: str, language: str = "ru") -> str:
        """
        Распознать голосовое сообщение с помощью faster-whisper (полностью бесплатно)
        
        Args:
            voice_path: Путь к файлу голосового сообщения (OGG или WAV)
            language: Язык распознавания (по умолчанию 'ru')
        
        Returns:
            Распознанный текст
        """
        try:
            # faster-whisper работает с OGG напрямую
            # Используем VAD (Voice Activity Detection) для фильтрации тишины
            segments, info = self.model.transcribe(
                voice_path,
                language=language,
                beam_size=5,
                vad_filter=True,  # Фильтрует тишину - улучшает качество
                vad_parameters=dict(min_silence_duration_ms=500)
            )
            
            # Собираем текст из сегментов
            text_parts = []
            for segment in segments:
                text_parts.append(segment.text.strip())
            
            text = " ".join(text_parts).strip()
            return text
            
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
        2. Распознать речь (полностью бесплатно, локально)
        3. Вернуть текст
        
        Args:
            message: Telegram message с голосовым сообщением
            bot: Bot instance для скачивания файла
        
        Returns:
            Распознанный текст
        """
        if not message.voice:
            raise ValueError("Message has no voice")
        
        # Проверка длительности (разумный лимит для производительности)
        if message.voice.duration > 300:  # 5 минут максимум
            raise ValueError("Voice message too long (max 5 minutes)")
        
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
            logger.info("✅ Voice service initialized (free, local, no API needed)")
        except Exception as e:
            logger.warning(f"Voice service not available: {e}")
            return None
    return voice_service
