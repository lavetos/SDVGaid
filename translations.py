"""Translation system for the bot - supports English, Spanish, Russian, Ukrainian"""

# Translation dictionary: key -> {lang_code: translation}
TRANSLATIONS = {
    # Greetings
    "greeting_simple": {
        "en": "Hi! ☀️\n\nI'm your helper for a soft and structured day.\n\nI won't tell you 'must' or 'should'.\nWe'll just go through the day together — as it goes 💛\n\nWhat would you like to do?",
        "es": "¡Hola! ☀️\n\nSoy tu ayudante para un día suave y estructurado.\n\nNo te diré 'debes' o 'tienes que'.\nSimplemente pasaremos el día juntos — como salga 💛\n\n¿Qué te gustaría hacer?",
        "ru": "Привет! ☀️\n\nЯ твой помощник для мягкого и структурированного дня.\n\nЯ не буду говорить тебе 'надо' или 'ты должен'.\nМы просто вместе пройдём по дню — как получится 💛\n\nЧем могу помочь?",
        "uk": "Привіт! ☀️\n\nЯ твій помічник для м'якого та структурованого дня.\n\nЯ не буду казати тобі 'треба' або 'ти повинен'.\nМи просто разом пройдемо по дню — як вийде 💛\n\nЧим можу допомогти?",
    },
    "greeting": {
        "en": "Hi! ☀️\n\nI'm your helper for a soft and structured day.\n\nI won't tell you 'must' or 'should'.\nWe'll just go through the day together — as it goes 💛\n\nHow are you? What's your energy level?",
        "es": "¡Hola! ☀️\n\nSoy tu ayudante para un día suave y estructurado.\n\nNo te diré 'debes' o 'tienes que'.\nSimplemente pasaremos el día juntos — como salga 💛\n\n¿Cómo estás? ¿Cuál es tu nivel de energía?",
        "ru": "Привет! ☀️\n\nЯ твой помощник для мягкого и структурированного дня.\n\nЯ не буду говорить тебе 'надо' или 'ты должен'.\nМы просто вместе пройдём по дню — как получится 💛\n\nКак дела? На сколько процентов ты заряжен?",
        "uk": "Привіт! ☀️\n\nЯ твій помічник для м'якого та структурованого дня.\n\nЯ не буду казати тобі 'треба' або 'ти повинен'.\nМи просто разом пройдемо по дню — як вийде 💛\n\nЯк справи? На скільки відсотків ти заряджений?",
    },
    
    # Energy
    "energy_question": {
        "en": "How are you feeling today? What's your energy level? 🔋\n\n(This helps me suggest the right tasks for you)",
        "es": "¿Cómo te sientes hoy? ¿Cuál es tu nivel de energía? 🔋\n\n(Esto me ayuda a sugerirte las tareas adecuadas)",
        "ru": "Как ты себя чувствуешь сегодня? Какая энергия? 🔋\n\n(Это поможет мне предложить подходящие задачи)",
        "uk": "Як ти себе почуваєш сьогодні? Яка енергія? 🔋\n\n(Це допоможе мені запропонувати підходящі задачі)",
    },
    "energy_saved": {
        "en": "✅ Energy level saved: {level}%",
        "es": "✅ Nivel de energía guardado: {level}%",
        "ru": "✅ Энергия сохранена: {level}%",
        "uk": "✅ Енергія збережена: {level}%",
    },
    "energy_select_above": {
        "en": "Please select one of the options above! 👆",
        "es": "¡Por favor selecciona una de las opciones arriba! 👆",
        "ru": "Выбери один из вариантов выше! 👆",
        "uk": "Виберіть один з варіантів вище! 👆",
    },
    "energy_low_advice": {
        "en": "💙 Low energy day — that's okay!\n\nLet's keep it simple:\n• One tiny task (5 minutes max)\n• Rest is totally fine\n• No pressure, no guilt",
        "es": "💙 Día de baja energía — ¡está bien!\n\nMantengámoslo simple:\n• Una tarea pequeña (5 minutos máximo)\n• Descansar está totalmente bien\n• Sin presión, sin culpa",
        "ru": "💙 Низкая энергия — это нормально!\n\nДавай упростим:\n• Одна маленькая задача (5 минут максимум)\n• Отдых — это нормально\n• Никакого давления, никакой вины",
        "uk": "💙 Низька енергія — це нормально!\n\nСпростимо:\n• Одна маленька задача (максимум 5 хвилин)\n• Відпочинок — це нормально\n• Жодного тиску, жодної провини",
    },
    "energy_medium_advice": {
        "en": "⚡ Medium energy — good for one main thing ✨\n\nFocus on one goal today, everything else is bonus.",
        "es": "⚡ Energía media — buena para una cosa principal ✨\n\nEnfócate en un objetivo hoy, todo lo demás es bonus.",
        "ru": "⚡ Средняя энергия — подходит для одного главного дела ✨\n\nСфокусируйся на одной цели сегодня, остальное — бонус.",
        "uk": "⚡ Середня енергія — підходить для однієї головної справи ✨\n\nЗосередься на одній меті сьогодні, решта — бонус.",
    },
    "energy_high_advice": {
        "en": "💪 High energy — great! 🌟\n\nYou can take on a few tasks today, but don't overdo it. One main goal + 2-3 small tasks is perfect.",
        "es": "💪 Alta energía — ¡genial! 🌟\n\nPuedes hacer algunas tareas hoy, pero no te excedas. Un objetivo principal + 2-3 tareas pequeñas es perfecto.",
        "ru": "💪 Высокая энергия — отлично! 🌟\n\nМожешь взять несколько задач сегодня, но не переусердствуй. Одна главная цель + 2-3 маленькие задачи — идеально.",
        "uk": "💪 Висока енергія — чудово! 🌟\n\nМожеш взяти кілька задач сьогодні, але не перестарайся. Одна головна мета + 2-3 маленькі задачі — ідеально.",
    },
    
    # Goals with energy adaptation
    "goal_question_low_energy": {
        "en": "What's one tiny thing you could do today? (5 minutes max) 🎯",
        "es": "¿Qué cosa pequeña podrías hacer hoy? (5 minutos máximo) 🎯",
        "ru": "Какое одно маленькое дело можно сделать сегодня? (5 минут максимум) 🎯",
        "uk": "Яку одну маленьку справу можна зробити сьогодні? (максимум 5 хвилин) 🎯",
    },
    "goal_question_high_energy": {
        "en": "What's your main goal today? (You have energy for a few tasks!) 🎯",
        "es": "¿Cuál es tu objetivo principal hoy? (¡Tienes energía para algunas tareas!) 🎯",
        "ru": "Какая твоя главная цель сегодня? (У тебя есть энергия на несколько задач!) 🎯",
        "uk": "Яка твоя головна мета сьогодні? (У тебе є енергія на кілька задач!) 🎯",
    },
    "goal_hint": {
        "en": "One thing — that's enough. You can write or send voice 🎤",
        "es": "Una cosa — es suficiente. Puedes escribir o enviar voz 🎤",
        "ru": "Одно дело — и всё хорошо. Можешь написать или отправить голосовое 🎤",
        "uk": "Одна справа — і все добре. Можеш написати або надіслати голосове 🎤",
    },
    "goal_change_question": {
        "en": "Want to change the goal?",
        "es": "¿Quieres cambiar el objetivo?",
        "ru": "Хочешь поменять цель?",
        "uk": "Хочеш змінити мету?",
    },
    
    # Plans with energy adaptation
    "plan_title": {
        "en": "📋 Daily plan",
        "es": "📋 Plan diario",
        "ru": "📋 План на день",
        "uk": "📋 План на день",
    },
    "plan_completed": {
        "en": "Completed",
        "es": "Completadas",
        "ru": "Выполнено",
        "uk": "Виконано",
    },
    "plan_all_done": {
        "en": "🎉 Everything done! You're awesome!\n\n",
        "es": "🎉 ¡Todo hecho! ¡Eres increíble!\n\n",
        "ru": "🎉 Всё сделано! Ты молодец!\n\n",
        "uk": "🎉 Все зроблено! Ти молодець!\n\n",
    },
    "plan_half_done": {
        "en": "💪 Great! More than half done!\n\n",
        "es": "💪 ¡Genial! ¡Más de la mitad hecho!\n\n",
        "ru": "💪 Отлично! Уже больше половины!\n\n",
        "uk": "💪 Чудово! Вже більше половини!\n\n",
    },
    "plan_some_done": {
        "en": "✨ Already {count} task{'s' if count > 1 else ''} done!\n\n",
        "es": "✨ ¡Ya {count} tarea{'s' if count > 1 else ''} hecha{'s' if count > 1 else ''}!\n\n",
        "ru": "✨ Уже {count} задача{'и' if count > 1 else ''} выполнена!\n\n",
        "uk": "✨ Вже {count} задача{'и' if count > 1 else ''} виконана!\n\n",
    },
    "plan_empty_low_energy": {
        "en": "📋 Plan is empty\n\n💙 With low energy, let's keep it simple:\n• One tiny task (5 min max)\n• Or just rest — that's fine!\n\nPress '➕ Add item' to add",
        "es": "📋 El plan está vacío\n\n💙 Con baja energía, mantengámoslo simple:\n• Una tarea pequeña (5 min máximo)\n• O solo descansa — ¡está bien!\n\nPresiona '➕ Agregar elemento' para agregar",
        "ru": "📋 План пуст\n\n💙 С низкой энергией упростим:\n• Одна маленькая задача (5 мин максимум)\n• Или просто отдохни — это нормально!\n\nНажми '➕ Добавить пункт'",
        "uk": "📋 План порожній\n\n💙 З низькою енергією спростимо:\n• Одна маленька задача (максимум 5 хв)\n• Або просто відпочини — це нормально!\n\nНатисни '➕ Додати пункт'",
    },
    "plan_empty_high_energy": {
        "en": "📋 Plan is empty\n\n💪 With high energy, you can add a few tasks!\n• One main task\n• 2-3 small tasks\n• Don't overdo it though\n\nPress '➕ Add item' to add",
        "es": "📋 El plan está vacío\n\n💪 Con alta energía, puedes agregar algunas tareas!\n• Una tarea principal\n• 2-3 tareas pequeñas\n• Pero no te excedas\n\nPresiona '➕ Agregar elemento' para agregar",
        "ru": "📋 План пуст\n\n💪 С высокой энергией можешь добавить несколько задач!\n• Одна главная задача\n• 2-3 маленькие задачи\n• Но не переусердствуй\n\nНажми '➕ Добавить пункт'",
        "uk": "📋 План порожній\n\n💪 З високою енергією можеш додати кілька задач!\n• Одна головна задача\n• 2-3 маленькі задачі\n• Але не перестарайся\n\nНатисни '➕ Додати пункт'",
    },
    "plan_energy_note_low": {
        "en": "💙 With low energy, maybe start with just 1-2 easiest tasks?",
        "es": "💙 Con baja energía, ¿quizás empieces con solo 1-2 tareas más fáciles?",
        "ru": "💙 С низкой энергией, может, начнёшь с 1-2 самых простых задач?",
        "uk": "💙 З низькою енергією, можливо, почнеш з 1-2 найпростіших задач?",
    },
    "plan_energy_note_high": {
        "en": "💪 With high energy, you could add a few more tasks if you want!",
        "es": "💪 Con alta energía, ¡podrías agregar algunas tareas más si quieres!",
        "ru": "💪 С высокой энергией можешь добавить ещё пару задач, если хочешь!",
        "uk": "💪 З високою енергією можеш додати ще пару задач, якщо хочеш!",
    },
    "continue_working": {
        "en": "Continue working with me!",
        "es": "¡Continúa trabajando conmigo!",
        "ru": "Продолжай работать со мной!",
        "uk": "Продовжуй працювати зі мною!",
    },
    
    # Energy levels
    "energy_less_40": {
        "en": "🔋 Less than 40%",
        "es": "🔋 Menos de 40%",
        "ru": "🔋 Меньше 40%",
        "uk": "🔋 Менше 40%",
    },
    "energy_around_60": {
        "en": "⚡ Around 60%",
        "es": "⚡ Alrededor de 60%",
        "ru": "⚡ Около 60%",
        "uk": "⚡ Близько 60%",
    },
    "energy_more_80": {
        "en": "💪 More than 80%",
        "es": "💪 Más de 80%",
        "ru": "💪 Больше 80%",
        "uk": "💪 Більше 80%",
    },
    
    # Goal related
    "goal_question": {
        "en": "What's the main thing for today? 🎯",
        "es": "¿Cuál es la cosa principal de hoy? 🎯",
        "ru": "Так, какое главное дело на сегодня? 🎯",
        "uk": "Так, яка головна справа на сьогодні? 🎯",
    },
    "goal_saved": {
        "en": "✅ Goal saved!\n\n{goal}\n\nI'll remind you in the evening 🤝",
        "es": "✅ ¡Objetivo guardado!\n\n{goal}\n\nTe recordaré por la tarde 🤝",
        "ru": "✅ Готово! Записал:\n\n{goal}\n\nЯ вечером напомню и спрошу, как прошло 🤝",
        "uk": "✅ Готово! Записав:\n\n{goal}\n\nЯ вечором нагадаю і спитаю, як пройшло 🤝",
    },
    
    # Evening check-in
    "evening_question": {
        "en": "How was your day? 🌙\n\nWhat did you manage to do?\n\n(Or press ❌ Cancel)",
        "es": "¿Cómo fue tu día? 🌙\n\n¿Qué lograste hacer?\n\n(O presiona ❌ Cancelar)",
        "ru": "Итак, как прошёл день? 🌙\n\nЧто получилось сделать?\n\n(Или нажми ❌ Отмена)",
        "uk": "Отже, як пройшов день? 🌙\n\nЩо вдалося зробити?\n\n(Або натисни ❌ Скасувати)",
    },
    "evening_thanks": {
        "en": "💫 Thanks for the check-in!\n\nHow would you rate this day? (1-10)\n\nJust write a number, for example: 7",
        "es": "💫 ¡Gracias por el chequeo!\n\n¿Cómo calificarías este día? (1-10)\n\nSolo escribe un número, por ejemplo: 7",
        "ru": "💫 Спасибо за чек-ин!\n\nКак оценишь этот день? (от 1 до 10)\n\nПросто напиши число, например: 7",
        "uk": "💫 Дякую за чек-ін!\n\nЯк оціниш цей день? (від 1 до 10)\n\nПросто напиши число, наприклад: 7",
    },
    
    # Common buttons
    "cancel": {
        "en": "❌ Cancel",
        "es": "❌ Cancelar",
        "ru": "❌ Отмена",
        "uk": "❌ Скасувати",
    },
    "skip": {
        "en": "Skip",
        "es": "Omitir",
        "ru": "Пропустить",
        "uk": "Пропустити",
    },
    
    # Error messages
    "error_generic": {
        "en": "Oops, something went wrong 😅 Try again or use regular commands!",
        "es": "Ups, algo salió mal 😅 ¡Intenta de nuevo o usa comandos regulares!",
        "ru": "Упс, что-то пошло не так 😅 Попробуй ещё раз или используй обычные команды!",
        "uk": "Упс, щось пішло не так 😅 Спробуй ще раз або використовуй звичайні команди!",
    },
    
    # Plans
    "plan_empty": {
        "en": "Plan is empty 📋\n\n✨ Start with a simple task:\n• Press '➕ Add item'\n• Or write: 'add to plan cleaning'",
        "es": "El plan está vacío 📋\n\n✨ Comienza con una tarea simple:\n• Presiona '➕ Agregar elemento'\n• O escribe: 'agregar al plan limpieza'",
        "ru": "План пуст 📋\n\n✨ Начни с простой задачи:\n• Нажми '➕ Добавить пункт'\n• Или напиши: 'добавь в план уборка'",
        "uk": "План порожній 📋\n\n✨ Почни з простої задачі:\n• Натисни '➕ Додати пункт'\n• Або напиши: 'додай до плану прибирання'",
    },
    
    # Reminders
    "reminder_created": {
        "en": "✅ Reminder created!\n\n💬 {text}\n⏰ {time} ({time_until})\n\nI'll remind you in your timezone! 🇪🇸",
        "es": "✅ ¡Recordatorio creado!\n\n💬 {text}\n⏰ {time} ({time_until})\n\n¡Te recordaré en tu zona horaria! 🇪🇸",
        "ru": "✅ Напоминание создано!\n\n💬 {text}\n⏰ {time} ({time_until})\n\nЯ напомню в твоей таймзоне! 🇪🇸",
        "uk": "✅ Нагадування створено!\n\n💬 {text}\n⏰ {time} ({time_until})\n\nЯ нагадаю в твоїй часовій зоні! 🇪🇸",
    },
    "reminder_sent": {
        "en": "🔔 Reminder ({time}):\n\n{text}\n\n💛 Don't rush, everything is fine",
        "es": "🔔 Recordatorio ({time}):\n\n{text}\n\n💛 No te apresures, todo está bien",
        "ru": "🔔 Напоминаю ({time}):\n\n{text}\n\n💛 Не спеши, всё в порядке",
        "uk": "🔔 Нагадую ({time}):\n\n{text}\n\n💛 Не поспішай, все в порядку",
    },
    
    # History
    "history_empty": {
        "en": "No history yet 📊\n\nStart using the bot, and your days will appear here!",
        "es": "Aún no hay historial 📊\n\n¡Comienza a usar el bot y tus días aparecerán aquí!",
        "ru": "Истории пока нет 📊\n\nНачни использовать бота, и твои дни появятся здесь!",
        "uk": "Історії поки що немає 📊\n\nПочни використовувати бота, і твої дні з'являться тут!",
    },
    "history_title": {
        "en": "📊 Days history (last 30)",
        "es": "📊 Historial de días (últimos 30)",
        "ru": "📊 История дней (последние 30)",
        "uk": "📊 Історія днів (останні 30)",
    },
    "history_more": {
        "en": "\n... and {count} more days",
        "es": "\n... y {count} días más",
        "ru": "\n... и ещё {count} дней",
        "uk": "\n... і ще {count} днів",
    },
    "history_hint": {
        "en": "💡 Write 'details 01.11' for day details\nOr write 'long' for full format",
        "es": "💡 Escribe 'detalles 01.11' para detalles del día\nO escribe 'largo' para formato completo",
        "ru": "💡 Напиши 'детали 01.11' для подробностей о дне\nИли напиши 'длинно' для полного формата",
        "uk": "💡 Напиши 'деталі 01.11' для деталей дня\nАбо напиши 'довго' для повного формату",
    },
    "already_rated": {
        "en": "You already rated today: {rating}/10 ⭐\n\nWant to change? Just write a new number (1-10).",
        "es": "Ya calificaste hoy: {rating}/10 ⭐\n\n¿Quieres cambiar? Solo escribe un nuevo número (1-10).",
        "ru": "Ты уже оценил сегодняшний день: {rating}/10 ⭐\n\nХочешь изменить оценку? Просто напиши новое число (1-10).",
        "uk": "Ти вже оцінив сьогоднішній день: {rating}/10 ⭐\n\nХочеш змінити? Просто напиши нове число (1-10).",
    },
    
    # Rating
    "rating_question": {
        "en": "How would you rate today? (1-10)\n\nJust write a number, for example: 7",
        "es": "¿Cómo calificarías hoy? (1-10)\n\nSolo escribe un número, por ejemplo: 7",
        "ru": "Как оценишь сегодняшний день? (от 1 до 10)\n\nПросто напиши число, например: 7",
        "uk": "Як оціниш сьогоднішній день? (від 1 до 10)\n\nПросто напиши число, наприклад: 7",
    },
    
    # Good night
    "good_night": {
        "en": "Good night! 🌙",
        "es": "¡Buenas noches! 🌙",
        "ru": "Спокойной ночи! 🌙",
        "uk": "Доброї ночі! 🌙",
    },
    
    # Time until
    "in_seconds": {
        "en": "in {seconds} seconds",
        "es": "en {seconds} segundos",
        "ru": "через {seconds} секунд",
        "uk": "через {seconds} секунд",
    },
    "in_minutes": {
        "en": "in {minutes} minutes",
        "es": "en {minutes} minutos",
        "ru": "через {minutes} минут",
        "uk": "через {minutes} хвилин",
    },
    "in_hours": {
        "en": "in {hours} hours",
        "es": "en {hours} horas",
        "ru": "через {hours} часов",
        "uk": "через {hours} годин",
    },
    "in_hours_minutes": {
        "en": "in {hours} h {minutes} min",
        "es": "en {hours} h {minutes} min",
        "ru": "через {hours} ч {minutes} мин",
        "uk": "через {hours} год {minutes} хв",
    },
}


