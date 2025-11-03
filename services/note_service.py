"""Note service - handles all note-related business logic"""
from typing import List, Optional
from db_helpers import (
    save_note, get_user_notes, delete_note, delete_all_notes
)


class NoteService:
    """Service for managing notes"""
    
    @staticmethod
    async def save(user_id: int, text: str):
        """Save note"""
        return await save_note(user_id, text)
    
    @staticmethod
    async def list_all(user_id: int, limit: int = 50) -> List:
        """Get all notes"""
        return await get_user_notes(user_id, limit=limit)
    
    @staticmethod
    async def delete(note_id: int, user_id: int) -> bool:
        """Delete note"""
        return await delete_note(note_id, user_id)
    
    @staticmethod
    async def delete_all(user_id: int) -> int:
        """Delete all notes"""
        return await delete_all_notes(user_id)
    
    @staticmethod
    async def search(user_id: int, query: str, limit: int = 20) -> List:
        """Search notes by query"""
        notes = await get_user_notes(user_id, limit=1000)
        query_lower = query.lower()
        return [note for note in notes if query_lower in note.text.lower()][:limit]

