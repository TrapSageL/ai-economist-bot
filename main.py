import asyncio
import os
import re
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart
from google import genai
from aiohttp import web

# ==========================================
# КОНФИГУРАЦИЯ И БЕЗОПАСНОСТЬ
# ==========================================
BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_KEY")

if not BOT_TOKEN or not GEMINI_KEY:
    exit("Ошибка: Переменные окружения BOT_TOKEN или GEMINI_KEY не заданы!")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
ai_client = genai.Client(api_key=GEMINI_KEY)

# ==========================================
# ФУНКЦИЯ ЗАЩИТЫ СИНТАКСИСА ТЕЛЕГРАМА
# ==========================================
def Сlean_and_format_html(text: str) -> str:
    """Очищает текст от опасных тегов и подтягивает оформление до идеала"""
    # Удаляем маркдаун-звездочки, если ИИ их случайно забыл
    text = text.replace("**", "").replace("*", "")
    text = text.replace("###", "")
    
    # Удаляем ломающие Telegram теги, заменяя их на переносы строк
    text = re.sub(r'</?(p|div|span|br|ul|ol|li)>', '\n', text)
    
    # Убираем тройные переносы строк, делая текст аккуратным
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

# ==========================================
# ИНТЕРФЕЙС И ИМБОВЫЕ КНОПКИ
# ==========================================
@dp.message(CommandStart())
async def cmd_start(message: Message):
    kb = [
        [KeyboardButton(text="⚡️ Предложи мне прибыльную идею")],
        [KeyboardButton(text="🧠 ИИ-ассистент для автоматизации рутины локального бизнеса")],
        [KeyboardButton(text="📱 Сеть Telegram Mini Apps для заказа кастомного мерча")]
    ]
    keyboard = ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Накатай стартап или жми на кнопку..."
    )
    
    welcome_text = (
        "📊 <b>Йоу! На связи твой ИИ-Бизнес Ментор.</b>\n\n"
        "Я не собираюсь льстить и хвалить проигрышные темы. Моя цель — устроить твоей задумке <b>жесткий венчурный краш-тест</b>.\n\n"
        "❌ Если идея — нерентабельный скам, я разнесу её по фактам (юнит-экономика, риски, ЦА).\n"
        "🔥 Если тема — жир, я распишу пошаговый план, как поднять на этом кэш.\n\n"
        "💡 <i>Напиши свою задумку или нажми на кнопку, чтобы я сам предложил тебе имбовый стартап!</i>"
    )
    await message.answer(welcome_text, parse_mode="HTML", reply_markup=keyboard)

# ==========================================
# ГЛАВНЫЙ ОПЕРАЦИОННЫЙ АНАЛИЗ (GEMINI 2.5)
# ==========================================
@dp.message(F.text)
async def analyze_business_idea(message: Message):
    status_message = await message.answer("🔄 Подключаю аналитику Кремниевой долины, считаю маржу...")
    
    system_prompt = (
        "Ты — циничный, молодой и дико успешный венчурный инвестор. Ты насквозь видишь рынок. "
        "Твоя аудитория — молодые ребята (14-20 лет), которые хотят запустить свой первый бизнес.\n"
        "Ты говоришь уверенно, современно, авторитетно. Твой сленг (скам, профит, жир, темка, база) "
        "выглядит естественно, а не как у 40-летнего бати. Ты не душнишь, но сыплешь реальными терминами (CAC, LTV, MVP, маржинальность).\n\n"
        "ТВОЯ ЗАДАЧА:\n"
        "1. Если пользователь пишет 'Предложи мне прибыльную идею' — сгенерируй ОДНУ ультра-актуальную, свежую и прибыльную идею на 2026 год, которую подросток может начать почти без бюджета. Опиши её по структуре ниже.\n"
        "2. Если пользователь ввел свою идею — сделай ей честный, жесткий краш-тест. Еслидея лажа (например, продавать воздух или открыть ларек с дисками) — прямо и аргументированно разнеси её. Не хвали плохие идеи!\n\n"
        "ПРАВИЛО ОФОРМЛЕНИЯ:\n"
        "Используй ТОЛЬКО теги <b> и <i> для выделения важных мыслей. Никаких звездочек! "
        "Ответь строго по следующим 4 блокам, разделяя их текстовой линией:\n\n"
        "🧐 <b>ВЕРДИКТ И РЕАЛЬНОСТЬ</b>\n"
        "[Твоя жесткая и честная оценка идеи. Это топ или скам/утопия?]\n\n"
        "────────────────────\n\n"
        "💸 <b>ЮНИТ-ЭКОНОМИКА (ГДЕ КЭШ?)</b>\n"
        "[Конкретная схема монетизации. За что люди будут платить? Как выйти в плюс?]\n\n"
        "────────────────────\n\n"
        "🚩 <b>ГЛАВНЫЕ РИСКИ</b>\n"
        "[Почему этот проект может загнуться в первый же месяц. Жесткие подводные камни.]\n\n"
        "────────────────────\n\n"
        "🛠 <b>MVP НА КОЛЕНКЕ (ПЕРВЫЙ ШАГ)</b>\n"
        "[Пошаговый план, как бесплатно протестировать эту тему за 48 часов.]"
    )
    
    try:
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=f"{system_prompt}\n\nЗапрос пользователя: {message.text}"
        )
        
        # Пропускаем текст через нашу функцию защиты синтаксиса
        final_text = Сlean_and_format_html(response.text)
        
        await message.answer(final_text, parse_mode="HTML")
        
        try:
            await status_message.delete()
        except:
            pass
            
    except Exception as e:
        await message.answer(f"❌ Ошибка ИИ-анализа: {str(e)}\nПопробуй отправить запрос еще раз.")

# ==========================================
# ВЕБ-СЕРВЕР ДЛЯ ПОДДЕРЖАНИЯ ЖИЗНИ (HEALTH CHECK)
# ==========================================
async def handle_index(request):
    return web.Response(text="Бизнес-Бот активен и работает!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_index)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

# ==========================================
# ТОЧКА ВХОДА В СИСТЕМУ
# ==========================================
async def main():
    await start_web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())