def get_language_code(telegram_lang_code: str = None) -> str:
    """
    Get language code from Telegram settings.
    Supports: en, es, ru, uk
    Defaults to English if not supported.
    
    Args:
        telegram_lang_code: Language code from Telegram (e.g., 'en', 'en-US', 'ru', 'es-ES')
    
    Returns:
        Language code: 'en', 'es', 'ru', or 'uk'
    """
    if not telegram_lang_code:
        return 'en'
    
    # Normalize language code (e.g., 'en-US' -> 'en', 'es-ES' -> 'es')
    lang = telegram_lang_code.lower().split('-')[0]
    
    # Map supported languages
    supported = {
        'en': 'en',
        'es': 'es',
        'ru': 'ru',
        'uk': 'uk',
        'ua': 'uk',  # Alternative code for Ukrainian
    }
    
    return supported.get(lang, 'en')  # Default to English if not supported


def translate(key: str, lang_code: str = 'en', **kwargs) -> str:
    """
    Get translation for a key.
    
    Args:
        key: Translation key
        lang_code: Language code ('en', 'es', 'ru', 'uk')
        **kwargs: Format arguments for the translation
    
    Returns:
        Translated string
    """
    lang_code = get_language_code(lang_code)
    
    translations = TRANSLATIONS.get(key, {})
    text = translations.get(lang_code, translations.get('en', key))
    
    # Format if kwargs provided
    if kwargs:
        try:
            text = text.format(**kwargs)
        except KeyError:
            # If formatting fails, return text as is
            pass
    
    return text


