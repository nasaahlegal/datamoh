from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ConversationHandler, CallbackQueryHandler, filters
)
from handlers import (
    start, category_handler, question_number_handler,
    payment_handler, back_handler, admin_action_handler,
    main_menu_handler, monthly_subscribe_handler, confirm_subscription_handler
)
from config import TOKEN
from users import init_users_db

(
    CHOOSE_CATEGORY,
    CHOOSE_QUESTION,
    WAIT_PAYMENT,
    MAIN_MENU,
    SUBSCRIBE_CONFIRM
) = range(5)

def main():
    init_users_db()
    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            MessageHandler(filters.Regex("^(القائمة الرئيسية)$"), main_menu_handler),
            MessageHandler(filters.TEXT & ~filters.COMMAND, start),
        ],
        states={
            CHOOSE_CATEGORY: [
                MessageHandler(filters.Regex("^(اشتراك شهري)$"), monthly_subscribe_handler),
                MessageHandler(filters.Regex("^(عن المنصة)$"), main_menu_handler),
                MessageHandler(filters.TEXT & ~filters.COMMAND, category_handler),
                MessageHandler(filters.Regex("^(القائمة الرئيسية)$"), main_menu_handler),
            ],
            CHOOSE_QUESTION: [
                MessageHandler(filters.Regex("^[0-9]+$"), question_number_handler),
                MessageHandler(filters.Regex("^(رجوع|القائمة الرئيسية)$"), main_menu_handler),
            ],
            WAIT_PAYMENT: [
                CallbackQueryHandler(payment_handler),
                MessageHandler(filters.Regex("^(رجوع|القائمة الرئيسية)$"), main_menu_handler),
            ],
            SUBSCRIBE_CONFIRM: [
                CallbackQueryHandler(confirm_subscription_handler),
                MessageHandler(filters.Regex("^(رجوع|القائمة الرئيسية)$"), main_menu_handler),
            ],
            MAIN_MENU: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu_handler)
            ]
        },
        fallbacks=[
            MessageHandler(filters.Regex("^(القائمة الرئيسية)$"), main_menu_handler),
            CommandHandler("start", start)
        ],
        allow_reentry=True
    )
    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(admin_action_handler, pattern="^(approve_sub_|reject_sub_).+"))
    app.run_polling()

if __name__ == "__main__":
    main()