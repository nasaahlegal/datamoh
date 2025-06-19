import time
from functools import wraps
from config import ADMIN_TELEGRAM_ID

# الأوامر التي يجب استثناؤها من الحماية (يمكنك تعديلها أو إضافة غيرها حسب الحاجة)
EXCLUDED_COMMANDS = {"نعم", "لا", "رجوع", "القائمة الرئيسية"}

last_commands = {}

def anti_spam(timeout=15):
    def decorator(func):
        @wraps(func)
        async def wrapper(update, context, *args, **kwargs):
            user_id = getattr(update.effective_user, "id", None)
            if user_id is None or user_id == ADMIN_TELEGRAM_ID:
                return await func(update, context, *args, **kwargs)
            # استخراج نص الأمر الحالي فقط (النص الكامل للرسالة)
            if hasattr(update, "message") and update.message:
                current_command = (update.message.text or "").strip()
            else:
                current_command = ""
            # استثناء أوامر الأزرار
            if current_command in EXCLUDED_COMMANDS:
                return await func(update, context, *args, **kwargs)
            now = time.time()
            user_entry = last_commands.get(user_id, {})
            last_cmd = user_entry.get("command")
            last_time = user_entry.get("time", 0)
            if current_command == last_cmd:
                if now - last_time < timeout:
                    await update.message.reply_text(
                        f"⚠️ يرجى الانتظار {timeout} ثانية قبل تكرار نفس الطلب.",
                        protect_content=True
                    )
                    return
            last_commands[user_id] = {"command": current_command, "time": now}
            return await func(update, context, *args, **kwargs)
        return wrapper
    return decorator