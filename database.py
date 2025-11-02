"""Модели базы данных"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, LargeBinary
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from config import DATABASE_URL

Base = declarative_base()


class User(Base):
    """Модель пользователя"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(255))
    name = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)


class EnergyLog(Base):
    """Лог уровня энергии"""
    __tablename__ = 'energy_logs'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    energy_level = Column(Integer, nullable=False)  # 40, 60, 80
    date = Column(DateTime, default=datetime.utcnow)


class DailyGoal(Base):
    """Главное дело дня"""
    __tablename__ = 'daily_goals'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    goal_text = Column(Text, nullable=False)
    completed = Column(Boolean, default=False)
    date = Column(DateTime, default=datetime.utcnow)


class Note(Base):
    """Заметка пользователя (внешняя голова)"""
    __tablename__ = 'notes'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class EveningCheckIn(Base):
    """Вечерний чек-ин"""
    __tablename__ = 'evening_checkins'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    what_worked = Column(Text)
    what_tired = Column(Text)
    what_helped = Column(Text)
    date = Column(DateTime, default=datetime.utcnow)


class UserState(Base):
    """Текущее состояние пользователя"""
    __tablename__ = 'user_states'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True, nullable=False)
    in_quiet_mode = Column(Boolean, default=False)
    quiet_mode_until = Column(DateTime)
    pomodoro_active = Column(Boolean, default=False)
    pomodoro_until = Column(DateTime)


class Reminder(Base):
    """Напоминания"""
    __tablename__ = 'reminders'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    when_datetime = Column(DateTime, nullable=False)
    completed = Column(Boolean, default=False)
    recurring = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class NoteEmbedding(Base):
    """Эмбеддинги заметок для поиска"""
    __tablename__ = 'note_embeddings'
    
    id = Column(Integer, primary_key=True)
    note_id = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False)
    embedding = Column(LargeBinary)  # numpy array as bytes
    created_at = Column(DateTime, default=datetime.utcnow)


class DailyPlanItem(Base):
    """План на день - список задач"""
    __tablename__ = 'daily_plan_items'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    completed = Column(Boolean, default=False)
    date = Column(DateTime, default=datetime.utcnow)
    order = Column(Integer, default=0)  # Порядок отображения


# Создание движка и сессии
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """Инициализация базы данных"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    """Получить сессию базы данных"""
    async with async_session() as session:
        yield session

