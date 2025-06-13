from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ConversationHandler, filters
)
from handlers import (
    start, main_menu_handler, category_handler, question_number_handler,
    confirm_free_or_sub_use_handler, payment_handler, back_to_questions_handler
)
from config import TOKEN
from users import init_users_db

(
    CHOOSE_CATEGORY,
    CHOOSE_QUESTION,
    WAIT_PAYMENT,
    MAIN_MENU,
    FREE_OR_SUB_CONFIRM
) = range(5)

def main():
    init_users_db()
    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            MessageHandler(filters.Regex("^(القائمة الرئيسية)$"), main_menu_handler),
        ],
        states={
            CHOOSE_CATEGORY: [
                MessageHandler(filters.Regex("^عن المنصة$"), category_handler),
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
                MessageHandler(filters.Regex("^(تم التحويل)$"), payment_handler),
                MessageHandler(filters.Regex("^(رجوع|القائمة الرئيسية)$"), main_menu_handler),
            ],
        },
        fallbacks=[
            MessageHandler(filters.Regex("^(القائمة الرئيسية)$"), main_menu_handler),
            CommandHandler("start", start)
        ],
        allow_reentry=True
    )
    app.add_handler(conv)
    app.run_polling()

if __name__ == "__main__":
    main()