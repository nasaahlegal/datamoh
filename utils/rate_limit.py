import time
from functools import wraps

# سجل: user_id -> {"action": action_name, "timestamp": وقت آخر تنفيذ}
_last_user_action = {}

def rate_limit_per_action(min_seconds=30, message="⏳ يرجى الانتظار 30 ثانية قبل إعادة المحاولة."):
    """
    يمنع تكرار نفس الإجراء (زر/أمر) خلال min_seconds ثانية لنفس المستخدم.
    لا يمنع الأوامر أو الأزرار المختلفة.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(update, context, *args, **kwargs):
            user_id = getattr(update.effective_user, "id", None)
            action_name = func.__name__
            now = time.time()
            last = _last_user_action.get(user_id)
            if last and last["action"] == action_name and now - last["timestamp"] < min_seconds:
                # تكرار نفس الإجراء بزمن أقل من المطلوب
                if getattr(update, "message", None):
                    await update.message.reply_text(
                        message, protect_content=True
                    )
                elif getattr(update, "callback_query", None):
                    await update.callback_query.answer(
                        message, show_alert=True
                    )
                return  # منع التنفيذ
            # سجل الإجراء الحالي
            _last_user_action[user_id] = {"action": action_name, "timestamp": now}
            return await func(update, context, *args, **kwargs)
        return wrapper
    return decorator