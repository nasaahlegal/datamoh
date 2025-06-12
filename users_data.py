# تخزين بيانات المستخدمين: عدد الأسئلة المجانية والاشتراكات
import time

user_data = {}

def get_user_info(user_id):
    if user_id not in user_data:
        user_data[user_id] = {
            "free_questions_left": 3,
            "subscribed_until": None
        }
    return user_data[user_id]

def use_free_question(user_id):
    info = get_user_info(user_id)
    if info["free_questions_left"] > 0:
        info["free_questions_left"] -= 1
        return True
    return False

def has_subscription(user_id):
    info = get_user_info(user_id)
    if info["subscribed_until"] and info["subscribed_until"] > int(time.time()):
        return True
    return False

def subscribe_user(user_id, months=1):
    now = int(time.time())
    expire = now + months * 30 * 24 * 60 * 60
    info = get_user_info(user_id)
    info["subscribed_until"] = expire