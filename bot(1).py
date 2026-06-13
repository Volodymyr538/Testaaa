import asyncio
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder
import json
from datetime import datetime

# ==================== НАСТРОЙКИ ====================
BOT_TOKEN = "8903935395:AAHWLIPYg1yFt0mI9pnZly3STFtblOJ4mCM"       # @BotFather
WEBHOOK_SECRET = "adonis_secret"   # Секретный ключ (совпадает с Lua скриптом)
PORT = 8080                        # Порт для HTTP сервера
# ===================================================

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Хранилище chat_id всех кто сделал /start
subscribers: set[int] = set()


@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    subscribers.add(message.chat.id)
    await message.answer(
        "👾 <b>Roblox Adonis Monitor</b>\n\n"
        "✅ Ты подписан на уведомления об Adonis командах.\n"
        "Все команды в чате игры будут приходить сюда.",
        parse_mode="HTML"
    )


async def handle_webhook(request: web.Request):
    """Принимаем POST запрос от Roblox"""
    # Проверка секретного ключа
    secret = request.headers.get("X-Secret", "")
    if secret != WEBHOOK_SECRET:
        return web.Response(status=403, text="Forbidden")

    try:
        data = await request.json()
    except Exception:
        return web.Response(status=400, text="Invalid JSON")

    # Данные из Roblox
    player_name    = data.get("player", "Unknown")
    player_id      = data.get("userId", "?")
    command        = data.get("command", "?")
    args           = data.get("args", "")
    place_id       = data.get("placeId", "?")
    place_name     = data.get("placeName", "Unknown Place")
    server_job_id  = data.get("jobId", "?")
    team           = data.get("team", "—")
    timestamp      = data.get("timestamp", datetime.utcnow().isoformat())

    # Форматируем время
    try:
        dt = datetime.fromisoformat(timestamp)
        time_str = dt.strftime("%d.%m.%Y %H:%M:%S UTC")
    except Exception:
        time_str = timestamp

    text = (
        f"🎮 <b>Adonis команда обнаружена!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Игрок:</b> <code>{player_name}</code>\n"
        f"🆔 <b>User ID:</b> <code>{player_id}</code>\n"
        f"🏷 <b>Команда:</b> <code>:{command}</code>\n"
        f"📝 <b>Аргументы:</b> <code>{args if args else '—'}</code>\n"
        f"👥 <b>Команда/Фракция:</b> {team}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🗺 <b>Место:</b> {place_name}\n"
        f"🔢 <b>Place ID:</b> <code>{place_id}</code>\n"
        f"🖥 <b>Server Job ID:</b> <code>{server_job_id[:16]}...</code>\n"
        f"🕐 <b>Время:</b> {time_str}"
    )

    # Кнопка профиля игрока
    builder = InlineKeyboardBuilder()
    builder.button(
        text="👤 Профиль Roblox",
        url=f"https://www.roblox.com/users/{player_id}/profile"
    )
    builder.button(
        text="🎮 Открыть игру",
        url=f"https://www.roblox.com/games/{place_id}"
    )
    builder.adjust(2)

    # Рассылаем всем подписчикам
    for chat_id in list(subscribers):
        try:
            await bot.send_message(
                chat_id,
                text,
                parse_mode="HTML",
                reply_markup=builder.as_markup()
            )
        except Exception as e:
            logging.warning(f"Не удалось отправить {chat_id}: {e}")
            subscribers.discard(chat_id)

    return web.Response(text="OK")


async def main():
    # Запускаем HTTP сервер и бота параллельно
    app = web.Application()
    app.router.add_post("/adonis", handle_webhook)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

    logging.info(f"HTTP сервер запущен на порту {PORT}")
    logging.info("Бот запущен, жду событий...")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
