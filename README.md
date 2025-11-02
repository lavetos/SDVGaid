# SDVGaid - Friendly Telegram Bot for People with ADHD

A warm assistant that helps structure your day without pressure or shame.

## 🎯 Features

- **Morning Dialogue** - Set up your day based on energy level
- **Daily Main Goal** - Focus on one important task
- **Pomodoro Timer** - 25 minutes of focus with breaks
- **External Brain** - Dump notes to free your mind
- **Evening Check-in** - Gentle daily reflection
- **Quiet Mode** - Temporarily disable notifications
- **Energy Diary** - Track energy levels over time

## 🚀 Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create `.env` file:
   ```
   BOT_TOKEN=your_bot_token
   DATABASE_URL=sqlite+aiosqlite:///adhd_bot.db
   ```
4. Run the bot:
   ```bash
   python bot.py
   ```

## 🤖 Commands

- `/start` - Start working with the bot
- `/goal` - Set your main daily goal
- `/focus` - Start Pomodoro timer
- `/note` - Add a note
- `/notes` - View all notes
- `/evening` - Evening check-in
- `/quiet` - Quiet mode for 30 minutes
- `/energy` - Energy statistics for the week

## 💡 Communication Style

Friendly, non-judgmental, with humor and support. The bot doesn't motivate through "should", but gently supports and helps.

## 🤖 AI Features (Optional)

The bot now supports **AI-powered natural language understanding** using OpenAI or Claude:

- Natural Russian language commands
- Smart task breakdown into micro-steps
- Automatic reminder creation from text
- Empathetic reframing of self-criticism
- Context-aware responses based on energy level

**See [AI_SETUP.md](AI_SETUP.md) for detailed setup instructions.**

## 🌐 Cloud Deployment

Run the bot 24/7 in the cloud! See [DEPLOY_FREE.md](DEPLOY_FREE.md) for detailed instructions.

**Quick options:**
- 🚂 **Railway.app** (Recommended) - Easy, free tier, PostgreSQL support
- 🎨 **Render.com** - Simple, free tier (sleeps after inactivity)
- 🪰 **Fly.io** - Free tier available
- 🐍 **PythonAnywhere** - Good for beginners

**🗄️ Persistent Database:** PostgreSQL support included! Data never lost. See [POSTGRESQL_SETUP.md](POSTGRESQL_SETUP.md)

## 📚 Documentation

- [SETUP.md](SETUP.md) - Installation guide
- [DEPLOY.md](DEPLOY.md) - Cloud deployment guide
- [AI_SETUP.md](AI_SETUP.md) - AI configuration
- [HOW_TO_GET_TOKEN.md](HOW_TO_GET_TOKEN.md) - Getting Telegram bot token

