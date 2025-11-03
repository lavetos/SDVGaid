"""Evening check-in service"""
from db_helpers import (
    save_evening_checkin, get_todays_goal, set_day_rating
)


class EveningService:
    """Service for evening check-ins"""
    
    @staticmethod
    async def save_checkin(
        user_id: int,
        telegram_id: int,
        what_worked: str,
        what_tired: str,
        what_helped: str
    ):
        """Save evening check-in"""
        # db_helpers uses user_id (internal), not telegram_id
        await save_evening_checkin(user_id, what_worked, what_tired, what_helped)
    
    @staticmethod
    async def should_ask_about_goal(user_id: int) -> tuple:
        """Check if should ask about goal completion"""
        goal = await get_todays_goal(user_id)
        if goal and not goal.completed:
            return True, goal
        return False, None
    
    @staticmethod
    async def save_rating(user_id: int, rating: int):
        """Save day rating"""
        await set_day_rating(user_id, date=None, rating=rating)

