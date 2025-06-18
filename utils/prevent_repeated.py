import time
from functools import wraps

REPEAT_BLOCK_SECONDS = 15

def prevent_repeated_commands(func):
    @wraps(func)
    async def wrapper(update, context, *args, **kwargs):
        user_data = context.user_data
        # يدعم فقط الرسائل النصية العادية (وليس الكولباك أو الصور)
        message = getattr(update, "message", None)
        if not message or not getattr(message, "text", None):
            return await func(update, context, *args, **kwargs)
        text = message.text.strip()
        now = time.time()
        last_cmd = user_data.get("last_cmd_text")
        last_cmd_time = user_data.get("last_cmd_time", 0)
        if last_cmd == text and now - last_cmd_time < REPEAT_BLOCK_SECONDS:
            await message.reply_text(
                f"🚫 يرجى عدم تكرار نفس الأمر بسرعة.\n"
                f"انتظر {int(REPEAT_BLOCK_SECONDS - (now - last_cmd_time))} ثانية قبل إعادة المحاولة."
            )
            return
        user_data["last_cmd_text"] = text
        user_data["last_cmd_time"] = now
        return await func(update, context, *args, **kwargs)
    return wrapper