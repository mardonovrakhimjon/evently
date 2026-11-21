import httpx
from bot.config import BACKEND_API_URL, BOT_API_SECRET


async def confirm_telegram_link(token: str, chat_id: int) -> tuple[bool, str]:
    """
    Calls backend /telegram/confirm/ with X-Bot-Secret header to link chat_id.
    """
    url = f"{BACKEND_API_URL.rstrip('/')}/telegram/confirm/"
    headers = {
        "X-Bot-Secret": BOT_API_SECRET,
    }
    payload = {
        "token": token,
        "chat_id": chat_id,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                return True, "Hisobingiz muvaffaqiyatli bog'landi!"
            data = response.json()
            return False, data.get("detail", "Xatolik yuz berdi.")
    except Exception as exc:
        return False, f"Serverga ulanishda xatolik: {exc}"
