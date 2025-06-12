from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ConversationHandler, CallbackQueryHandler, filters
)
from handlers import (
    start, category_handler, question_handler,
    payment_handler, subscription_paid, error_handler
)
from keyboards import MAIN_MENU
from config import TOKEN
from states_enum import States

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            States.CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, category_handler)],
            States.QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, question_handler)],
            States.PAYMENT: [CallbackQueryHandler(payment_handler, pattern="^paid$")],
            States.SUBSCRIBE: [CallbackQueryHandler(subscription_paid, pattern="^sub_paid$")]
        },
        fallbacks=[MessageHandler(filters.Regex("^العودة إلى القائمة الرئيسية$"), start)],
    )
    app.add_handler(conv_handler)
    app.add_error_handler(error_handler)
    app.run_polling()

if __name__ == '__main__':
    main()