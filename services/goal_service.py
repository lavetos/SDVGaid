"""Goal service - handles all goal-related business logic"""
from typing import Optional
from db_helpers import (
    get_todays_goal, save_goal, complete_goal,
    update_goal_pomodoros, get_todays_energy
)
from translations import translate


class GoalService:
    """Service for managing daily goals"""
    
    @staticmethod
    async def get_goal_prompt(user_id: int, lang: str) -> str:
        """Get goal prompt adapted to user's energy level"""
        energy = await get_todays_energy(user_id)
        
        if energy and energy < 40:
            return translate("goal_question_low_energy", lang)
        elif energy and energy >= 80:
            return translate("goal_question_high_energy", lang)
        else:
            return translate("goal_question", lang)
    
    @staticmethod
    async def format_goal_with_progress(goal, lang: str) -> str:
        """Format goal message with pomodoro progress"""
        text = translate("goal_current", lang, text=goal.goal_text)
        
        if goal.estimated_pomodoros:
            progress_emoji = "🎉" if goal.completed_pomodoros >= goal.estimated_pomodoros else "🍅"
            text += f"\n\n{progress_emoji} " + translate("pomodoros_progress", lang, 
                                                          completed=goal.completed_pomodoros,
                                                          estimated=goal.estimated_pomodoros)
            
            if goal.completed_pomodoros < goal.estimated_pomodoros:
                remaining = goal.estimated_pomodoros - goal.completed_pomodoros
                text += "\n" + translate("pomodoros_remaining", lang, count=remaining)
        else:
            text += f"\n\n💡 " + translate("pomodoros_can_add", lang)
        
        if goal.completed:
            text += "\n\n✅ " + translate("goal_completed", lang)
        
        return text
    
    @staticmethod
    async def save_user_goal(user_id: int, goal_text: str, estimated_pomodoros: Optional[int] = None):
        """Save goal for user"""
        return await save_goal(user_id, goal_text, estimated_pomodoros)
    
    @staticmethod
    async def get_user_goal(user_id: int):
        """Get today's goal for user"""
        return await get_todays_goal(user_id)
    
    @staticmethod
    async def complete_user_goal(goal_id: int):
        """Mark goal as completed"""
        await complete_goal(goal_id, True)
    
    @staticmethod
    async def increment_pomodoro(user_id: int):
        """Increment completed pomodoros for today's goal"""
        goal = await get_todays_goal(user_id)
        if goal:
            new_count = (goal.completed_pomodoros or 0) + 1
            await update_goal_pomodoros(goal.id, completed=new_count)

