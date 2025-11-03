"""Energy service - handles energy level management"""
from typing import Optional
from db_helpers import save_energy_level, get_todays_energy
from translations import translate


class EnergyService:
    """Service for managing energy levels"""
    
    @staticmethod
    async def save(user_id: int, energy_level: int):
        """Save energy level"""
        await save_energy_level(user_id, energy_level)
    
    @staticmethod
    async def get_today(user_id: int) -> Optional[int]:
        """Get today's energy level"""
        return await get_todays_energy(user_id)
    
    @staticmethod
    async def get_advice(energy_level: int, lang: str) -> str:
        """Get advice based on energy level"""
        if energy_level < 40:
            return translate("energy_low_advice", lang)
        elif energy_level < 60:
            return translate("energy_medium_advice", lang)
        else:
            return translate("energy_high_advice", lang)

