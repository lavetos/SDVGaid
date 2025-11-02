# How to Get Your Telegram Bot Token

## Quick Steps:

1. **Open Telegram** on your phone or desktop

2. **Search for @BotFather**
   - This is the official bot that helps you create bots

3. **Start a chat and send:**
   ```
   /newbot
   ```

4. **Follow the prompts:**
   - BotFather will ask for a name (e.g., "My ADHD Helper")
   - Then ask for a username ending in `bot` (e.g., "my_adhd_helper_bot")

5. **Get your token:**
   - BotFather will give you a token like:
   ```
   1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
   ```

6. **Save the token in `.env` file:**
   ```bash
   # Edit .env and replace the placeholder
   nano .env
   # or
   open .env  # On Mac
   ```
   
   Replace `your_telegram_bot_token_here` with your actual token

7. **Start the bot:**
   ```bash
   source venv/bin/activate
   python bot.py
   ```

## Privacy Note:
- Your bot token is like a password - keep it secret!
- Never commit `.env` file to git (it's already in .gitignore)
- If token leaks, regenerate it with `/revoke` to @BotFather

## Testing Your Bot:
After starting, search for your bot by username in Telegram and send `/start` to begin!

