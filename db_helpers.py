"""Вспомогательные функции для работы с БД"""
from database import async_session, User, EnergyLog, DailyGoal, Note, EveningCheckIn, UserState, Reminder, DailyPlanItem
from datetime import datetime, timedelta
from sqlalchemy import select, func


async def get_or_create_user(telegram_id: int, username: str = None, name: str = None) -> User:
    """Получить или создать пользователя"""
    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        
        if not user:
            user = User(telegram_id=telegram_id, username=username, name=name)
            session.add(user)
            await session.commit()
        
        return user


async def save_energy_level(user_id: int, energy_level: int):
    """Сохранить уровень энергии"""
    async with async_session() as session:
        energy_log = EnergyLog(user_id=user_id, energy_level=energy_level)
        session.add(energy_log)
        await session.commit()


async def get_todays_goal(user_id: int) -> DailyGoal:
    """Получить цель на сегодня"""
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    async with async_session() as session:
        result = await session.execute(
            select(DailyGoal)
            .where(DailyGoal.user_id == user_id)
            .where(DailyGoal.date >= today_start)
            .order_by(DailyGoal.id.desc())
        )
        return result.scalar_one_or_none()


async def save_goal(user_id: int, goal_text: str) -> DailyGoal:
    """Сохранить цель дня"""
    async with async_session() as session:
        goal = DailyGoal(user_id=user_id, goal_text=goal_text)
        session.add(goal)
        await session.commit()
        return goal


async def complete_goal(goal_id: int, completed: bool = True):
    """Отметить цель как выполненную"""
    async with async_session() as session:
        result = await session.execute(select(DailyGoal).where(DailyGoal.id == goal_id))
        goal = result.scalar_one()
        goal.completed = completed
        await session.commit()


async def save_note(user_id: int, text: str) -> Note:
    """Сохранить заметку"""
    async with async_session() as session:
        note = Note(user_id=user_id, text=text)
        session.add(note)
        await session.commit()
        return note


async def get_user_notes(user_id: int, limit: int = 20) -> list[Note]:
    """Получить последние заметки пользователя"""
    async with async_session() as session:
        result = await session.execute(
            select(Note)
            .where(Note.user_id == user_id)
            .order_by(Note.id.desc())
            .limit(limit)
        )
        return result.scalars().all()


async def get_user_state(user_id: int) -> UserState:
    """Получить состояние пользователя"""
    async with async_session() as session:
        result = await session.execute(select(UserState).where(UserState.user_id == user_id))
        state = result.scalar_one_or_none()
        
        if not state:
            state = UserState(user_id=user_id)
            session.add(state)
            await session.commit()
        
        return state


async def set_quiet_mode(user_id: int, duration_seconds: int):
    """Установить режим тишины"""
    async with async_session() as session:
        result = await session.execute(select(UserState).where(UserState.user_id == user_id))
        state = result.scalar_one_or_none()
        
        if not state:
            state = UserState(user_id=user_id)
            session.add(state)
        
        state.in_quiet_mode = True
        state.quiet_mode_until = datetime.utcnow() + timedelta(seconds=duration_seconds)
        await session.commit()


async def disable_quiet_mode(user_id: int):
    """Отключить режим тишины"""
    async with async_session() as session:
        result = await session.execute(select(UserState).where(UserState.user_id == user_id))
        state = result.scalar_one()
        state.in_quiet_mode = False
        state.quiet_mode_until = None
        await session.commit()


async def save_evening_checkin(user_id: int, what_worked: str = None, what_tired: str = None, what_helped: str = None):
    """Сохранить вечерний чек-ин"""
    async with async_session() as session:
        checkin = EveningCheckIn(user_id=user_id, what_worked=what_worked, what_tired=what_tired, what_helped=what_helped)
        session.add(checkin)
        await session.commit()


async def get_energy_stats_week(user_id: int) -> dict:
    """Получить статистику энергии за неделю"""
    week_ago = datetime.utcnow() - timedelta(days=7)
    async with async_session() as session:
        result = await session.execute(
            select(
                func.avg(EnergyLog.energy_level).label('avg_energy'),
                func.count(EnergyLog.id).label('days_count')
            )
            .where(EnergyLog.user_id == user_id)
            .where(EnergyLog.date >= week_ago)
        )
        row = result.first()
        return {
            'avg_energy': round(row.avg_energy) if row.avg_energy else 0,
            'days_count': row.days_count
        }


# ==================== REMINDERS ====================

async def create_reminder(user_id: int, text: str, when_datetime: datetime, recurring: bool = False) -> Reminder:
    """Создать напоминание"""
    async with async_session() as session:
        reminder = Reminder(
            user_id=user_id,
            text=text,
            when_datetime=when_datetime,
            recurring=recurring
        )
        session.add(reminder)
        await session.commit()
        await session.refresh(reminder)
        return reminder


