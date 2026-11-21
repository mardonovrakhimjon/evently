import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
BOT_API_SECRET = os.getenv("BOT_API_SECRET", "")
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000/api/v1")
