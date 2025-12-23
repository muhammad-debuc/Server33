import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from yt_dlp import YoutubeDL

# Твой токен
TOKEN = "7830133674:AAFb4DklxfjqsiLWSLvlX7ybC4SUgtexxGY"

bot = Bot(token=TOKEN)
dp = Dispatcher()

user_settings = {}

MESSAGES = {
    'ru': {
        'start': "🇷🇺 Выбери язык / 🇹🇯 Забонро интихоб кунед:",
        'welcome': "🇷🇺 Привет! Пришли ссылку, чтобы получить кнопки для скачивания, или задай вопрос нейросети 🤖",
        'loading': "⏳ Обработка...",
        'ai_thinking': "🤔 Нейросеть думает...",
        'manual_save': "📥 Нажми на кнопку ниже, чтобы скачать файл вручную:",
        'error': "❌ Ошибка. Ссылка не поддерживается или скрыта."
    },
    'tj': {
        'welcome': "🇹🇯 Салом! Истинодро фиристед то тугмаҳои боргириро гиред, ё ба нейросеть савол диҳед 🤖",
        'loading': "⏳ Дар ҳоли кор...",
        'ai_thinking': "🤔 Нейросеть фикр карда истодааст...",
        'manual_save': "📥 Тугмаи зерро пахш кунед, то файлро дастӣ боргирӣ кунед:",
        'error': "❌ Хатогӣ. Истинод кор намекунад."
    }
}

# --- Блок Нейросети (Новый шлюз) ---
async def ask_ai(prompt):
    try:
        # Используем альтернативный бесплатный шлюз
        url = "https://api.pawan.krd/cosmosrp/v1/chat/completions"
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": prompt}]
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=20) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data['choices'][0]['message']['content']
                else:
                    return "🤖 Извините, я сейчас перегружен. Попробуйте через минуту."
    except:
        return "🤖 Ошибка связи. Проверьте интернет в Termux."

# --- Хэндлеры ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="Русский 🇷🇺", callback_data="lang_ru")
    kb.button(text="Тоҷикӣ 🇹🇯", callback_data="lang_tj")
    await message.answer(MESSAGES['ru']['start'], reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("lang_"))
async def set_lang(callback: types.CallbackQuery):
    lang = callback.data.split("_")[1]
    user_settings[callback.from_user.id] = {'lang': lang}
    await callback.message.edit_text(MESSAGES[lang]['welcome'])

@dp.message(F.text.regexp(r'^https?://'))
async def handle_link(message: types.Message):
    user_id = message.from_user.id
    lang = user_settings.get(user_id, {}).get('lang', 'ru')
    url = message.text
    wait_msg = await message.answer(MESSAGES[lang]['loading'])

    try:
        # Получаем прямые ссылки без скачивания на само устройство
        ydl_opts = {'quiet': True, 'noplaylist': True, 'format': 'best'}
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            direct_url = info.get('url')
            title = info.get('title', 'Video')

        if direct_url:
            kb = InlineKeyboardBuilder()
            kb.button(text="📥 Скачать / Боргирӣ", url=direct_url)
            await wait_msg.edit_text(f"🎬 {title}\n\n{MESSAGES[lang]['manual_save']}", 
                                   reply_markup=kb.as_markup())
        else:
            await wait_msg.edit_text(MESSAGES[lang]['error'])
    except Exception as e:
        await wait_msg.edit_text(f"{MESSAGES[lang]['error']}\n{str(e)[:50]}")

@dp.message(F.text)
async def handle_ai(message: types.Message):
    user_id = message.from_user.id
    lang = user_settings.get(user_id, {}).get('lang', 'ru')
    
    await bot.send_chat_action(message.chat.id, action="typing")
    status_msg = await message.answer(MESSAGES[lang]['ai_thinking'])
    
    answer = await ask_ai(message.text)
    await status_msg.edit_text(answer)

async def main():
    print("🚀 Бот запущен (Ручной режим + AI)")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
