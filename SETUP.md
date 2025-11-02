# Setup Instructions

## Prerequisites
- Python 3.11+
- Telegram Bot Token from @BotFather

## Installation Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/lavetos/SDVGaid.git
   cd SDVGaid
   ```

2. **Create virtual environment**
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create .env file**
   Create a `.env` file in the project root:
   ```
   BOT_TOKEN=your_telegram_bot_token_here
   DATABASE_URL=sqlite+aiosqlite:///adhd_bot.db
   
   # Optional: AI features (see AI_SETUP.md)
   # OPENAI_API_KEY=your_openai_key
   # ANTHROPIC_API_KEY=your_claude_key
   ```

5. **Run the bot**
   ```bash
   python bot.py
   ```

6. **Find your bot on Telegram**
   Search for your bot using the username provided by BotFather and start chatting with `/start`

## Getting Bot Token

1. Open Telegram and search for @BotFather
2. Send `/newbot` command
3. Follow the instructions to create a bot
4. Copy the token provided
5. Paste it into your `.env` file

## Bot Commands

- `/start` - Start working with the bot
- `/goal` - Set your main daily goal
- `/focus` - Start Pomodoro timer
- `/note` - Add a note
- `/notes` - View all notes
- `/evening` - Evening check-in
- `/quiet` - Quiet mode for 30 minutes
- `/energy` - Energy statistics for the week

## Database

The bot uses SQLite database stored in `adhd_bot.db` file. Database is automatically created on first run.

## Features

- **Morning Dialogue**: Start your day by choosing your energy level
- **Daily Goals**: Set and track your main goal for the day
- **Pomodoro Timer**: Focus for 25 minutes with breaks
- **External Brain**: Dump your thoughts into notes to free your mind
- **Evening Check-in**: Reflect on the day with gentle questions
- **Quiet Mode**: Take a break from notifications
- **Energy Diary**: Track your energy patterns over time
- 🤖 **AI-Powered** (Optional): Natural language understanding, task breakdown, empathetic responses

## AI Features (Optional)

The bot now supports AI-powered features:
- Chat in natural Russian language
- Smart task breakdown into micro-steps
- Automatic reminder creation from text
- Empathetic reframing of self-criticism

**See [AI_SETUP.md](AI_SETUP.md) for detailed AI configuration.**

## Support

This bot is designed with ADHD in mind - no judgment, no pressure, just friendly support. 💛

