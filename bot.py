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
from admin_handlers import (
    admin_add_question, admin_update_question, admin_delete_question, admin_list_questions
)
from config import TOKEN, ADMIN_TELEGRAM_ID
from users import init_users_db
from questions_db import init_questions_db

(
    CHOOSE_CATEGORY,
    CHOOSE_QUESTION,
    WAIT_PAYMENT,
    FREE_OR_SUB_CONFIRM,
    SUBSCRIPTION_FLOW
) = range(5)

def main():
    # تهيئة قواعد البيانات (مرة واحدة فقط، أو اتركها هنا فهي تتحقق تلقائياً)
    init_users_db()
    init_questions_db()

    app = ApplicationBuilder().token(TOKEN).build()

    # أوامر الأدمن لإدارة الأسئلة
    app.add_handler(CommandHandler("addq", admin_add_question, filters=filters.User(ADMIN_TELEGRAM_ID)))
    app.add_handler(CommandHandler("updateq", admin_update_question, filters=filters.User(ADMIN_TELEGRAM_ID)))
    app.add_handler(CommandHandler("delq", admin_delete_question, filters=filters.User(ADMIN_TELEGRAM_ID)))
    app.add_handler(CommandHandler("listq", admin_list_questions, filters=filters.User(ADMIN_TELEGRAM_ID)))

    # أوامر الأدمن الأخرى
    app.add_handler(CommandHandler("admin", admin_stats, filters=filters.User(ADMIN_TELEGRAM_ID)))
    app.add_handler(CommandHandler("subs", admin_subs, filters=filters.User(ADMIN_TELEGRAM_ID)))
    app.add_handler(MessageHandler(filters.Regex("^[0-9]+$") & filters.User(ADMIN_TELEGRAM_ID), admin_subscription_select))
    app.add_handler(CallbackQueryHandler(admin_subs_callback, pattern=r"^(extend|delete)_[0-9]+|subs_back$"))
    app.add_handler(CallbackQueryHandler(handle_admin_callback, pattern=r"^(accept|reject)_\d+$"))

    # المحادثة الرئيسية للمستخدمين
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
            # أي رسالة غير مفهومة ترجع المستخدم للقائمة الرئيسية
            MessageHandler(filters.ALL, main_menu_handler),
        ],
        allow_reentry=True
    )
    
    app.add_handler(conv)
    app.run_polling()

if __name__ == "__main__":
    main()