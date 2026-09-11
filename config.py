import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
AVIASALES_TOKEN = os.getenv("AVIASALES_TOKEN", "")
KIWI_API_KEY = ""  # не используется: Kiwi требует 50k MAU, заменён Aviasales Search API
CHECK_INTERVAL_HOURS = int(os.getenv("CHECK_INTERVAL_HOURS", "6"))

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не задан в .env файле")
