from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ConversationHandler, filters, CallbackQueryHandler
)
from handlers import (
    start, main_menu_handler, category_handler, question_number_handler,
    confirm_free_or_sub_use_handler, payment_handler, back_to_questions_handler,
    subscription_handler, subscription_confirm, admin_stats, handle_admin_callback,
    list_active_subs, manage_subscription, subscription_action
)
from config import TOKEN, ADMIN_TELEGRAM_ID
from users import init_users_db

(
    CHOOSE_CATEGORY,
    CHOOSE_QUESTION,
    WAIT_PAYMENT,
    FREE_OR_SUB_CONFIRM,
    SUBSCRIPTION_FLOW,
    ADMIN_MANAGE_SUB,
    ADMIN_SUB_ACTION
) = range(7)

def main():
    init_users_db()
    app = ApplicationBuilder().token(TOKEN).build()

    # المحادثة الرئيسية للبوت
    conv = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            MessageHandler(filters.Regex("^(القائمة الرئيسية)$"), main_menu_handler),
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
            CommandHandler("start", start)
        ],
        allow_reentry=True
    )
    
    # محادثة إدارة الاشتراكات للمشرفين
    admin_conv = ConversationHandler(
        entry_points=[
            CommandHandler("active_subs", list_active_subs, filters=filters.User(ADMIN_TELEGRAM_ID)),
            CommandHandler("admin", admin_stats, filters=filters.User(ADMIN_TELEGRAM_ID))
        ],
        states={
            ADMIN_MANAGE_SUB: [
                MessageHandler(filters.TEXT & ~filters.COMMAND & filters.User(ADMIN_TELEGRAM_ID), manage_subscription)
            ],
            ADMIN_SUB_ACTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND & filters.User(ADMIN_TELEGRAM_ID), subscription_action)
            ],
        },
        fallbacks=[
            CommandHandler("active_subs", list_active_subs, filters=filters.User(ADMIN_TELEGRAM_ID)),
            CommandHandler("admin", admin_stats, filters=filters.User(ADMIN_TELEGRAM_ID))
        ],
        allow_reentry=True
    )

    app.add_handler(conv)
    app.add_handler(admin_conv)
    app.add_handler(CallbackQueryHandler(handle_admin_callback, pattern=r"^(accept|reject)_\d+$"))
    
    app.run_polling()

if __name__ == "__main__":
    main()