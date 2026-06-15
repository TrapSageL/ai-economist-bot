import asyncio
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart
from google import genai
from aiohttp import web

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_KEY")

if not BOT_TOKEN or not GEMINI_KEY:
    exit("Ошибка: Настрой переменные окружения!")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
ai_client = genai.Client(api_key=GEMINI_KEY)

# ==========================================
# ИНТЕРФЕЙС
# ==========================================
@dp.message(CommandStart())
async def cmd_start(message: Message):
    kb = [
        [KeyboardButton(text="⚡️ Предложи актуальную бизнес-идею")],
        [KeyboardButton(text="🤖 ИИ-сервис для бизнеса"), KeyboardButton(text="📱 Локальный стартап")]
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    
    welcome_text = (
        "💼 Система ИИ-анализа стартапов активна\n"
        "─────────────────────────\n\n"
        "Привет! Напиши свою бизнес-идею, и я устрою ей жёсткий краш-тест.\n\n"
        "👉 Или просто нажми на кнопку ниже, и я сам предложу тебе готовый кейс."
    )
    await message.answer(welcome_text, reply_markup=keyboard)

# ==========================================
# УМНАЯ ФИЛЬТРАЦИЯ ЗАПРОСОВ
# ==========================================
@dp.message(F.text)
async def analyze_business_idea(message: Message):
    # Если пользователь нажал кнопку генерации идеи
    if "Предложи" in message.text:
        status = await message.answer("🚀 Генерирую трендовый стартап на 2026 год...")
        
        system_prompt = (
            "Ты — успешный венчурный инвестор. Придумай ОДНУ конкретную, свежую и очень прибыльную бизнес-идею "
            "на 2026 год для молодежи или студентов, которую можно запустить с минимальным бюджетом.\n"
            "Пиши на чистом русском языке, очень кратко и тезисно (до 100 слов).\n\n"
            "СТРОГОЕ ПРАВИЛО: Не используй звездочки (*) и HTML. Формат ответа строго такой:\n\n"
            "💎 ГОТОВЫЙ КЕЙС ДЛЯ ЗАПУСКА\n"
            "───────────────────\n"
            "СУТЬ: [Что за бизнес и в чем фишка]\n"
            "ПЛЮСЫ: [Почему это выстрелит прямо сейчас]\n"
            "СТАРТ: [Простой первый шаг за 48 часов без вложений]"
        )
        user_input = "Сгенерируй новую идею."
        
    # Если пользователь ввёл СВОЮ идею для анализа
    else:
        status = await message.answer("🔄 Экспресс-анализ концепта...")
        
        system_prompt = (
            "Ты — строгий, прямолинейный инвестиционный аналитик. Твоя задача — сделать быстрый, жесткий "
            "краш-тест идеи пользователя без воды и сленга. Пиши кратко (до 100 слов), без звездочек (*) и HTML.\n\n"
            "Если идея откровенно слабая, детская или нерентабельная, ответь строго по этой структуре:\n"
            "🔴 СТАТУС: УТОПИЯ\n"
            "───────────────────\n"
            "КРИТИКА: [Почему прогорит и где потеряются деньги]\n"
            "АЛЬТЕРНАТИВА: [Как изменить вектор, чтобы получить прибыль]\n\n"
            "Если идея реально жизнеспособная и крутая, ответь строго по этой структуре:\n"
            "🟢 СТАТУС: ПЕРСПЕКТИВНО\n"
            "───────────────────\n"
            "ПОТЕНЦИАЛ: [В чем главная ценность идеи]\n"
            "МОНЕТИЗАЦИЯ: [Как и на ком делать деньги]\n"
            "ПЕРВЫЙ ШАГ: [Что сделать для создания MVP]"
        )
        user_input = f"Оцени идею: {message.text}"
    
    try:
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=f"{system_prompt}\n\n{user_input}"
        )
        
        final_text = response.text.replace("**", "").replace("*", "").strip()
        final_text += "\n─────────────────────────\n🎯 Жду следующую идею или нажатие кнопки."
        
        await message.answer(final_text)
        await status.delete()
        
    except Exception as e:
        await message.answer("❌ Ошибка связи с ИИ. Попробуй еще раз.")
        await status.delete()

# ==========================================
# СЕРВЕР RENDER
# ==========================================
async def handle_index(request): return web.Response(text="Active")
async def main():
    app = web.Application()
    app.router.add_get('/', handle_index)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', int(os.getenv("PORT", 8000))).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())