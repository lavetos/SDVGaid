"""Register all handlers with dispatcher"""
from bot import dp, BotStates


def register_all_handlers():
    """Register all handlers"""
    # Import handlers (will register themselves via decorators)
    from handlers import goal_handlers, plan_handlers, note_handlers, reminder_handlers, evening_handlers
    
    # Register handlers that need dp injection
    goal_handlers.register_handlers(dp, BotStates)
    plan_handlers.register_handlers(dp, BotStates)
    note_handlers.register_handlers(dp, BotStates)
    reminder_handlers.register_handlers(dp, BotStates)
    evening_handlers.register_handlers(dp, BotStates)

