import asyncio
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from google import genai

# ==========================================
# БЕЗОПАСНЫЕ НАСТРОЙКИ (Ключи берутся из системы)
# ==========================================
BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_KEY")

if not BOT_TOKEN or not GEMINI_KEY:
    exit("Ошибка: Переменные окружения BOT_TOKEN или GEMINI_KEY не заданы!")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
ai_client = genai.Client(api_key=GEMINI_KEY)

@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer("📊 <b>Привет!</b> Я твой персональный ИИ-бизнес-консультант. Напиши мне свою бизнес-идею, и я разложу её по полочкам.", parse_mode="HTML")

@dp.message(F.text)
async def analyze_business_idea(message: Message):
    status_message = await message.answer("🔄 Экономический анализ запущен, собираю данные...")

    system_prompt = (
        "Ты — топовый международный бизнес-консультант и венчурный аналитик. "
        "Проведи глубокий, но лаконичный экспресс-анализ бизнес-идеи пользователя для его портфолио.\n"
        "Используй профессиональную терминологию (LTV, CAC, юнит-экономика, MVP, барьеры входа), где это уместно.\n"
        "ВАЖНО: Выделяй ключевые экономические понятия и заголовки с помощью HTML-тегов жирности: <b>текст</b>. Не используй звездочки!\n\n"
        "Ответь строго по следующим блокам, разделяя их пустой строкой:\n"
        "🚀 <b>ПОТЕНЦИАЛ И МОДЕЛЬ МОНЕТИЗАЦИИ:</b>\n"
        "⚠️ <b>КЛЮЧЕВЫЕ РИСКИ И БАРЬЕРЫ:</b>\n"
        "🎯 <b>ЦЕЛЕВАЯ АУДИТОРИЯ (ЦА):</b>\n"
        "🏁 <b>СТРАТЕГИЯ ЗАПУСКА (MVP):</b>\n\n"
        "Пиши емко, тезисно, общая длина ответа должна быть до 2000 символов."
    )

    try:
        # Запрос к нейросети Gemini
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=f"{system_prompt}\n\nИдея пользователя: {message.text}"
        )
        
        # Отправляем ответ в Telegram
        await message.answer(response.text, parse_mode="HTML")
        
        # Удаляем плашку загрузки
        try:
            await status_message.delete()
        except:
            pass

    except Exception as e:
        await message.answer(f"❌ Ошибка при анализе: {str(e)}")

async def main():
    print("Бот-Экономист успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())