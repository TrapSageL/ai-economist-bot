import asyncio
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart
from google import genai
from aiohttp import web

# ==========================================
# БЕЗОПАСНЫЕ НАСТРОЙКИ (ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ)
# ==========================================
BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_KEY")

if not BOT_TOKEN or not GEMINI_KEY:
    exit("Ошибка: Переменные окружения BOT_TOKEN или GEMINI_KEY не заданы!")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
ai_client = genai.Client(api_key=GEMINI_KEY)

# ==========================================
# ОБРАБОТКА КОМАНДЫ /START (КНОПКИ МЕНЮ)
# ==========================================
@dp.message(CommandStart())
async def cmd_start(message: Message):
    # Удобные кнопки с шаблонами молодежных бизнес-идей для теста
    kb = [
        [KeyboardButton(text="☕️ Кофейня самообслуживания")],
        [KeyboardButton(text="📱 Приложение для выгула собак")],
        [KeyboardButton(text="👕 Бренд одежды с ИИ-принтами")]
    ]
    keyboard = ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,  # Делает кнопки аккуратными и маленькими
        input_field_placeholder="Накатай свою идею или жми на шаблон..."
    )
    
    welcome_text = (
        "📊 <b>Йоу! Я твой персональный ИИ-бизнес-консультант.</b>\n\n"
        "Помогаю раскидать любые стартапы и темки с точки зрения экономики, юнит-анализа и жестких рисков. Без душноты и на понятном языке.\n\n"
        "💡 <i>Просто напиши мне свою задумку или нажми на один из готовых шаблонов внизу, устроим ей тест!</i>"
    )
    await message.answer(welcome_text, parse_mode="HTML", reply_markup=keyboard)

# ==========================================
# АНАЛИЗ БИЗНЕС-ИДЕИ ЧЕРЕЗ GEMINI (С ФИЛЬТРОМ ОШИБОК)
# ==========================================
@dp.message(F.text)
async def analyze_business_idea(message: Message):
    status_message = await message.answer("🔄 Экономический анализ запущен, собираю данные...")
    
    system_prompt = (
        "Ты — молодой, успешный венчурный инвестор, стартапер и крипто-предприниматель. "
        "Ты общаешься с молодёжью (твоя аудитория — школьники и студенты 14-20 лет) на их языке, "
        "используешь современный сленг (краш-тест, жир, вайб, скам, темка, профит, апрув, база), но при этом "
        "реально круто разбираешься в юнит-экономике, MVP, LTV и CAC.\n\n"
        "Твоя задача — провести честный, весёлый, но экономически грамотный краш-тест бизнес-идеи пользователя.\n"
        "СТРОГОЕ ПРАВИЛО ФОРМАТИРОВАНИЯ: Оформляй ответ СТРОГО с помощью HTML-тегов, которые поддерживает Telegram:\n"
        "Разрешено использовать ТОЛЬКО <b>для жирного текста</b> и <i>для курсива</i>.\n"
        "НЕ ИСПОЛЬЗУЙ звездочки (*), теги <p>, </p>, <div>, <br>, <ul>, <li>. Вообще никогда их не пиши!\n\n"
        "Ответь строго по следующим блокам, разделяя их тонкими линиями:\n\n"
        "💸 <b>В ЧЕМ ТЕМКА И ГДЕ ПРОФИТ?</b>\n"
        "<i>Разбор монетизации. Как рубить кэш и масштабировать этот вайб.</i>\n\n"
        "────────────────────\n\n"
        "🚩 <b>ОСТОРОЖНО, СКАМ (РИСКИ)</b>\n"
        "<i>Главные барьеры и почему проект может влететь на деньги. Без душноты.</i>\n\n"
        "────────────────────\n\n"
        "👥 <b>ДЛЯ КОГО ВАЙБ? (ЦА)</b>\n"
        "<i>Кто твои трушные платящие клиенты, которые купят продукт.</i>\n\n"
        "────────────────────\n\n"
        "🛠 <b>ДЕЛАЕМ MVP НА КОЛЕНКЕ</b>\n"
        "<i>Первые изи шаги, как протестить идею бесплатно и получить первый апрув.</i>\n\n"
        "Пиши чётко, тезисно, с юмором. Общая длина ответа — до 2000 символов."
    )
    
    try:
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=f"{system_prompt}\n\nИдея пользователя: {message.text}"
        )
        
        # Защита: удаляем теги <p>, если нейросеть их всё же добавит, чтобы Telegram не ругался
        clean_text = response.text.replace("<p>", "").replace("</p>", "\n")
        
        await message.answer(clean_text, parse_mode="HTML")
        try:
            await status_message.delete()
        except:
            pass
    except Exception as e:
        await message.answer(f"❌ Ошибка при анализе: {str(e)}")

# ==========================================
# ВСТРОЕННЫЙ ВЕБ-СЕРВЕР ДЛЯ ОБМАНА RENDER
# ==========================================
async def handle_index(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_index)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"Мини-веб-сервер запущен на порту {port}")

# ==========================================
# ГЛАВНЫЙ ЗАПУСК
# ==========================================
async def main():
    print("Бот-Экономист успешно запущен!")
    await start_web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())