"""Вспомогательные функции для работы с БД"""
from database import async_session, User, EnergyLog, DailyGoal, Note, EveningCheckIn, UserState, Reminder, DailyPlanItem
from datetime import datetime, timedelta
from sqlalchemy import select, func, Integer


async def get_or_create_user(telegram_id: int, username: str = None, name: str = None, language_code: str = None) -> User:
    """Получить или создать пользователя"""
    from translations import get_language_code
    
    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        
        if not user:
            lang = get_language_code(language_code) if language_code else 'en'
            user = User(telegram_id=telegram_id, username=username, name=name, language_code=lang)
            session.add(user)
            await session.commit()
        else:
            # Update language if provided and different
            if language_code:
                new_lang = get_language_code(language_code)
                if user.language_code != new_lang:
                    user.language_code = new_lang
                    await session.commit()
        
        return user


async def get_user_language_code(user_id: int) -> str:
    """Get user's language code"""
    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        return user.language_code if user and user.language_code else 'en'


async def save_energy_level(user_id: int, energy_level: int):
    """Сохранить уровень энергии"""
    async with async_session() as session:
        # Check if there's already an energy log for today
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        result = await session.execute(
            select(EnergyLog)
            .where(EnergyLog.user_id == user_id)
            .where(EnergyLog.date >= today_start)
            .order_by(EnergyLog.date.desc())
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            # Update existing
            existing.energy_level = energy_level
        else:
            # Create new
            energy_log = EnergyLog(user_id=user_id, energy_level=energy_level)
            session.add(energy_log)
        
        await session.commit()


async def get_todays_energy(user_id: int) -> int:
    """Получить уровень энергии на сегодня"""
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    async with async_session() as session:
        result = await session.execute(
            select(EnergyLog)
            .where(EnergyLog.user_id == user_id)
            .where(EnergyLog.date >= today_start)
            .order_by(EnergyLog.date.desc())
        )
        energy_log = result.scalar_one_or_none()
        return energy_log.energy_level if energy_log else None


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


async def save_goal(user_id: int, goal_text: str, estimated_pomodoros: int = None) -> DailyGoal:
    """Сохранить цель дня"""
    async with async_session() as session:
        goal = DailyGoal(user_id=user_id, goal_text=goal_text, estimated_pomodoros=estimated_pomodoros)
        session.add(goal)
        await session.commit()
        return goal


async def update_goal_pomodoros(goal_id: int, estimated: int = None, completed: int = None):
    """Обновить оценку или прогресс помидоров для цели"""
    async with async_session() as session:
        result = await session.execute(select(DailyGoal).where(DailyGoal.id == goal_id))
        goal = result.scalar_one()
        if estimated is not None:
            goal.estimated_pomodoros = estimated
        if completed is not None:
            goal.completed_pomodoros = completed
        await session.commit()


async def increment_goal_pomodoro(user_id: int):
    """Увеличить счетчик выполненных помидоров для сегодняшней цели"""
    goal = await get_todays_goal(user_id)
    if goal:
        # Если есть оценка - обновляем, если нет - просто увеличиваем счетчик
        new_count = (goal.completed_pomodoros or 0) + 1
        await update_goal_pomodoros(goal.id, completed=new_count)


async def complete_goal(goal_id: int, completed: bool = True):
    """Отметить цель как выполненную"""
    async with async_session() as session:
        result = await session.execute(select(DailyGoal).where(DailyGoal.id == goal_id))
        goal = result.scalar_one()
        goal.completed = completed
        await session.commit()


async def set_day_rating(user_id: int, date: datetime = None, rating: int = None):
    """Установить оценку дня (1-10)"""
    if date is None:
        date = datetime.now()
    date_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
    
    async with async_session() as session:
        # Находим цель на этот день
        result = await session.execute(
            select(DailyGoal)
            .where(DailyGoal.user_id == user_id)
            .where(DailyGoal.date >= date_start)
            .order_by(DailyGoal.id.desc())
        )
        goal = result.scalar_one_or_none()
        
        if goal:
            goal.day_rating = rating
        else:
            # Создаем запись если её нет
            goal = DailyGoal(
                user_id=user_id,
                goal_text="",
                completed=False,
                date=date_start,
                day_rating=rating
            )
            session.add(goal)
        
        await session.commit()
        return goal


async def get_daily_summary(user_id: int, date: datetime = None):
    """Получить сводку дня: цель, план, оценка"""
    if date is None:
        date = datetime.now()
    date_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
    date_end = date_start + timedelta(days=1)
    
    async with async_session() as session:
        # Цель дня
        goal_result = await session.execute(
            select(DailyGoal)
            .where(DailyGoal.user_id == user_id)
            .where(DailyGoal.date >= date_start)
            .where(DailyGoal.date < date_end)
            .order_by(DailyGoal.id.desc())
        )
        goal = goal_result.scalar_one_or_none()
        
        # План
        plan_result = await session.execute(
            select(DailyPlanItem)
            .where(DailyPlanItem.user_id == user_id)
            .where(DailyPlanItem.date >= date_start)
            .where(DailyPlanItem.date < date_end)
            .order_by(DailyPlanItem.order.asc())
        )
        plan_items = plan_result.scalars().all()
        
        # Вечерний чек-ин
        checkin_result = await session.execute(
            select(EveningCheckIn)
            .where(EveningCheckIn.user_id == user_id)
            .where(EveningCheckIn.date >= date_start)
            .where(EveningCheckIn.date < date_end)
            .order_by(EveningCheckIn.id.desc())
        )
        checkin = checkin_result.scalar_one_or_none()
        
        return {
            'goal': goal,
            'plan_items': list(plan_items),
            'checkin': checkin,
            'date': date_start
        }


async def get_days_history(user_id: int, limit: int = 30):
    """Получить историю дней"""
    async with async_session() as session:
        # Получаем все цели (используем простой select без func.date для совместимости)
        goals_result = await session.execute(
            select(DailyGoal)
            .where(DailyGoal.user_id == user_id)
            .order_by(DailyGoal.date.desc())
            .limit(limit * 2)
        )
        goals = goals_result.scalars().all()
        
        # Группируем по дням
        days_map = {}
        for goal in goals:
            # Нормализуем дату (убираем время)
            goal_date = goal.date.replace(hour=0, minute=0, second=0, microsecond=0) if goal.date else datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            day_key = goal_date.isoformat()[:10]  # Используем только дату без времени
            
            if day_key not in days_map:
                days_map[day_key] = {
                    'date': goal_date,
                    'goal': goal.goal_text if goal.goal_text else None,
                    'goal_completed': goal.completed,
                    'rating': goal.day_rating,
                    'pomodoros': f"{goal.completed_pomodoros or 0}/{goal.estimated_pomodoros or 0}" if goal.estimated_pomodoros else None,
                    'plan_count': 0,
                    'plan_completed': 0
                }
            else:
                # Обновляем если есть более свежие данные
                if goal.goal_text:
                    days_map[day_key]['goal'] = goal.goal_text
                if goal.day_rating:
                    days_map[day_key]['rating'] = goal.day_rating
                if goal.estimated_pomodoros:
                    days_map[day_key]['pomodoros'] = f"{goal.completed_pomodoros or 0}/{goal.estimated_pomodoros or 0}"
                days_map[day_key]['goal_completed'] = goal.completed
        
        # Добавляем данные о плане (используем более простой подход для совместимости)
        all_plans_result = await session.execute(
            select(DailyPlanItem)
            .where(DailyPlanItem.user_id == user_id)
            .order_by(DailyPlanItem.date.desc())
        )
        all_plans = all_plans_result.scalars().all()
        
        # Группируем планы по дням
        plans_by_day = {}
        for plan_item in all_plans:
            plan_date = plan_item.date.replace(hour=0, minute=0, second=0, microsecond=0) if plan_item.date else None
            if plan_date:
                day_key = plan_date.isoformat() if isinstance(plan_date, datetime) else str(plan_date)
                if day_key not in plans_by_day:
                    plans_by_day[day_key] = {'total': 0, 'completed': 0}
                plans_by_day[day_key]['total'] += 1
                if plan_item.completed:
                    plans_by_day[day_key]['completed'] += 1
        
        for day_key, plan_data in plans_by_day.items():
            if day_key in days_map:
                days_map[day_key]['plan_count'] = plan_data['total']
                days_map[day_key]['plan_completed'] = plan_data['completed']
            elif day_key not in days_map:
                # Парсим дату из ключа
                try:
                    if isinstance(day_key, str):
                        day_date = datetime.fromisoformat(day_key.replace('Z', '+00:00')) if 'T' in day_key else datetime.strptime(day_key, '%Y-%m-%d')
                    else:
                        day_date = day_key
                except:
                    continue
                days_map[day_key] = {
                    'date': day_date,
                    'goal': None,
                    'goal_completed': False,
                    'rating': None,
                    'pomodoros': None,
                    'plan_count': plan_data['total'],
                    'plan_completed': plan_data['completed']
                }
        
        # Сортируем по дате (новые первыми)
        days_list = sorted(days_map.values(), key=lambda x: x['date'], reverse=True)
        return days_list[:limit]


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


async def delete_note(note_id: int, user_id: int) -> bool:
    """Удалить заметку"""
    async with async_session() as session:
        result = await session.execute(
            select(Note)
            .where(Note.id == note_id)
            .where(Note.user_id == user_id)
        )
        note = result.scalar_one_or_none()
        
        if not note:
            return False
        
        await session.delete(note)
        await session.commit()
        return True


async def delete_all_notes(user_id: int) -> int:
    """Удалить все заметки пользователя"""
    async with async_session() as session:
        result = await session.execute(
            select(Note).where(Note.user_id == user_id)
        )
        notes = result.scalars().all()
        count = len(notes)
        
        for note in notes:
            await session.delete(note)
        
        await session.commit()
        return count


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

