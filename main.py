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
# ИНТЕРФЕЙС (ЯРКИЙ И КЛИКАБЕЛЬНЫЙ)
# ==========================================
@dp.message(CommandStart())
async def cmd_start(message: Message):
    kb = [
        [KeyboardButton(text="⚡️ ПРЕДЛОЖИ ТРЕНДОВУЮ ИДЕЮ 2026")],
        [KeyboardButton(text="🤖 ИИ-ассистент"), KeyboardButton(text="📱 Мини-апп в ТГ")]
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    
    welcome_text = (
        "🤖 КИБЕР-МЕНТОР СТАРТАПОВ АКТИВИРОВАН\n"
        "───────────────────────────────\n\n"
        "Врубай логику: отправь мне свою бизнес-идею на краш-тест или нажми верхнюю кнопку, и я выкачу готовый прибыльный кейс.\n\n"
        "Правда в глаза, жесткий аудит, без цензуры и душноты."
    )
    await message.answer(welcome_text, reply_markup=keyboard)

# ==========================================
# ДИНАМИЧЕСКИЙ ДАШБОРД (ГЕНЕРАЦИЯ И АНАЛИЗ)
# ==========================================
@dp.message(F.text)
async def analyze_business_idea(message: Message):
    status_msg = await message.answer("⏳ Сканирую рынок, генерирую дашборд...")
    
    # Если нажата кнопка генерации идеи
    if "ПРЕДЛОЖИ" in message.text or "идею" in message.text.lower():
        system_prompt = (
            "Ты — футуристичный венчурный ИИ-генератор. Придумай ОДНУ конкретную, гениальную и простую "
            "бизнес-идею для микробизнеса на 2026 год, которую можно запустить без денег.\n"
            "Пиши максимально коротко, тезисно, используй эмодзи-шкалы. Никакого HTML и звездочек.\n\n"
            "ФОРМАТ ОТВЕТА СТРОГО ТАКОЙ:\n\n"
            "⚡️ СТАТУС: ТРЕНД 2026\n"
            "───────────────────────────────\n"
            "💎 ИДЕЯ: [Название стартапа в 3 словах]\n"
            "📊 ПОТЕНЦИАЛ: [Оценка от 1 до 5 звезд, например ⭐️⭐️⭐️⭐️⭐️]\n"
            "📌 СУТЬ: [Коротко, в чем фишка стартапа]\n"
            "💰 КЭШБЕК: [На чем конкретно заработок]\n"
            "🚀 СТАРТ: [Что сделать в первые 48 часов без бюджета]"
        )
        user_input = "Сгенерируй легальный и прибыльный концепт бизнеса."
        
    # Если пользователь прислал СВОЮ идею
    else:
        system_prompt = (
            "Ты — циничный цифровой аудитор стартапов. Твоя задача — сделать моментальный краш-тест идеи.\n"
            "Оцени её критически. Пиши ультра-коротко (до 70 слов), без воды, без HTML и без звездочек (*).\n\n"
            "ЕСЛИ ИДЕЯ СЛАБАЯ/БРЕДОВАЯ, выкати этот формат:\n"
            "🔴 СТАТУС: КРАХ И СКАМ\n"
            "───────────────────────────────\n"
            "💀 ПОЧЕМУ ПРОДОХНЕТ: [Главная тупость идеи в 2 строчки]\n"
            "📉 РЕЙТИНГ: ⭐️☆☆☆☆\n"
            "💡 ПИВОТ: [Как переделать эту лажу в нормальную рабочую тему]\n\n"
            "ЕСЛИ ИДЕЯ РЕАЛЬНО ЖИЗНЕСПОСОБНАЯ, выкати этот формат:\n"
            "🟢 СТАТУС: ДОПУЩЕН К РЫНКУ\n"
            "───────────────────────────────\n"
            "🔥 В ЧЕМ СИЛА: [Главный плюс идеи]\n"
            "📈 РЕЙТИНГ: [Твоя оценка звезд, например ⭐️⭐️⭐️⭐️☆]\n"
            "💵 ПЛАН МОНЕТИЗАЦИИ: [Откуда прилетят первые деньги]\n"
            "🛠 ШАГ ДЛЯ MVP: [Как быстро собрать прототип на коленке]"
        )
        user_input = f"Проведи аудит проекта: {message.text}"
        
    try:
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=f"{system_prompt}\n\n{user_input}"
        )
        
        # Полная очистка от мусора маркдауна
        final_text = response.text.replace("**", "").replace("*", "").strip()
        final_text += "\n───────────────────────────────\n🎮 Жду следующий концепт или клик по кнопке."
        
        await message.answer(final_text)
        await status_msg.delete()
        
    except Exception as e:
        # Если вдруг упадет сеть — мы увидим точную причину ошибки
        await message.answer(f"❌ Ошибка модуля ИИ: {str(e)}")
        await status_msg.delete()

# ==========================================
# СЕТЕВОЙ ХОСТИНГ ДЛЯ RENDER
# ==========================================
async def handle_index(request): return web.Response(text="AI Online")
async def main():
    app = web.Application()
    app.router.add_get('/', handle_index)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', int(os.getenv("PORT", 8000))).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())