def get_user_language(telegram_user) -> str:
    """
    Get user's language from Telegram user object.
    
    Args:
        telegram_user: Telegram user object (from message.from_user)
    
    Returns:
        Language code: 'en', 'es', 'ru', or 'uk'
    """
    lang_code = getattr(telegram_user, 'language_code', None)
    return get_language_code(lang_code)


# Additional translations for refactored handlers
TRANSLATIONS.update({
    "goal_understood": {
        "en": "Got it! 🎯\n\n{goal}",
        "es": "¡Entendido! 🎯\n\n{goal}",
        "ru": "Понял! 🎯\n\n{goal}",
        "uk": "Зрозумів! 🎯\n\n{goal}",
    },
    "pomodoros_question": {
        "en": "How many pomodoros (25 minutes) will you need? 🍅",
        "es": "¿Cuántos pomodoros (25 minutos) necesitarás? 🍅",
        "ru": "Сколько помидоров (25 минут) понадобится? 🍅",
        "uk": "Скільки помідорів (25 хвилин) знадобиться? 🍅",
    },
    "pomodoros_can_skip": {
        "en": "You can write a number or 'skip'",
        "es": "Puedes escribir un número o 'omitir'",
        "ru": "Можешь написать число или 'пропустить'",
        "uk": "Можеш написати число або 'пропустити'",
    },
    "pomodoros_invalid_range": {
        "en": "Pomodoros should be between 1 and 50 😊\n\nTry again or write 'skip'",
        "es": "Los pomodoros deben estar entre 1 y 50 😊\n\nIntenta de nuevo o escribe 'omitir'",
        "ru": "Помидоры должны быть от 1 до 50 😊\n\nПопробуй ещё раз или напиши 'пропустить'",
        "uk": "Помідори повинні бути від 1 до 50 😊\n\nСпробуй ще раз або напиши 'пропустити'",
    },
    "pomodoros_invalid_format": {
        "en": "Please write a number (1-50) 😊\n\nOr write 'skip'",
        "es": "Por favor escribe un número (1-50) 😊\n\nO escribe 'omitir'",
        "ru": "Пожалуйста, напиши число (1-50) 😊\n\nИли напиши 'пропустить'",
        "uk": "Будь ласка, напиши число (1-50) 😊\n\nАбо напиши 'пропустити'",
    },
    "goal_confirmed": {
        "en": "Great! Let's stay with this goal 💛\n\nGood luck! 💪",
        "es": "¡Genial! Quedémonos con este objetivo 💛\n\n¡Buena suerte! 💪",
        "ru": "Отлично! Остаёмся с этой целью 💛\n\nУдачи! 💪",
        "uk": "Чудово! Залишаємось з цією метою 💛\n\nУдачі! 💪",
    },
    "goal_saved_no_pomodoros": {
        "en": "✅ Goal saved!\n\n{goal}\n\n💡 You can add pomodoro estimate later via /goal",
        "es": "✅ ¡Objetivo guardado!\n\n{goal}\n\n💡 Puedes agregar estimación de pomodoros más tarde con /goal",
        "ru": "✅ Готово! Записал:\n\n{goal}\n\n💡 Можешь позже добавить оценку в помидорах через /goal",
        "uk": "✅ Готово! Записав:\n\n{goal}\n\n💡 Можеш пізніше додати оцінку в помідорах через /goal",
    },
    "pomodoros_saved": {
        "en": "🍅 {count} pomodoros estimated",
        "es": "🍅 {count} pomodoros estimados",
        "ru": "🍅 {count} помидоров оценено",
        "uk": "🍅 {count} помідорів оцінено",
    },
    "plan_item_added": {
        "en": "✅ Added to plan:\n\n{text}",
        "es": "✅ Agregado al plan:\n\n{text}",
        "ru": "✅ Добавлено в план:\n\n{text}",
        "uk": "✅ Додано до плану:\n\n{text}",
    },
    "plan_item_added_large": {
        "en": "✅ Added to plan:\n\n{text}\n\n💡 If task is large, you can write 'break this task' and I'll help divide it into steps",
        "es": "✅ Agregado al plan:\n\n{text}\n\n💡 Si la tarea es grande, puedes escribir 'divide esta tarea' y te ayudaré a dividirla en pasos",
        "ru": "✅ Добавлено в план:\n\n{text}\n\n💡 Если задача большая, можешь написать 'разбей эту задачу' и я помогу разделить на шаги",
        "uk": "✅ Додано до плану:\n\n{text}\n\n💡 Якщо задача велика, можеш написати 'розбий цю задачу' і я допоможу розділити на кроки",
    },
    "plan_add_question": {
        "en": "What to add? 📋",
        "es": "¿Qué agregar? 📋",
        "ru": "Что добавим? 📋",
        "uk": "Що додамо? 📋",
    },
    "plan_add_hint": {
        "en": "Write task or send voice 🎤",
        "es": "Escribe tarea o envía voz 🎤",
        "ru": "Напиши задачу или отправь голосовое 🎤",
        "uk": "Напиши задачу або надішли голосове 🎤",
    },
    "plan_updated": {
        "en": "📋 Plan updated",
        "es": "📋 Plan actualizado",
        "ru": "План обновлен 📋",
        "uk": "План оновлено 📋",
    },
    "plan_delete_confirm": {
        "en": "❓ Delete this task?\n\n{text}",
        "es": "❓ ¿Eliminar esta tarea?\n\n{text}",
        "ru": "❓ Точно удалить задачу?\n\n{text}",
        "uk": "❓ Точно видалити задачу?\n\n{text}",
    },
    "plan_item_deleted": {
        "en": "✅ Task deleted",
        "es": "✅ Tarea eliminada",
        "ru": "✅ Задача удалена",
        "uk": "✅ Задачу видалено",
    },
    "plan_empty_after_delete": {
        "en": "Plan is empty 📋\nWant to add a task?",
        "es": "El plan está vacío 📋\n¿Quieres agregar una tarea?",
        "ru": "План пуст 📋\nХочешь добавить задачу?",
        "uk": "План порожній 📋\nХочеш додати задачу?",
    },
    "updated": {
        "en": "✅ Updated!",
        "es": "✅ ¡Actualizado!",
        "ru": "✅ Обновлено!",
        "uk": "✅ Оновлено!",
    },
    "deleted": {
        "en": "🗑️ Deleted",
        "es": "🗑️ Eliminado",
        "ru": "🗑️ Удалено",
        "uk": "🗑️ Видалено",
    },
    "item_not_found": {
        "en": "Item not found",
        "es": "Elemento no encontrado",
        "ru": "Пункт не найден",
        "uk": "Пункт не знайдено",
    },
    "excellent": {
        "en": "Excellent!",
        "es": "¡Excelente!",
        "ru": "Отлично!",
        "uk": "Чудово!",
    },
    "almost_done": {
        "en": "Almost done!",
        "es": "¡Casi terminado!",
        "ru": "Почти всё!",
        "uk": "Майже все!",
    },
    "good": {
        "en": "Good!",
        "es": "¡Bien!",
        "ru": "Хорошо!",
        "uk": "Добре!",
    },
    
    # Notes
    "note_question": {
        "en": "What to write down? 📝\n\nYou can write or send voice 🎤",
        "es": "¿Qué anotar? 📝\n\nPuedes escribir o enviar voz 🎤",
        "ru": "Что записать? 📝\n\nМожешь написать или отправить голосовое 🎤",
        "uk": "Що записати? 📝\n\nМожеш написати або надіслати голосове 🎤",
    },
    "note_saved": {
        "en": "✅ Saved:\n\n{text}",
        "es": "✅ Guardado:\n\n{text}",
        "ru": "✅ Запомнил:\n\n{text}",
        "uk": "✅ Запам'ятав:\n\n{text}",
    },
    "notes_empty": {
        "en": "No notes yet 📝\n\n✨ Just write: 'save buy milk'\nOr use the '📝 Notes' button\n\n💡 Notes are your external memory. Write anything!",
        "es": "Aún no hay notas 📝\n\n✨ Solo escribe: 'guarda comprar leche'\nO usa el botón '📝 Notas'\n\n💡 Las notas son tu memoria externa. ¡Escribe lo que quieras!",
        "ru": "Заметок пока нет 📝\n\n✨ Просто напиши: 'запиши купить молоко'\nИли используй кнопку '📝 Заметки'\n\n💡 Заметки — это твоя внешняя память. Записывай что угодно!",
        "uk": "Нотаток поки немає 📝\n\n✨ Просто напиши: 'запиши купити молоко'\nАбо використовуй кнопку '📝 Нотатки'\n\n💡 Нотатки — це твоя зовнішня пам'ять. Записуй що завгодно!",
    },
    "notes_list_title": {
        "en": "📝 Your notes (last {recent} of {total}):",
        "es": "📝 Tus notas (últimas {recent} de {total}):",
        "ru": "📝 Твои заметки (последние {recent} из {total}):",
        "uk": "📝 Твої нотатки (останні {recent} з {total}):",
    },
    "notes_more": {
        "en": "... and {count} more notes",
        "es": "... y {count} notas más",
        "ru": "... и ещё {count} заметок",
        "uk": "... і ще {count} нотаток",
    },
    "notes_hint": {
        "en": "💡 Write 'find <word>' to search notes\n🗑 To delete write: 'delete all notes'",
        "es": "💡 Escribe 'buscar <palabra>' para buscar notas\n🗑 Para eliminar escribe: 'eliminar todas las notas'",
        "ru": "💡 Напиши 'найди <слово>' для поиска по заметкам\n🗑 Для удаления напиши: 'удали все заметки'",
        "uk": "💡 Напиши 'знайди <слово>' для пошуку по нотатках\n🗑 Для видалення напиши: 'видали всі нотатки'",
    },
    
    # Reminders
    "reminders_empty": {
        "en": "No reminders yet 📭\n\n✨ You can add a reminder:\n• Press '➕ Add' button below\n• Or just write: 'remind me to call mom tomorrow at 15:00'",
        "es": "Aún no hay recordatorios 📭\n\n✨ Puedes agregar un recordatorio:\n• Presiona el botón '➕ Agregar' abajo\n• O solo escribe: 'recuérdame llamar a mamá mañana a las 15:00'",
        "ru": "Напоминаний пока нет 📭\n\n✨ Можешь добавить напоминание:\n• Нажми кнопку '➕ Добавить' ниже\n• Или просто напиши: 'напомни позвонить маме завтра в 15:00'",
        "uk": "Нагадувань поки немає 📭\n\n✨ Можеш додати нагадування:\n• Натисни кнопку '➕ Додати' нижче\n• Або просто напиши: 'нагадай зателефонувати мамі завтра о 15:00'",
    },
    "reminders_title": {
        "en": "Reminders ({count}) ⏰",
        "es": "Recordatorios ({count}) ⏰",
        "ru": "Напоминания ({count}) ⏰",
        "uk": "Нагадування ({count}) ⏰",
    },
    "reminder_not_found": {
        "en": "Reminder not found",
        "es": "Recordatorio no encontrado",
        "ru": "Напоминание не найдено",
        "uk": "Нагадування не знайдено",
    },
    "reminder_details": {
        "en": "⏰ Reminder\n\n{text}\n\nWhen: {when}",
        "es": "⏰ Recordatorio\n\n{text}\n\nCuándo: {when}",
        "ru": "⏰ Напоминание\n\n{text}\n\nКогда: {when}",
        "uk": "⏰ Нагадування\n\n{text}\n\nКоли: {when}",
    },
    "reminder_completed": {
        "en": "✅ Completed!",
        "es": "✅ ¡Completado!",
        "ru": "✅ Выполнено!",
        "uk": "✅ Виконано!",
    },
    "reminder_completed_msg": {
        "en": "Reminder completed ✅",
        "es": "Recordatorio completado ✅",
        "ru": "Напоминание выполнено ✅",
        "uk": "Нагадування виконано ✅",
    },
    "reminder_delete_confirm": {
        "en": "❓ Really delete this reminder?\n\n{text}",
        "es": "❓ ¿Realmente eliminar este recordatorio?\n\n{text}",
        "ru": "❓ Точно удалить напоминание?\n\n{text}",
        "uk": "❓ Точно видалити нагадування?\n\n{text}",
    },
    "reminders_empty_after_delete": {
        "en": "No reminders 📭\nWant to add one?",
        "es": "No hay recordatorios 📭\n¿Quieres agregar uno?",
        "ru": "Напоминаний нет 📭\nХочешь добавить?",
        "uk": "Нагадувань немає 📭\nХочеш додати?",
    },
    
    # Evening
    "evening_tired_question": {
        "en": "What exhausted you today?",
        "es": "¿Qué te agotó hoy?",
        "ru": "Что вымотало сегодня?",
        "uk": "Що виснажило сьогодні?",
    },
    "evening_helped_question": {
        "en": "And last: what helped a little today? 💛",
        "es": "Y por último: ¿qué ayudó un poco hoy? 💛",
        "ru": "И последнее: что помогло немного сегодня? 💛",
        "uk": "І останнє: що трохи допомогло сьогодні? 💛",
    },
    "goal_reminder": {
        "en": "💬 Remember your goal:\n{text}\n\nWhat about it?",
        "es": "💬 Recuerda tu objetivo:\n{text}\n\n¿Qué tal?",
        "ru": "💬 Помнишь про цель:\n{text}\n\nЧто с ней?",
        "uk": "💬 Пам'ятаєш про мету:\n{text}\n\nЩо з нею?",
    },
    "rating_question_optional": {
        "en": "How would you rate today? (1-10)\n\nJust write a number, for example: 7\n\nOr write 'skip'",
        "es": "¿Cómo calificarías hoy? (1-10)\n\nSolo escribe un número, por ejemplo: 7\n\nO escribe 'omitir'",
        "ru": "Как оценишь сегодняшний день? (от 1 до 10)\n\nПросто напиши число, например: 7\n\nИли напиши 'пропустить'",
        "uk": "Як оціниш сьогоднішній день? (від 1 до 10)\n\nПросто напиши число, наприклад: 7\n\nАбо напиши 'пропустити'",
    },
})

