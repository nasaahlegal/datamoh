import logging
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ConversationHandler, filters, CallbackQueryHandler
)
from config import TOKEN, ADMIN_TELEGRAM_ID
from users import init_users_db
from handlers import (
    start, main_menu_handler, category_handler, question_number_handler,
    confirm_free_or_sub_use_handler, payment_handler, back_to_questions_handler,
    subscription_handler, subscription_confirm, lawyer_platform_handler
)
from admin_handlers import (
    admin_menu, admin_stats, admin_subs, admin_subscription_select,
    admin_subs_callback, handle_admin_callback,
    admin_manage_questions, admin_panel_router, admin_category_select,
    admin_question_router, admin_new_question, admin_new_answer,
    admin_manage_action, admin_edit_question, admin_edit_answer
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

(
    CHOOSE_CATEGORY,
    CHOOSE_QUESTION,
    WAIT_PAYMENT,
    FREE_OR_SUB_CONFIRM,
    SUBSCRIPTION_FLOW
) = range(5)

def main():
    init_users_db()
    app = ApplicationBuilder().token(TOKEN).build()

    # أوامر الأدمن
    app.add_handler(CommandHandler("admin", admin_menu, filters=filters.User(ADMIN_TELEGRAM_ID)))
    app.add_handler(CommandHandler("stats", admin_stats, filters=filters.User(ADMIN_TELEGRAM_ID)))
    app.add_handler(CommandHandler("subs", admin_subs, filters=filters.User(ADMIN_TELEGRAM_ID)))
    app.add_handler(CommandHandler("manage_questions", admin_manage_questions, filters=filters.User(ADMIN_TELEGRAM_ID)))

    # أزرار لوحة الأدمن
    app.add_handler(MessageHandler(filters.Regex(r"^(إدارة المشتركين|إدارة الأسئلة|القائمة الرئيسية)$") & filters.User(ADMIN_TELEGRAM_ID), admin_panel_router))

    # إدارة المشتركين
    app.add_handler(MessageHandler(filters.Regex("^[0-9]+$") & filters.User(ADMIN_TELEGRAM_ID), admin_subscription_select))
    app.add_handler(CallbackQueryHandler(admin_subs_callback, pattern=r"^(extend|delete)_[0-9]+|subs_back$"))
    app.add_handler(CallbackQueryHandler(handle_admin_callback, pattern=r"^(accept|reject)_\d+$"))

    # إدارة الأسئلة
    app.add_handler(MessageHandler(filters.Regex(r"^(أحوال شخصية|عقارات|عمل|جنائي|مرور|أخرى)$") & filters.User(ADMIN_TELEGRAM_ID), admin_category_select))
    app.add_handler(MessageHandler(filters.Regex(r"^(إضافة سؤال جديد|رجوع|.*)$") & filters.User(ADMIN_TELEGRAM_ID), admin_question_router))
    app.add_handler(MessageHandler(filters.TEXT & filters.User(ADMIN_TELEGRAM_ID), admin_new_question))
    app.add_handler(MessageHandler(filters.TEXT & filters.User(ADMIN_TELEGRAM_ID), admin_new_answer))
    app.add_handler(MessageHandler(filters.Regex(r"^(تعديل السؤال|حذف السؤال|رجوع)$") & filters.User(ADMIN_TELEGRAM_ID), admin_manage_action))
    app.add_handler(MessageHandler(filters.TEXT & filters.User(ADMIN_TELEGRAM_ID), admin_edit_question))
    app.add_handler(MessageHandler(filters.TEXT & filters.User(ADMIN_TELEGRAM_ID), admin_edit_answer))

    # ConversationHandler الأساسي للمستخدم
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
    app.run_polling()

if __name__ == "__main__":
    main()