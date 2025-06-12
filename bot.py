from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ConversationHandler, CallbackQueryHandler, filters
)
from handlers import (
    start, category_handler, question_handler,
    payment_handler, back_handler, admin_action_handler
)
from config import TOKEN
from users import init_users_db

CHOOSE_CATEGORY, CHOOSE_QUESTION, WAIT_PAYMENT = range(3)

def main():
    init_users_db()
    app = ApplicationBuilder().token(TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start), MessageHandler(filters.TEXT & ~filters.COMMAND, start)],
        states={
            CHOOSE_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, category_handler)],
            CHOOSE_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, question_handler)],
            WAIT_PAYMENT: [CallbackQueryHandler(payment_handler)]
        },
        fallbacks=[MessageHandler(filters.Regex("رجوع"), back_handler)],
    )
    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(admin_action_handler, pattern="^(approve_sub_|reject_sub_).+"))
    app.run_polling()

if __name__ == "__main__":
    main()