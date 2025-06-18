import time
from functools import wraps

_last_user_action = {}

def rate_limit(min_seconds=30, message="⏳ يرجى الانتظار 30 ثانية قبل إعادة المحاولة."):
    """
    ديكوريتر يمنع المستخدم من تنفيذ الإجراء أكثر من مرة خلال min_seconds ثانية.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(update, context, *args, **kwargs):
            user_id = getattr(update.effective_user, "id", None)
            now = time.time()
            if user_id is None or user_id not in _last_user_action or now - _last_user_action[user_id] >= min_seconds:
                _last_user_action[user_id] = now
                return await func(update, context, *args, **kwargs)
            else:
                # حاول إرسال الرسالة في المكان الصحيح
                if getattr(update, "message", None):
                    await update.message.reply_text(
                        message, protect_content=True
                    )
                elif getattr(update, "callback_query", None):
                    await update.callback_query.answer(
                        message, show_alert=True
                    )
                return
        return wrapper
    return decorator