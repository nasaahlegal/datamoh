import time
from functools import wraps
from config import ADMIN_TELEGRAM_ID

# هيكلية: {user_id: {"command": str, "time": float}}
last_commands = {}

def anti_spam(timeout=15):
    def decorator(func):
        @wraps(func)
        async def wrapper(update, context, *args, **kwargs):
            user_id = getattr(update.effective_user, "id", None)
            # استثناء الأدمن من الحظر
            if user_id is None or user_id == ADMIN_TELEGRAM_ID:
                return await func(update, context, *args, **kwargs)
            # استخراج نص الأمر الحالي فقط (النص الكامل للرسالة)
            if hasattr(update, "message") and update.message:
                current_command = update.message.text or ""
            else:
                current_command = ""
            now = time.time()
            user_entry = last_commands.get(user_id, {})
            last_cmd = user_entry.get("command")
            last_time = user_entry.get("time", 0)

            if current_command == last_cmd:
                if now - last_time < timeout:
                    # منع التكرار
                    await update.message.reply_text(
                        f"⚠️ يرجى الانتظار {timeout} ثانية قبل تكرار نفس الطلب.",
                        protect_content=True
                    )
                    return
            # حفظ الأمر الجديد/الوقت
            last_commands[user_id] = {"command": current_command, "time": now}
            return await func(update, context, *args, **kwargs)
        return wrapper
    return decorator