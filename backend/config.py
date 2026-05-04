"""Environment & constants."""
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

MONGO_URL = os.environ['MONGO_URL']
DB_NAME = os.environ['DB_NAME']
CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')

RESEND_API_KEY = os.environ.get('RESEND_API_KEY')
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'onboarding@resend.dev')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

VAPID_PUBLIC_KEY = os.environ.get('VAPID_PUBLIC_KEY')
VAPID_PRIVATE_KEY = os.environ.get('VAPID_PRIVATE_KEY')
VAPID_CLAIMS_SUB = os.environ.get('VAPID_CLAIMS_SUB', 'mailto:admin@meowls.gov')

# Email retry queue tuning (exponential backoff, seconds)
EMAIL_RETRY_BACKOFF_SECONDS = [60, 300, 900, 3600, 21600]  # 1m, 5m, 15m, 1h, 6h
EMAIL_RETRY_WORKER_INTERVAL_SECONDS = 30
EMAIL_RETRY_MAX_ATTEMPTS = len(EMAIL_RETRY_BACKOFF_SECONDS)
