import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from config import (
    CATEGORIES, FREE_QUESTIONS_LIMIT, QUESTION_PRICE,
    SINGLE_PAY_MSG, ADMIN_TELEGRAM_ID, ADMIN_USERNAME, SUPPORT_USERNAME,
    ABOUT_MSG, SUBSCRIPTION_PRICE, PAY_ACCOUNT, PAY_MSG, WELCOME_MSG
)
from keyboards import (
    get_main_menu_markup, get_payment_reply_markup,
    get_back_main_markup, get_about_markup, get_free_confirm_markup,
    get_subscription_markup, get_admin_decision_markup, get_lawyer_platform_markup
)
from users import (
    create_or_get_user, decrement_free_questions,
    get_user, set_subscription, get_connection,
    is_subscribed
)
import questions
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

CHOOSE_CATEGORY, CHOOSE_QUESTION, WAIT_PAYMENT, FREE_OR_SUB_CONFIRM, SUBSCRIPTION_FLOW = range(5)

pending_paid_questions = {}

def get_answer_from_questions(question_text):
    for category, qlist in questions.LEGAL_QUESTIONS.items():
        for q, a in qlist:
            if q.strip() == question_text.strip():
                return a
    return "لا توجد إجابة مسجلة لهذا السؤال."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    create_or_get_user(user.id, user.username, user.full_name)
    await update.message.reply_text(
        WELCOME_MSG,
        reply_markup=get_lawyer_platform_markup(questions.LEGAL_QUESTIONS)
    )
    return CHOOSE_CATEGORY

async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👇 اختر القسم المناسب من القائمة للبدء:",
        reply_markup=get_lawyer_platform_markup(questions.LEGAL_QUESTIONS)
    )
    return CHOOSE_CATEGORY

async def lawyer_platform_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "للدخول إلى منصة محامي.كوم يرجى الضغط على الرابط التالي:\n\n"
        "@mohamy_law_bot"
    )

async def category_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    create_or_get_user(user.id, user.username, user.full_name)
    text = update.message.text

    if text == "اشتراك شهري":
        return await subscription_handler(update, context)
    elif text in questions.LEGAL_QUESTIONS:
        context.user_data["category"] = text
        qs = questions.LEGAL_QUESTIONS[text]
        context.user_data["questions"] = [q for q, _ in qs]
        numbered = "\n".join([f"{i+1}. {q}" for i, q in enumerate(context.user_data["questions"])])
        await update.message.reply_text(
            f"الأسئلة المتوفرة ضمن قسم [{text}]:\n\n{numbered}\n\n"
            "أرسل رقم السؤال للاطلاع على جوابه، أو أرسل (رجوع) أو (القائمة الرئيسية) للعودة.",
            reply_markup=get_back_main_markup()
        )
        return CHOOSE_QUESTION
    elif text == "عن المنصة":
        await update.message.reply_text(
            ABOUT_MSG,
            reply_markup=get_about_markup()
        )
        return CHOOSE_CATEGORY
    else:
        await update.message.reply_text(
            "يرجى اختيار تصنيف صحيح.",
            reply_markup=get_lawyer_platform_markup(questions.LEGAL_QUESTIONS))
        return CHOOSE_CATEGORY

