"""Plan service - handles all plan-related business logic"""
from typing import List, Optional
from db_helpers import (
    get_plan_items, add_plan_item, delete_plan_item,
    toggle_plan_item, get_todays_energy
)
from translations import translate


class PlanService:
    """Service for managing daily plans"""
    
    @staticmethod
    async def get_plan_summary(user_id: int, lang: str) -> dict:
        """Get plan summary with energy-based suggestions"""
        items = await get_plan_items(user_id, completed=None)
        energy = await get_todays_energy(user_id)
        
        completed = sum(1 for item in items if item.completed)
        total = len(items)
        
        # Energy-based notes
        energy_note = ""
        if energy and energy < 40 and total > 2:
            energy_note = "\n\n" + translate("plan_energy_note_low", lang)
        elif energy and energy >= 80 and total < 3:
            energy_note = "\n\n" + translate("plan_energy_note_high", lang)
        
        # Empty plan message
        if total == 0:
            if energy and energy < 40:
                empty_msg = translate("plan_empty_low_energy", lang)
            elif energy and energy >= 80:
                empty_msg = translate("plan_empty_high_energy", lang)
            else:
                empty_msg = translate("plan_empty", lang)
        else:
            empty_msg = None
        
        return {
            'items': items,
            'completed': completed,
            'total': total,
            'energy_note': energy_note,
            'empty_msg': empty_msg
        }
    
    @staticmethod
    async def format_plan_progress(completed: int, total: int, lang: str) -> str:
        """Format plan progress message"""
        progress_emoji = "🎉" if completed == total else "💪" if completed > 0 else "✨"
        text = translate("plan_title", lang) + f"\n\n{progress_emoji} "
        text += translate("plan_completed", lang) + f": {completed}/{total}\n"
        
        if completed > 0:
            if completed == total:
                text += translate("plan_all_done", lang) + "\n\n"
            elif completed >= total / 2:
                text += translate("plan_half_done", lang, count=completed) + "\n\n"
            else:
                text += translate("plan_some_done", lang, count=completed) + "\n\n"
        
        return text
    
    @staticmethod
    async def add_item(user_id: int, text: str):
        """Add item to plan"""
        return await add_plan_item(user_id, text)
    
    @staticmethod
    async def toggle_item(item_id: int, user_id: int) -> bool:
        """Toggle item completion"""
        return await toggle_plan_item(item_id, user_id)
    
    @staticmethod
    async def delete_item(item_id: int, user_id: int) -> bool:
        """Delete plan item"""
        return await delete_plan_item(item_id, user_id)
    
    @staticmethod
    async def get_items(user_id: int, completed: Optional[bool] = None) -> List:
        """Get plan items"""
        return await get_plan_items(user_id, completed=completed)

