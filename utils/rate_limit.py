import time
from functools import wraps

# سجل آخر محاولة لكل مستخدم
_last_user_action = {}

def rate_limit(min_seconds=60):
    """
    ديكوريتر يمنع المستخدم من تنفيذ الإجراء أكثر من مرة خلال min_seconds ثانية.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(update, context, *args, **kwargs):
            user_id = getattr(update.effective_user, "id", None)
            now = time.time()
            # إذا لم يُنفذ من قبل أو مرت المدة، دع التنفيذ
            if user_id is None or user_id not in _last_user_action or now - _last_user_action[user_id] >= min_seconds:
                _last_user_action[user_id] = now
                return await func(update, context, *args, **kwargs)
            else:
                await update.message.reply_text(
                    "⏳ يرجى الانتظار قليلاً قبل إعادة المحاولة.",
                    protect_content=True
                )
                return
        return wrapper
    return decorator