async def get_all_reminders(user_id: int, completed: bool = False, limit: int = 50) -> list[Reminder]:
    """Получить все напоминания пользователя"""
    async with async_session() as session:
        result = await session.execute(
            select(Reminder)
            .where(Reminder.user_id == user_id)
            .where(Reminder.completed == completed)
            .order_by(Reminder.when_datetime.asc())
            .limit(limit)
        )
        return result.scalars().all()


async def get_reminder(reminder_id: int, user_id: int) -> Reminder:
    """Получить напоминание по ID"""
    async with async_session() as session:
        result = await session.execute(
            select(Reminder)
            .where(Reminder.id == reminder_id)
            .where(Reminder.user_id == user_id)
        )
        return result.scalar_one_or_none()


async def update_reminder(reminder_id: int, user_id: int, text: str = None, when_datetime: datetime = None) -> bool:
    """Обновить напоминание"""
    async with async_session() as session:
        result = await session.execute(
            select(Reminder)
            .where(Reminder.id == reminder_id)
            .where(Reminder.user_id == user_id)
        )
        reminder = result.scalar_one_or_none()
        
        if not reminder:
            return False
        
        if text:
            reminder.text = text
        if when_datetime:
            reminder.when_datetime = when_datetime
        
        await session.commit()
        return True


async def delete_reminder(reminder_id: int, user_id: int) -> bool:
    """Удалить напоминание"""
    async with async_session() as session:
        result = await session.execute(
            select(Reminder)
            .where(Reminder.id == reminder_id)
            .where(Reminder.user_id == user_id)
        )
        reminder = result.scalar_one_or_none()
        
        if not reminder:
            return False
        
        await session.delete(reminder)
        await session.commit()
        return True


async def complete_reminder(reminder_id: int, user_id: int) -> bool:
    """Отметить напоминание как выполненное"""
    async with async_session() as session:
        result = await session.execute(
            select(Reminder)
            .where(Reminder.id == reminder_id)
            .where(Reminder.user_id == user_id)
        )
        reminder = result.scalar_one_or_none()
        
        if not reminder:
            return False
        
        reminder.completed = True
        await session.commit()
        return True


# ==================== DAILY PLAN ====================

async def add_plan_item(user_id: int, text: str) -> DailyPlanItem:
    """Добавить пункт в план дня"""
    async with async_session() as session:
        # Get max order for today
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        result = await session.execute(
            select(func.max(DailyPlanItem.order))
            .where(DailyPlanItem.user_id == user_id)
            .where(DailyPlanItem.date >= today_start)
        )
        max_order = result.scalar() or 0
        
        item = DailyPlanItem(user_id=user_id, text=text, order=max_order + 1)
        session.add(item)
        await session.commit()
        await session.refresh(item)
        return item


async def get_plan_items(user_id: int, date: datetime = None, completed: bool = None) -> list[DailyPlanItem]:
    """Получить пункты плана на день"""
    if date is None:
        date = datetime.now()
    date_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
    
    async with async_session() as session:
        query = select(DailyPlanItem).where(
            DailyPlanItem.user_id == user_id,
            DailyPlanItem.date >= date_start
        )
        
        if completed is not None:
            query = query.where(DailyPlanItem.completed == completed)
        
        result = await session.execute(query.order_by(DailyPlanItem.order.asc()))
        return result.scalars().all()


async def get_plan_item(item_id: int, user_id: int) -> DailyPlanItem:
    """Получить пункт плана по ID"""
    async with async_session() as session:
        result = await session.execute(
            select(DailyPlanItem)
            .where(DailyPlanItem.id == item_id)
            .where(DailyPlanItem.user_id == user_id)
        )
        return result.scalar_one_or_none()


async def update_plan_item(item_id: int, user_id: int, text: str) -> bool:
    """Обновить пункт плана"""
    async with async_session() as session:
        result = await session.execute(
            select(DailyPlanItem)
            .where(DailyPlanItem.id == item_id)
            .where(DailyPlanItem.user_id == user_id)
        )
        item = result.scalar_one_or_none()
        
        if not item:
            return False
        
        item.text = text
        await session.commit()
        return True


async def delete_plan_item(item_id: int, user_id: int) -> bool:
    """Удалить пункт плана"""
    async with async_session() as session:
        result = await session.execute(
            select(DailyPlanItem)
            .where(DailyPlanItem.id == item_id)
            .where(DailyPlanItem.user_id == user_id)
        )
        item = result.scalar_one_or_none()
        
        if not item:
            return False
        
        await session.delete(item)
        await session.commit()
        return True


async def toggle_plan_item(item_id: int, user_id: int) -> bool:
    """Переключить выполненность пункта плана"""
    async with async_session() as session:
        result = await session.execute(
            select(DailyPlanItem)
            .where(DailyPlanItem.id == item_id)
            .where(DailyPlanItem.user_id == user_id)
        )
        item = result.scalar_one_or_none()
        
        if not item:
            return False
        
        item.completed = not item.completed
        await session.commit()
        return True

