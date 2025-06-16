import os
import json

TOKEN = os.environ["BOT_TOKEN"]
DATABASE_URL = os.environ["DATABASE_URL"]

ADMIN_TELEGRAM_ID = int(os.environ.get("ADMIN_TELEGRAM_ID", "8109994800"))

# تحميل الأسئلة والأجوبة من ملف JSON موحّد
with open("data/questions.json", encoding="utf-8") as f:
    Q_DATA = json.load(f)

FREE_QUESTIONS_LIMIT = 3
QUESTION_PRICE = 5000
SUBSCRIPTION_PRICE = 50000
SUBSCRIPTION_DAYS = 30
PAY_ACCOUNT = "9916153415"

SUPPORT_EMAIL = "mohamycom@proton.me"
SUPPORT_CHANNEL = "t.me/mohamycom_tips"
