from config import ADMIN_TELEGRAM_ID

def is_admin_only(func):
    async def wrapper(update, context, *args, **kwargs):
        # Detect if the update is message or callback_query
        user_id = None
        if getattr(update, "effective_user", None):
            user_id = update.effective_user.id

        if user_id != ADMIN_TELEGRAM_ID:
            if getattr(update, "message", None):
                await update.message.reply_text("❌ ليس لديك صلاحية تنفيذ هذا الأمر.")
            elif getattr(update, "callback_query", None):
                await update.callback_query.answer("❌ ليس لديك صلاحية تنفيذ هذا الأمر.", show_alert=True)
            return
        return await func(update, context, *args, **kwargs)
    return wrapper