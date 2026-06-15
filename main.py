import asyncio
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart
from google import genai
from aiohttp import web

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Получаем список ключей. В Render укажи их через запятую: КЛЮЧ1,КЛЮЧ2,КЛЮЧ3
RAW_KEYS = os.getenv("GEMINI_KEYS", os.getenv("GEMINI_KEY", ""))
GEMINI_KEYS = [k.strip() for k in RAW_KEYS.split(",") if k.strip()]

if not BOT_TOKEN or not GEMINI_KEYS:
    exit("Ошибка: Настрой BOT_TOKEN и добавь хотя бы один ключ в GEMINI_KEYS!")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Индекс текущего активного ключа
current_key_index = 0

def get_ai_client():
    """Получает клиент ИИ со встроенной ротацией ключей"""
    global current_key_index
    active_key = GEMINI_KEYS[current_key_index]
    return genai.Client(api_key=active_key)

def rotate_key():
    """Переключает бота на следующий ключ в списке"""
    global current_key_index
    if len(GEMINI_KEYS) > 1:
        current_key_index = (current_key_index + 1) % len(GEMINI_KEYS)
        print(f"[SYSTEM] Переключение на API-ключ №{current_key_index + 1}")

# ==========================================
# ИНТЕРФЕЙС
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
        "Отправь мне свою бизнес-идею на жесткий краш-тест или нажми кнопку, и я выкачу готовый прибыльный кейс.\n\n"
        "Система защиты от сбоев включена. Работаем без пауз."
    )
    await message.answer(welcome_text, reply_markup=keyboard)

# ==========================================
# ДИНАМИЧЕСКИЙ ДАШБОРД С ЗАЩИТОЙ ОТ ПАДЕНИЯ КЛЮЧЕЙ
# ==========================================
@dp.message(F.text)
async def analyze_business_idea(message: Message):
    status_msg = await message.answer("⏳ Сканирую рынок, генерирую дашборд...")
    
    # Настройка промптов в зависимости от запроса
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
        
    # Цикл обхода ключей: пробуем отправить запрос доступными ключами
    response_text = None
    for _ in range(len(GEMINI_KEYS)):
        try:
            ai_client = get_ai_client()
            response = ai_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=f"{system_prompt}\n\n{user_input}"
            )
            response_text = response.text
            break  # Если запрос прошел успешно, выходим из цикла поиска ключа
        except Exception as e:
            print(f"[WARNING] Ошибка текущего ключа: {str(e)}")
            rotate_key()  # Переключаемся на следующий ключ при любой ошибке
            await asyncio.sleep(1) # Небольшая пауза перед повтором
            
    if response_text:
        final_text = response_text.replace("**", "").replace("*", "").strip()
        final_text += "\n───────────────────────────────\n🎮 Жду следующий концепт или клик по кнопке."
        await message.answer(final_text)
    else:
        await message.answer("❌ Все доступные API-ключи перегружены лимитами. Попробуйте через минуту.")
        
    await status_msg.delete()

# ==========================================
# СЕРВЕР RENDER
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