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
# ПРЕМИАЛЬНЫЙ ИНТЕРФЕЙС БОТА
# ==========================================
@dp.message(CommandStart())
async def cmd_start(message: Message):
    kb = [
        [KeyboardButton(text="💡 Предложи актуальную бизнес-идею")],
        [KeyboardButton(text="🤖 ИИ-сервис для бизнеса"), KeyboardButton(text="📱 Локальный стартап")]
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    
    welcome_text = (
        "💼 <b>Система экспресс-анализа стартапов «Бизнес-Вайб»</b>\n"
        "─────────────────────────\n\n"
        "Приветствую! Я твой цифровой бизнес-ментор. Моя задача — провести трезвый аудит твоей идеи, рассчитать её жизнеспособность и указать на скрытые риски.\n\n"
        "✍️ <b>Напиши свою задумку</b> коротким текстом или выбери один из готовых векторов анализа с помощью кнопок ниже."
    )
    await message.answer(welcome_text, parse_mode="HTML", reply_markup=keyboard)

# ==========================================
# СТИЛЬНЫЙ И КРАСИВЫЙ АНАЛИЗ (UI/UX ОПТИМИЗАЦИЯ)
# ==========================================
@dp.message(F.text)
async def analyze_business_idea(message: Message):
    status = await message.answer("⚡️ <i>Запуск ИИ-анализа бизнес-модели...</i>", parse_mode="HTML")
    
    system_prompt = (
        "Ты — авторитетный, прямолинейный бизнес-ментор и венчурный инвестор. "
        "Твоя цель — дать честную, профессиональную и очень краткую оценку идее.\n\n"
        "ПРАВИЛО ТОНА: Говори на чистом, грамотном, современном русском языке. "
        "НИКАКОГО фальшивого молодежного сленга. Общайся уважительно, но критично.\n\n"
        "СТРОГИЙ ШАБЛОН ОТВЕТА (Скопируй один в один, заполнив блоки внутри кавычек, не используй звездочки):\n\n"
        "📈 <b>АНАЛИЗ И ПЕРСПЕКТИВА</b>\n"
        "┃ <i>[Твоя экспертная оценка идеи в 2 емких предложениях]</i>\n\n"
        "💰 <b>БИЗНЕС-МОДЕЛЬ</b>\n"
        "┃ <i>[Как именно и на ком этот проект будет зарабатывать]</i>\n\n"
        "⚠️ <b>КРИТИЧЕСКИЕ РИСКИ</b>\n"
        "┃ <i>[Главные причины, почему бизнес может прогореть]</i>\n\n"
        "🚀 <b>БЫСТРЫЙ СТАРТ (MVP)</b>\n"
        "└ <i>[Конкретное простое действие для проверки идеи за 48 часов без бюджета]</i>"
    )
    
    try:
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=f"{system_prompt}\n\nИдея пользователя: {message.text}"
        )
        
        # Очищаем текст от мусорных символов маркдауна, которые ИИ может вернуть случайно
        final_text = response.text.replace("**", "").replace("*", "")
        
        # Добавляем красивую нижнюю плашку под ответом
        final_text += "\n─────────────────────────\n🎯 <i>Для нового теста введите другую идею.</i>"
        
        await message.answer(final_text, parse_mode="HTML")
        await status.delete()
    except Exception as e:
        await message.answer("❌ Не удалось обработать запрос. Пожалуйста, попробуйте еще раз.")
        await status.delete()

# ==========================================
# ВЕБ-СЕРВЕР ДЛЯ ОБЛАКА RENDER
# ==========================================
async def handle_index(request): 
    return web.Response(text="Бизнес-аналитик активен.")

async def main():
    app = web.Application()
    app.router.add_get('/', handle_index)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', int(os.getenv("PORT", 8000))).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())