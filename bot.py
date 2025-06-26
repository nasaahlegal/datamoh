from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ConversationHandler, CallbackQueryHandler, filters
)
from config import TOKEN, ADMIN_TELEGRAM_ID, Q_DATA
from handlers.admin import (
    admin_stats, admin_subs, report_subscriptions,
    admin_subscription_select, admin_subs_callback, handle_admin_callback,
    show_admin_log
)
from handlers.user import (
    start, main_menu_handler, category_handler, question_number_handler,
    confirm_free_or_sub_use_handler, back_to_questions_handler,
    lawyer_platform_handler, spam_handler, pay_confirm_handler,
    choose_payment_method_handler, subcategory_handler
)
from handlers.payment import (
    subscription_handler, subscription_confirm, payment_handler
)
from handlers.electronic_payment import electronic_payment_handler
from states_enum import States
from users import init_users_db

def main():
    init_users_db()
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("admin", admin_stats))
    app.add_handler(CommandHandler("subs", admin_subs))
    app.add_handler(CommandHandler("report", report_subscriptions))
    app.add_handler(CommandHandler("show_admin_log", show_admin_log))

    app.add_handler(
        MessageHandler(filters.Regex("^[0-9]+$") & filters.User(ADMIN_TELEGRAM_ID), admin_subscription_select)
    )
    app.add_handler(
        CallbackQueryHandler(admin_subs_callback, pattern=r"^(extend|delete)_[0-9]+|subs_back$")
    )
    app.add_handler(
        CallbackQueryHandler(handle_admin_callback, pattern=r"^(accept|reject)_(sub|question)_\d+$")
    )

    conv = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            MessageHandler(filters.Regex("^(القائمة الرئيسية)$"), main_menu_handler),
            MessageHandler(filters.Regex("^(العودة إلى منصة محاميكم)$"), lawyer_platform_handler),
        ],
        states={
            States.CATEGORY.value: [
                MessageHandler(filters.Regex("^(عن المنصة|اشتراك شهري|العودة إلى منصة محاميكم|القائمة الرئيسية)$"), category_handler),
                MessageHandler(filters.TEXT & ~filters.COMMAND, category_handler),
            ],
            "SUBCATEGORY": [
                MessageHandler(filters.TEXT & ~filters.COMMAND, subcategory_handler),
            ],
            States.QUESTION.value: [
                MessageHandler(filters.Regex("^[0-9]+$"), question_number_handler),
                MessageHandler(filters.Regex("^(رجوع|القائمة الرئيسية)$"), main_menu_handler),
            ],
            "CHOOSE_PAYMENT_METHOD": [
                MessageHandler(filters.Regex("^(التحويل اليدوي|الدفع الإلكتروني|رجوع|القائمة الرئيسية)$"), choose_payment_method_handler),
            ],
            "PAY_CONFIRM": [
                MessageHandler(filters.Regex("^(نعم|لا|رجوع)$"), pay_confirm_handler),
            ],
            States.FREE_OR_SUB_CONFIRM.value: [
                MessageHandler(filters.Regex("^(نعم)$"), confirm_free_or_sub_use_handler),
                MessageHandler(filters.Regex("^(رجوع)$"), back_to_questions_handler),
                MessageHandler(filters.Regex("^(القائمة الرئيسية)$"), main_menu_handler),
            ],
            States.PAYMENT.value: [
                MessageHandler(filters.Regex("^(تم التحويل|الغاء)$"), payment_handler),
            ],
            States.SUBSCRIBE.value: [
                MessageHandler(filters.Regex("^(موافق|رجوع)$"), subscription_confirm),
            ],
        },
        fallbacks=[
            MessageHandler(filters.Regex("^(القائمة الرئيسية)$"), main_menu_handler),
            MessageHandler(filters.Regex("^(العودة إلى منصة محاميكم)$"), lawyer_platform_handler),
            CommandHandler("start", start),
            MessageHandler(filters.ALL, main_menu_handler),
        ],
        allow_reentry=True
    )
    app.add_handler(conv)

    app.add_handler(MessageHandler(filters.Entity("url"), spam_handler))

    app.run_polling()

if __name__ == "__main__":
    main()