import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from bot.config import BOT_TOKEN
from bot.handlers import router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


async def main():
    if not BOT_TOKEN or BOT_TOKEN in ("dummy_telegram_bot_token", "your_telegram_bot_token"):
        logger.warning(
            "TELEGRAM_BOT_TOKEN o'rnatilmagan yoki dummy holatda! Bot konteyneri to'xtab qolmasligi uchun kutish rejimida ishlaydi. Haqiqiy tokenni .env faylida ko'rsating."
        )
        while True:
            await asyncio.sleep(3600)

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()
    dp.include_router(router)

    logger.info("Evently Telegram bot ishga tushmoqda...")
    try:
        # Clear webhook and old backlog updates
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
