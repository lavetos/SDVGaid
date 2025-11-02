# AI Integration Setup

This bot now supports **AI-powered natural language understanding** using OpenAI or Claude.

## Features

- 🧠 **Natural Language Understanding** - Chat with the bot in plain Russian
- 🔧 **Function Calling** - Bot extracts intents and calls functions automatically
- 💬 **Smart Responses** - Context-aware, empathetic responses
- 📝 **Task Breakdown** - AI helps break tasks into micro-steps
- 💭 **Reframing** - Converts self-criticism into support
- 📅 **Smart Reminders** - Understands natural time expressions
- 🔍 **Note Search** - Find notes semantically (coming soon)

## Quick Start

### Option 1: OpenAI

1. Get your API key from [platform.openai.com](https://platform.openai.com/api-keys)

2. Add to `.env`:
```bash
OPENAI_API_KEY=sk-your-key-here
```

3. Restart the bot

### Option 2: Claude (Anthropic)

1. Get your API key from [console.anthropic.com](https://console.anthropic.com/)

2. Add to `.env`:
```bash
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

3. Restart the bot

## Usage Examples

### Natural Language Commands

**Before (only commands):**
```
/goal Отправить отчёт
```

**Now (natural language):**
```
Напомни отправить отчёт завтра в 15:00
```

The bot will:
1. Parse the time ("завтра в 15:00")
2. Extract intent (reminder)
3. Create the reminder
4. Confirm in a friendly way

### Task Breakdown

```
User: Застрял с отчётом, не знаю с чего начать
Bot: Понимаю. Давай микрошагами:
     1) Открой файл отчёта
     2) Напиши 3 bullet-пункта для вводной части
     3) Запусти 25 минут фокуса
     
     Поехали? 🚀
```

### Empathetic Reframing

```
User: Я лентяй, ничего не сделал сегодня
Bot: Ты не лентяй — ты устал 💛
     Даже просто дожить день — уже достижение.
     Предлагаю одно крошечное действие на сейчас
     (5 минут максимум).
```

## How It Works

### Architecture

```
User Message
    ↓
AI Service (OpenAI/Claude)
    ↓
Function Calling
    ├─ parse_time_ru
    ├─ create_reminder
    ├─ add_note
    ├─ start_focus_timer
    └─ break_down_task
    ↓
Execute Actions
    ↓
Friendly Response
```

### Function Tools

The bot has these AI functions:

1. **create_reminder** - Create reminders with natural time parsing
2. **add_note** - Save notes to external brain
3. **start_focus_timer** - Launch Pomodoro
4. **parse_time_ru** - Parse Russian time expressions
5. **break_down_task** - Break tasks into micro-steps
6. **get_energy_level** - Get current energy for context

### System Prompt

The AI uses a carefully crafted system prompt:

- **Tone**: Warm, empathetic friend
- **Style**: Short phrases, emojis, no judgment
- **Principles**: No "should", no shaming, support always
- **Adaptive**: Changes based on energy level

## Cost Optimization

### Recommended Settings

**For OpenAI:**
- Model: `gpt-4o-mini` (cheapest, good quality)
- Max tokens: 500 (keeps responses concise)
- Temperature: 0.7 (balanced creativity/consistency)

**For Claude:**
- Model: `claude-3-haiku-20240307` (cheapest Claude)
- Max tokens: 500

### Cost Management

- **Batch small requests** - Multiple intents per message
- **Cache common responses** - Repeated patterns
- **Local mode for sensitive data** - Process locally when needed
- **Rate limiting** - Optional daily limits per user

## Fallback Behavior

If AI is not configured or errors occur:

- Bot works perfectly with regular commands
- Friendly message explains AI is optional
- No functionality loss

## Privacy & Safety

- ✅ **Opt-in**: AI only processes if API key is set
- ✅ **No medical advice**: System prompt explicitly forbids it
- ✅ **Data control**: Choose what goes to AI
- ✅ **Local first**: Important data stays local
- ✅ **Transparent**: Users know when AI is used

## Troubleshooting

### "No AI provider configured"

**Solution**: Add API key to `.env` file

### Import errors for openai/anthropic

**Solution**: Install dependencies:
```bash
pip install openai anthropic
```

### High costs

**Solution**: 
1. Use cheaper models (gpt-4o-mini, claude-haiku)
2. Reduce max_tokens
3. Add rate limiting
4. Use local mode for some features

### AI responses not empathetic

**Solution**: Check system prompt in `prompts.py` - may need tuning

## Advanced: Customization

### Adjust System Prompt

Edit `prompts.py` → `SYSTEM_PROMPT` to change AI personality

### Add New Functions

1. Define in `ai_functions.py` → `FUNCTION_TOOLS`
2. Implement handler in `ai_functions.py` → `FunctionHandler`
3. AI will auto-detect and use it

### Energy-Based Adaptation

AI responses adapt to user's energy level:
- Low (<40%): One microstep, no pressure
- Medium (60%): Regular support
- High (>80%): Multiple tasks OK

## Next Steps

- [ ] Voice input with Whisper
- [ ] Smart note search with embeddings
- [ ] Personalized daily routine suggestions
- [ ] Mood tracking and patterns
- [ ] Habit streaks with gentle nudges

