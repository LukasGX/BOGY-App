import os
from dotenv import load_dotenv
from slowapi import Limiter
from slowapi.util import get_remote_address

load_dotenv()

sl_limiter = Limiter(key_func=get_remote_address, default_limits=["200/hour"])

# Load VAPID credentials from environment for security (set in .env)
VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY")
VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY")
VAPID_EMAIL = os.getenv("VAPID_EMAIL")
SECRET_KEY = os.getenv("SESSION_SECRET_KEY")