async def subscription_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_info = get_user(user.id)
    if is_subscribed(user.id):
        now = int(time.time())
        days_left = int((user_info["sub_expiry"] - now) // (24*60*60))
        await update.message.reply_text(
            f"لديك اشتراك شهري فعّال بالفعل.\nعدد الأيام المتبقية: {days_left} يومًا.\n"
            "يمكنك الاستمرار في استخدام جميع ميزات المنصة.",
            reply_markup=get_lawyer_platform_markup(questions.LEGAL_QUESTIONS)
        )
        return CHOOSE_CATEGORY
    await update.message.reply_text(
        "اهلا بك في الاستشارات التلقائية لمنصة محامي.كوم\n\n"
        "يمكنك تفعيل الاشتراك الشهري لهذه الخدمة بقيمة 50,000 دينار عراقي "
        "والاستمتاع بعدد لا محدود من الاجابات التلقائية المتوفرة في هذا القسم\n\n"
        "تتم دفع رسوم الاشتراك في الوقت الحالي عبر تطبيق (كي) المدعوم من قبل مصرف الرافدين\n"
        "وسيتم تفعيل باقي الطرق قريبا\n\n"
        "للاستمرار يرجى الضغط على موافق",
        reply_markup=get_subscription_markup()
    )
    return SUBSCRIPTION_FLOW

async def subscription_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "موافق":
        await update.message.reply_text(
            "يرجى تحويل رسوم الاشتراك الى الحساب التالي:\n"
            "9916153415\n\n"
            "بعد التحويل يرجى الضغط على (تم التحويل) وسيتم تفعيل الاشتراك بعد التأكد من قبل المختص",
            reply_markup=get_payment_reply_markup()
        )
        context.user_data["subscription_request"] = True
        context.user_data["payment_type"] = "subscription"
        return WAIT_PAYMENT
    elif text == "رجوع":
        await main_menu_handler(update, context)
        return CHOOSE_CATEGORY
    else:
        await update.message.reply_text("يرجى الاختيار من الأزرار المتوفرة فقط.")
        return SUBSCRIPTION_FLOW

async def question_number_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_info = get_user(user.id)
    questions_list = context.user_data.get("questions", [])

    try:
        idx = int(update.message.text) - 1
        if idx < 0 or idx >= len(questions_list):
            await update.message.reply_text(
                "الرجاء إرسال رقم صحيح من القائمة.",
                reply_markup=get_back_main_markup()
            )
            return CHOOSE_QUESTION
    except Exception:
        await update.message.reply_text(
            "الرجاء إرسال رقم صحيح من القائمة.",
            reply_markup=get_back_main_markup()
        )
        return CHOOSE_QUESTION

    question = questions_list[idx]
    context.user_data["pending_answer"] = question
    context.user_data["pending_category"] = context.user_data.get("category", "")

    if is_subscribed(user.id):
        await update.message.reply_text(
            f"الإجابة:\n{get_answer_from_questions(question)}\n\n"
            f"(اشتراكك الشهري فعّال، متبقٍ لك {int((user_info['sub_expiry']-int(time.time()))//(24*60*60))} يوم)",
            reply_markup=get_lawyer_platform_markup(questions.LEGAL_QUESTIONS)
        )
        return CHOOSE_CATEGORY

    if user_info["free_questions_left"] > 0:
        await update.message.reply_text(
            f"لديك {user_info['free_questions_left']} سؤال مجاني متبقٍ.\n"
            "هل ترغب باستخدام سؤال مجاني للحصول على الجواب؟",
            reply_markup=get_free_confirm_markup()
        )
        context.user_data["awaiting_free_answer"] = True
        return FREE_OR_SUB_CONFIRM
    else:
        await update.message.reply_text(
            SINGLE_PAY_MSG,
            reply_markup=get_payment_reply_markup()
        )
        context.user_data["subscription_request"] = False
        context.user_data["payment_type"] = "question"
        return WAIT_PAYMENT

async def confirm_free_or_sub_use_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_info = get_user(user.id)
    pending_answer = context.user_data.get("pending_answer")

    if update.message.text == "نعم" and context.user_data.get("awaiting_free_answer"):
        decrement_free_questions(user.id)
        left = user_info['free_questions_left'] - 1
        await update.message.reply_text(
            f"الإجابة:\n{get_answer_from_questions(pending_answer)}\n\n(تبقى لديك {left} سؤال مجاني)",
            reply_markup=get_lawyer_platform_markup(questions.LEGAL_QUESTIONS)
        )
        context.user_data.pop("awaiting_free_answer", None)
        return CHOOSE_CATEGORY
    elif update.message.text == "رجوع":
        cat = context.user_data.get("category")
        qs = questions.LEGAL_QUESTIONS.get(cat, [])
        context.user_data["questions"] = [q for q, _ in qs]
        numbered = "\n".join([f"{i+1}. {q}" for i, q in enumerate(context.user_data["questions"])])
        await update.message.reply_text(
            f"الأسئلة المتوفرة ضمن قسم [{cat}]:\n\n{numbered}\n\n"
            "أرسل رقم السؤال للاطلاع على جوابه، أو أرسل (رجوع) أو (القائمة الرئيسية) للعودة.",
            reply_markup=get_back_main_markup()
        )
        context.user_data.pop("awaiting_free_answer", None)
        return CHOOSE_QUESTION
    elif update.message.text == "القائمة الرئيسية":
        return await main_menu_handler(update, context)
    else:
        await update.message.reply_text("يرجى الاختيار من الأزرار المتوفرة فقط.", reply_markup=get_free_confirm_markup())
        return FREE_OR_SUB_CONFIRM

async def back_to_questions_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cat = context.user_data.get("category")
    qs = questions.LEGAL_QUESTIONS.get(cat, [])
    context.user_data["questions"] = [q for q, _ in qs]
    numbered = "\n".join([f"{i+1}. {q}" for i, q in enumerate(context.user_data["questions"])])
    await update.message.reply_text(
        f"الأسئلة المتوفرة ضمن قسم [{cat}]:\n\n{numbered}\n\n"
        "أرسل رقم السؤال للاطلاع على جوابه، أو أرسل (رجوع) أو (القائمة الرئيسية) للعودة.",
        reply_markup=get_back_main_markup()
    )
    context.user_data.pop("awaiting_free_answer", None)
    return CHOOSE_QUESTION

async def payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text
    user_id = user.id

    if text == "تم التحويل":
        if context.user_data.get("subscription_request", False):
            await update.message.reply_text(
                "✅ تم إرسال طلب اشتراكك بنجاح!\n"
                "سيتم تفعيل الاشتراك خلال 24 ساعة بعد التحقق من التحويل.\n"
                "يمكنك متابعة استخدام البوت الآن:",
                reply_markup=get_lawyer_platform_markup(questions.LEGAL_QUESTIONS)
            )
            await update.get_bot().send_message(
                chat_id=ADMIN_TELEGRAM_ID,
                text=f"📬 طلب اشتراك جديد:\n"
                     f"👤 الاسم: {user.full_name}\n"
                     f"🔗 المعرف: @{user.username or 'بدون'}\n"
                     f"🆔 ID: {user.id}\n"
                     f"💳 المبلغ: 50,000 دينار عراقي\n"
                     f"⏳ المدة: 30 يوم",
                reply_markup=get_admin_decision_markup(user.id)
            )
            context.user_data["last_payment_type"] = "subscription"
        else:
            pending_answer = context.user_data.get("pending_answer", "سؤال غير محدد")
            pending_category = context.user_data.get("pending_category", "")
            await update.message.reply_text(
                "✅ تم إرسال طلبك بنجاح!\n"
                "سيتم الرد على سؤالك خلال 24 ساعة بعد التحقق من التحويل.\n"
                "يمكنك متابعة استخدام البوت الآن:",
                reply_markup=get_lawyer_platform_markup(questions.LEGAL_QUESTIONS)
            )
            await update.get_bot().send_message(
                chat_id=ADMIN_TELEGRAM_ID,
                text=f"📬 طلب دفع لسؤال:\n"
                     f"👤 الاسم: {user.full_name}\n"
                     f"🔗 المعرف: @{user.username or 'بدون'}\n"
                     f"🆔 ID: {user.id}\n"
                     f"❓ السؤال: {pending_answer}",
                reply_markup=get_admin_decision_markup(user.id)
            )
            pending_paid_questions[user.id] = (pending_answer, pending_category)
            context.user_data["last_payment_type"] = "question"

        context.user_data.pop("pending_answer", None)
        context.user_data.pop("pending_category", None)
        context.user_data.pop("subscription_request", None)
        return CHOOSE_CATEGORY

    elif text == "الغاء":
        await update.message.reply_text(
            "تم إلغاء عملية الدفع.\n"
            "يمكنك العودة للقائمة الرئيسية:",
            reply_markup=get_lawyer_platform_markup(questions.LEGAL_QUESTIONS)
        )
        return CHOOSE_CATEGORY

    else:
        await update.message.reply_text("يرجى استخدام الأزرار فقط.", reply_markup=get_payment_reply_markup())
        return WAIT_PAYMENT