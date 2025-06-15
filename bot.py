from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ConversationHandler, filters, CallbackQueryHandler
)
from handlers import (
    start, main_menu_handler, category_handler, question_number_handler,
    confirm_free_or_sub_use_handler, payment_handler, back_to_questions_handler,
    subscription_handler, subscription_confirm, admin_stats, handle_admin_callback,
    admin_subs, admin_subscription_select, admin_subs_callback, lawyer_platform_handler
)
from config import TOKEN, ADMIN_TELEGRAM_ID
from users import init_users_db
from logger import get_logger
from rate_limiter import rate_limiter

logger = get_logger("bot")

(
    CHOOSE_CATEGORY,
    CHOOSE_QUESTION,
    WAIT_PAYMENT,
    FREE_OR_SUB_CONFIRM,
    SUBSCRIPTION_FLOW
) = range(5)

def log_user_event(update, event: str):
    user = update.effective_user
    logger.info(f"{event} | user_id={user.id} | username={user.username} | name={user.full_name}")

def main():
    init_users_db()
    app = ApplicationBuilder().token(TOKEN).build()

    # handlers الخاصة بالادمن يجب أن تكون قبل ConversationHandler
    app.add_handler(CommandHandler("admin", admin_stats, filters=filters.User(ADMIN_TELEGRAM_ID)))
    app.add_handler(CommandHandler("subs", admin_subs, filters=filters.User(ADMIN_TELEGRAM_ID)))
    app.add_handler(MessageHandler(filters.Regex("^[0-9]+$") & filters.User(ADMIN_TELEGRAM_ID), admin_subscription_select))
    app.add_handler(CallbackQueryHandler(admin_subs_callback, pattern=r"^(extend|delete)_[0-9]+|subs_back$"))
    app.add_handler(CallbackQueryHandler(handle_admin_callback, pattern=r"^(accept|reject)_\d+$"))

    # فلتر سبام قبل كل رسالة
    async def anti_spam(update, context):
        user_id = update.effective_user.id
        if not rate_limiter.is_allowed(user_id):
            await update.message.reply_text("🚫 يرجى الانتظار قليلاً قبل تكرار الطلب.")
            log_user_event(update, "SPAM_BLOCKED")
            return
        await context.application.process_update(update)

    app.add_handler(MessageHandler(filters.ALL, anti_spam), group=0)

    conv = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            MessageHandler(filters.Regex("^(القائمة الرئيسية)$"), main_menu_handler),
            MessageHandler(filters.Regex("^(العودة إلى منصة محامي.كوم)$"), lawyer_platform_handler),
        ],
        states={
            CHOOSE_CATEGORY: [
                MessageHandler(filters.Regex("^(عن المنصة|اشتراك شهري)$"), category_handler),
                MessageHandler(filters.TEXT & ~filters.COMMAND, category_handler),
            ],
            CHOOSE_QUESTION: [
                MessageHandler(filters.Regex("^[0-9]+$"), question_number_handler),
                MessageHandler(filters.Regex("^(رجوع|القائمة الرئيسية)$"), main_menu_handler),
            ],
            FREE_OR_SUB_CONFIRM: [
                MessageHandler(filters.Regex("^(نعم)$"), confirm_free_or_sub_use_handler),
                MessageHandler(filters.Regex("^(رجوع)$"), back_to_questions_handler),
                MessageHandler(filters.Regex("^(القائمة الرئيسية)$"), main_menu_handler),
            ],
            WAIT_PAYMENT: [
                MessageHandler(filters.Regex("^(تم التحويل|الغاء)$"), payment_handler),
            ],
            SUBSCRIPTION_FLOW: [
                MessageHandler(filters.Regex("^(موافق|رجوع)$"), subscription_confirm),
            ],
        },
        fallbacks=[
            MessageHandler(filters.Regex("^(القائمة الرئيسية)$"), main_menu_handler),
            MessageHandler(filters.Regex("^(العودة إلى منصة محامي.كوم)$"), lawyer_platform_handler),
            CommandHandler("start", start),
            MessageHandler(filters.ALL, main_menu_handler),
        ],
        allow_reentry=True
    )
    
    app.add_handler(conv)
    logger.info("Bot polling started.")
    app.run_polling()

if __name__ == "__main__":
    main()