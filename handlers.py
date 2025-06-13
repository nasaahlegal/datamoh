from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from config import (
    CATEGORIES, ANSWERS, FREE_QUESTIONS_LIMIT, QUESTION_PRICE,
    SUBSCRIPTION_PRICE, SUBSCRIPTION_DAYS, PAY_MSG, SINGLE_PAY_MSG,
    ADMIN_TELEGRAM_ID, ADMIN_USERNAME, SUPPORT_USERNAME, ABOUT_MSG,
    PAY_ACCOUNT_MSG
)
from keyboards import (
    get_categories_markup, get_main_menu_markup, get_payment_markup,
    get_subscribe_confirm_markup, get_admin_payment_action_markup
)
from users import (
    init_users_db, create_or_get_user, decrement_free_questions, reset_free_questions,
    set_subscription, is_subscribed, get_user, get_subscription_expiry
)
import time

# Conversation states
CHOOSE_CATEGORY, CHOOSE_QUESTION, WAIT_PAYMENT, MAIN_MENU, SUBSCRIBE_CONFIRM = range(5)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    create_or_get_user(user.id, user.username, user.full_name)
    await update.message.reply_text(
        "مرحباً بك في المنصة القانونية الذكية من محامي.كوم! اختر القسم:",
        reply_markup=get_main_menu_markup(CATEGORIES)
    )
    return CHOOSE_CATEGORY

async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "اختر القسم المناسب:",
        reply_markup=get_main_menu_markup(CATEGORIES)
    )
    return CHOOSE_CATEGORY

async def category_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    create_or_get_user(user.id, user.username, user.full_name)
    cat = update.message.text
    if cat in CATEGORIES:
        context.user_data["category"] = cat
        questions = CATEGORIES[cat]
        numbered = "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])
        await update.message.reply_text(
            f"الأسئلة المتوفرة ضمن قسم [{cat}]:\n\n{numbered}\n\n"
            "أرسل رقم السؤال للاطلاع على جوابه، أو أرسل (رجوع) أو (القائمة الرئيسية) للعودة.",
            reply_markup=get_main_menu_markup(CATEGORIES)
        )
        context.user_data["questions"] = questions
        return CHOOSE_QUESTION
    elif cat == "اشتراك شهري":
        # الانتقال لخطوة تأكيد الاشتراك
        await update.message.reply_text(
            PAY_MSG,
            reply_markup=get_subscribe_confirm_markup()
        )
        return SUBSCRIBE_CONFIRM
    elif cat == "عن المنصة":
        await update.message.reply_text(
            ABOUT_MSG,
            reply_markup=get_main_menu_markup(CATEGORIES)
        )
        return CHOOSE_CATEGORY
    else:
        await update.message.reply_text(
            "يرجى اختيار تصنيف صحيح.",
            reply_markup=get_main_menu_markup(CATEGORIES)
        )
        return CHOOSE_CATEGORY

async def question_number_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_info = get_user(user.id)
    questions = context.user_data.get("questions", [])
    try:
        idx = int(update.message.text) - 1
        if idx < 0 or idx >= len(questions):
            raise Exception()
    except Exception:
        await update.message.reply_text(
            "الرجاء إرسال رقم صحيح من القائمة.",
            reply_markup=get_main_menu_markup(CATEGORIES)
        )
        return CHOOSE_QUESTION
    question = questions[idx]
    context.user_data["pending_answer"] = question

    if is_subscribed(user.id):
        expiry = get_subscription_expiry(user.id)
        days_left = int((expiry - int(time.time())) / (24*60*60))
        await update.message.reply_text(
            f"لديك اشتراك فعال. متبقي لك {days_left} يوم من الاشتراك.\n"
            "هل تريد الحصول على الجواب الآن؟\n"
            "ارسل (نعم) أو (رجوع) أو (القائمة الرئيسية)."
        )
        context.user_data["awaiting_subscribed_answer"] = True
        return CHOOSE_QUESTION

    if user_info["free_questions_left"] > 0:
        await update.message.reply_text(
            f"لديك {user_info['free_questions_left']} سؤال مجاني متبقٍ.\n"
            "هل ترغب باستخدام سؤال مجاني للحصول على الجواب؟\n"
            "ارسل (نعم) أو (رجوع) أو (القائمة الرئيسية)."
        )
        context.user_data["awaiting_free_answer"] = True
        return CHOOSE_QUESTION
    else:
        await update.message.reply_text(
            SINGLE_PAY_MSG,
            reply_markup=get_payment_markup()
        )
        return WAIT_PAYMENT

