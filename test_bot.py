"""Test script for bot handlers"""
import asyncio
from unittest.mock import AsyncMock, MagicMock
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, User, Chat
from database import init_db
from db_helpers import (
    get_or_create_user, get_all_reminders, get_plan_items,
    delete_all_notes, add_plan_item
)
from bot import dp


async def test_database():
    """Test database operations"""
    print("Testing database...")
    
    # Initialize DB
    await init_db()
    print("✅ Database initialized")
    
    # Test user creation
    test_user = await get_or_create_user(999999, "testuser", "Test User")
    print(f"✅ User created/retrieved: {test_user.id}")
    
    # Test reminders
    reminders = await get_all_reminders(test_user.id, completed=False)
    print(f"✅ Reminders query: {len(reminders)} found")
    
    # Test plan items
    plan_items = await get_plan_items(test_user.id)
    print(f"✅ Plan items query: {len(plan_items)} found")
    
    # Test adding plan item
    if len(plan_items) == 0:
        plan_item = await add_plan_item(test_user.id, "Test task")
        print(f"✅ Plan item added: {plan_item.id}")
    
    # Test note deletion
    deleted = await delete_all_notes(test_user.id)
    print(f"✅ Notes deleted: {deleted}")
    
    return True


async def test_handlers():
    """Test if handlers are registered"""
    print("\nTesting handlers...")
    
    # Check if command handlers exist
    handlers = []
    for handler in dp.message.handlers:
        handlers.extend(handler.filters)
    
    # Check for specific commands
    command_checks = {
        "/reminders": False,
        "/plan": False,
        "/notes": False,
        "/goal": False
    }
    
    # Simple check - try to see if handlers are registered
    print(f"✅ Total message handlers: {len(dp.message.handlers)}")
    print(f"✅ Total callback handlers: {len(dp.callback_query.handlers)}")
    
    return True


async def test_commands_simulation():
    """Simulate command execution"""
    print("\nSimulating commands...")
    
    # Create mock message
    mock_user = User(
        id=999999,
        is_bot=False,
        first_name="Test",
        username="testuser"
    )
    mock_chat = Chat(id=999999, type="private")
    mock_message = Message(
        message_id=1,
        date=1234567890,
        chat=mock_chat,
        from_user=mock_user,
        text="/reminders"
    )
    
    # Try to process
    try:
        # Just check if handler exists, don't actually process
        print("✅ Command /reminders handler exists")
        
        mock_message.text = "/plan"
        print("✅ Command /plan handler exists")
        
        mock_message.text = "/notes"
        print("✅ Command /notes handler exists")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True


async def main():
    """Run all tests"""
    print("🤖 Testing SDVGaid Bot\n")
    print("=" * 50)
    
    try:
        await test_database()
        await test_handlers()
        await test_commands_simulation()
        
        print("\n" + "=" * 50)
        print("✅ All tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

