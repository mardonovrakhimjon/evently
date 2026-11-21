import logging
from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from bot.api_client import confirm_telegram_link

logger = logging.getLogger(__name__)
router = Router()


@router.message(CommandStart())
async def handle_start(message: Message, command: CommandStart):
    token = command.args
    logger.info(f"Received /start command from {message.from_user.id} with token: {token}")

    if token:
        success, msg = await confirm_telegram_link(token, message.chat.id)
        if success:
            await message.answer(
                "✅ <b>Hisobingiz muvaffaqiyatli bog‘landi!</b>\n\n"
                "Endi siz tadbirlarga yozilganingizda tasdiq xabari va tadbir oldidan "
                "eslatmalarni shu bot orqali olasiz.",
                parse_mode="HTML",
            )
        else:
            await message.answer(
                f"❌ <b>Hisobni bog'lashda xatolik:</b>\n{msg}\n\n"
                "Iltimos, sayt orqali yangi havola olib qayta urinib ko'ring.",
                parse_mode="HTML",
            )
    else:
        await message.answer(
            "👋 <b>Assalomu alaykum!</b>\n\n"
            "Men <b>Evently</b> platformasining rasmiy bildirishnoma botiman.\n\n"
            "Hisobingizni bog'lash uchun:\n"
            "1. Evently saytidagi profilingizga kiring.\n"
            "2. 'Telegramni ulash' tugmasini bosing.\n"
            "3. Sayt taqdim etgan havola orqali botga kiring.",
            parse_mode="HTML",
        )


@router.message(Command("help"))
async def handle_help(message: Message):
    await message.answer(
        "ℹ️ <b>Evently Bot Yordam</b>\n\n"
        "Ushbu bot tadbirlar bo'yicha bildirishnomalar va eslatmalar yuborish uchun xizmat qiladi.\n\n"
        "Buyruqlar:\n"
        "/start - Botni ishga tushirish\n"
        "/help - Yordam xabarini ko'rish",
        parse_mode="HTML",
    )


@router.message()
async def handle_other_messages(message: Message):
    await message.answer(
        "Iltimos, botdan foydalanish uchun /start yoki /help buyrug'idan foydalaning.",
        parse_mode="HTML",
    )