async def payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    await query.answer()
    if query.data == "paid":
        # إشعار للأدمن مع أزرار
        pending_answer = context.user_data.get("pending_answer", None)
        await query.message.reply_text("تم إرسال طلبك وسيتم تفعيل الخدمة بعد التأكد من التحويل.")
        await context.bot.send_message(
            chat_id=ADMIN_TELEGRAM_ID,
            text=f"طلب دفع لسؤال:\nالاسم: {user.full_name}\nالمعرف: @{user.username or 'بدون'}\nID: {user.id}\nالسؤال: {pending_answer}",
            reply_markup=get_admin_payment_action_markup(f"{user.id}_q")
        )
        context.user_data.pop("pending_answer", None)
        return ConversationHandler.END
    elif query.data == "back":
        await query.message.reply_text(
            "تم الرجوع إلى القائمة الرئيسية.",
            reply_markup=get_main_menu_markup(CATEGORIES)
        )
        return CHOOSE_CATEGORY
    else:
        await query.message.reply_text("حدث خطأ! يرجى المحاولة مرة أخرى.")
        return ConversationHandler.END

async def monthly_subscribe_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        PAY_MSG,
        reply_markup=get_subscribe_confirm_markup()
    )
    return SUBSCRIBE_CONFIRM

async def confirm_subscription_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    await query.answer()
    if query.data == "sub_accept":
        await query.message.reply_text(
            PAY_ACCOUNT_MSG,
            reply_markup=get_payment_markup()
        )
        context.user_data["awaiting_subscription"] = True
        return WAIT_PAYMENT
    elif query.data == "sub_cancel":
        await query.message.reply_text(
            "تم إلغاء الاشتراك. عد إلى القائمة الرئيسية.",
            reply_markup=get_main_menu_markup(CATEGORIES)
        )
        return CHOOSE_CATEGORY

async def admin_action_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.from_user.id != ADMIN_TELEGRAM_ID:
        await query.answer("غير مصرح لك بهذه العملية.", show_alert=True)
        return
    data = query.data
    await query.answer()
    if data.startswith("approve_sub_"):
        id_part = data.replace("approve_sub_", "")
        if "_q" in id_part:
            user_id = int(id_part.split("_")[0])
            user = get_user(user_id)
            question = None  # يمكن توسيع منطق الربط مع السؤال
            await context.bot.send_message(
                chat_id=user_id,
                text="تم تأكيد الدفع. سيتم إرسال الجواب إليك خلال دقيقة.\n"
                     f"للدعم: @{SUPPORT_USERNAME}"
            )
            await query.edit_message_text("✅ تم تأكيد دفع سؤال مفرد.")
        else:
            user_id = int(id_part)
            user = get_user(user_id)
            set_subscription(user_id, user["username"], user["full_name"])
            reset_free_questions(user_id)
            await context.bot.send_message(
                chat_id=user_id,
                text=f"تم تفعيل اشتراكك الشهري! يمكنك الآن طرح عدد غير محدود من الأسئلة لمدة {SUBSCRIPTION_DAYS} يوم.\n"
                     f"للدعم: @{SUPPORT_USERNAME}"
            )
            await query.edit_message_text("✅ تم تفعيل الاشتراك الشهري.")
    elif data.startswith("reject_sub_"):
        id_part = data.replace("reject_sub_", "")
        user_id = int(id_part.split("_")[0])
        await context.bot.send_message(
            chat_id=user_id,
            text=f"لم يتم قبول طلب الدفع. إذا كان هنالك خطأ راسل الدعم: @{SUPPORT_USERNAME}"
        )
        await query.edit_message_text("❌ تم رفض الاشتراك/الدفع لهذا المستخدم.")

async def back_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "اختر القسم المناسب:",
        reply_markup=get_main_menu_markup(CATEGORIES)
    )
    return CHOOSE_CATEGORY