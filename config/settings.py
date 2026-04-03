import os
from dotenv import load_dotenv

load_dotenv()

# ── Client identity ────────────────────────────────────────────────────────
CLIENT_NAME     = os.getenv("CLIENT_NAME", "MyBrand")
CLIENT_INDUSTRY = os.getenv("CLIENT_INDUSTRY", "SaaS")
CLIENT_TONE     = os.getenv("CLIENT_TONE", "professional")
CLIENT_LANGUAGE = os.getenv("CLIENT_LANGUAGE", "en")

# ── Model ──────────────────────────────────────────────────────────────────
MODEL_PROVIDER  = os.getenv("MODEL_PROVIDER", "groq")

# ── Platform credentials ───────────────────────────────────────────────────
LINKEDIN = {
    "email":    os.getenv("LINKEDIN_EMAIL"),
    "password": os.getenv("LINKEDIN_PASSWORD"),
    "lead_keywords": os.getenv("LINKEDIN_LEAD_SEARCH_KEYWORDS", "").split(","),
    "daily_connection_limit": int(os.getenv("LINKEDIN_DAILY_CONNECTION_LIMIT", 20)),
}
INSTAGRAM = {
    "username": os.getenv("INSTAGRAM_USERNAME"),
    "password": os.getenv("INSTAGRAM_PASSWORD"),
}
TIKTOK = {"session_id": os.getenv("TIKTOK_SESSION_ID")}
FACEBOOK = {
    "access_token": os.getenv("FACEBOOK_ACCESS_TOKEN"),
    "page_id":      os.getenv("FACEBOOK_PAGE_ID"),
}
TELEGRAM = {
    "bot_token":   os.getenv("TELEGRAM_BOT_TOKEN"),
    "channel_id":  os.getenv("TELEGRAM_CHANNEL_ID"),
}
WHATSAPP = {
    "account_sid": os.getenv("TWILIO_ACCOUNT_SID"),
    "auth_token":  os.getenv("TWILIO_AUTH_TOKEN"),
    "from_number": os.getenv("TWILIO_WHATSAPP_FROM"),
}
EMAIL = {
    "sendgrid_key": os.getenv("SENDGRID_API_KEY"),
    "from_address": os.getenv("EMAIL_FROM"),
}
CALENDLY = {
    "api_key":   os.getenv("CALENDLY_API_KEY"),
    "event_url": os.getenv("CALENDLY_EVENT_URL"),
}

# ── Memory ─────────────────────────────────────────────────────────────────
CHROMA_PERSIST_DIR  = os.getenv("CHROMA_PERSIST_DIR", "./data/memory")
BUSINESS_DATA_DIR   = os.getenv("BUSINESS_DATA_DIR", "./data/business")
