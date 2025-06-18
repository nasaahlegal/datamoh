from telegram import Update
from telegram.ext import ContextTypes
from config import (
    Q_DATA, QUESTION_PRICE, FREE_QUESTIONS_LIMIT,
    ABOUT_MSG, WELCOME_MSG, SINGLE_PAY_MSG, ADMIN_TELEGRAM_ID
)
from keyboards import (
    get_lawyer_platform_markup, get_back_main_markup,
    get_free_confirm_markup, get_payment_reply_markup, get_about_markup,
    get_pay_confirm_markup
)
from users import (
    create_or_get_user, get_user,
    decrement_free_questions, is_subscribed
)
from states_enum import States

from utils.rate_limit import rate_limit

@rate_limit(30)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    create_or_get_user(user.id, user.username, user.full_name)
    await update.message.reply_text(
        WELCOME_MSG,
        reply_markup=get_lawyer_platform_markup(Q_DATA),
        protect_content=True
    )
    return States.CATEGORY.value

@rate_limit(30)
async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👇 اختر القسم المناسب من القائمة للبدء:",
        reply_markup=get_lawyer_platform_markup(Q_DATA),
        protect_content=True
    )
    return States.CATEGORY.value

@rate_limit(30)
async def lawyer_platform_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "للدخول إلى منصة محامي.كوم يرجى الضغط على الرابط التالي:\n\n"
        "@mohamy_law_bot",
        protect_content=True
    )
    return States.CATEGORY.value

@rate_limit(30)
async def about_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        ABOUT_MSG,
        reply_markup=get_about_markup(),
        protect_content=True
    )
    return States.CATEGORY.value

@rate_limit(30)
async def subscription_handler_limit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from handlers.payment import subscription_handler
    return await subscription_handler(update, context)

def get_answer(question_text):
    for cat, items in Q_DATA.items():
        for entry in items:
            if entry["question"] == question_text:
                return entry["answer"]
    return "لا توجد إجابة مسجلة لهذا السؤال."

async def category_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "اشتراك شهري":
        return await subscription_handler_limit(update, context)  # هنا الحماية فقط على هذا الزر
    if text == "عن المنصة":
        return await about_handler(update, context)  # الحماية هنا فقط
    if text in Q_DATA:
        context.user_data["category"] = text
        questions = [e["question"] for e in Q_DATA[text]]
        context.user_data["questions"] = questions
        numbered = "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])
        await update.message.reply_text(
            f"الأسئلة المتوفرة ضمن قسم [{text}]:\n\n{numbered}\n\n"
            "أرسل رقم السؤال للاطلاع على جوابه، أو أرسل (رجوع) أو (القائمة الرئيسية) للعودة.",
            reply_markup=get_back_main_markup(),
            protect_content=True
        )
        return States.QUESTION.value
    await update.message.reply_text(
        "يرجى اختيار تصنيف صحيح.",
        reply_markup=get_lawyer_platform_markup(Q_DATA),
        protect_content=True
    )
    return States.CATEGORY.value

async def question_number_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    questions = context.user_data.get("questions", [])
    try:
        idx = int(update.message.text) - 1
        if idx < 0 or idx >= len(questions):
            raise Exception()
    except Exception:
        await update.message.reply_text(
            "الرجاء إرسال رقم صحيح من القائمة.",
            reply_markup=get_back_main_markup(),
            protect_content=True
        )
        return States.QUESTION.value

    question = questions[idx]
    context.user_data["pending_answer"] = question

    if is_subscribed(user.id):
        answer = get_answer(question)
        await update.message.reply_text(
            f"الإجابة:\n{answer}",
            reply_markup=get_lawyer_platform_markup(Q_DATA),
            protect_content=True
        )
        return States.CATEGORY.value

    user_info = get_user(user.id)
    if user_info["free_questions_left"] > 0:
        await update.message.reply_text(
            f"لديك {user_info['free_questions_left']} سؤال مجاني متبقٍ.\n"
            "هل ترغب باستخدام سؤال مجاني للحصول على الجواب؟",
            reply_markup=get_free_confirm_markup(),
            protect_content=True
        )
        context.user_data["awaiting_free_answer"] = True
        return States.FREE_OR_SUB_CONFIRM.value

    # يطلب موافقة المستخدم أولاً على الدفع
    await update.message.reply_text(
        f"طريقة الدفع: عبر تطبيق كي المدعوم من قبل مصرف الرافدين.\n"
        f"المبلغ: {QUESTION_PRICE:,} دينار عراقي.\n"
        "هل تقبل الدفع للإجابة على هذا السؤال؟",
        reply_markup=get_pay_confirm_markup(),
        protect_content=True
    )
    context.user_data["awaiting_pay_confirm"] = True
    return "PAY_CONFIRM"

async def pay_confirm_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "نعم" and context.user_data.get("awaiting_pay_confirm"):
        await update.message.reply_text(
            SINGLE_PAY_MSG,
            reply_markup=get_payment_reply_markup(),
            protect_content=True
        )
        context.user_data["payment_type"] = "question"
        context.user_data.pop("awaiting_pay_confirm", None)
        return States.PAYMENT.value
    elif text in ["لا", "رجوع"]:
        context.user_data.pop("awaiting_pay_confirm", None)
        return await main_menu_handler(update, context)

async def confirm_free_or_sub_use_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_info = get_user(user.id)
    pending_answer = context.user_data.get("pending_answer")
    text = update.message.text

    if text == "نعم" and context.user_data.get("awaiting_free_answer"):
        decrement_free_questions(user.id)
        left = user_info["free_questions_left"] - 1
        answer = get_answer(pending_answer)
        await update.message.reply_text(
            f"الإجابة:\n{answer}\n\n(تبقى لديك {left} سؤال مجاني)",
            reply_markup=get_lawyer_platform_markup(Q_DATA),
            protect_content=True
        )
        context.user_data.pop("awaiting_free_answer", None)
        return States.CATEGORY.value
    elif text == "رجوع":
        return await back_to_questions_handler(update, context)
    elif text == "القائمة الرئيسية":
        return await main_menu_handler(update, context)
    else:
        await update.message.reply_text(
            "يرجى الاختيار من الأزرار المتوفرة فقط.",
            reply_markup=get_free_confirm_markup(),
            protect_content=True
        )
        return States.FREE_OR_SUB_CONFIRM.value

async def back_to_questions_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cat = context.user_data.get("category")
    questions = [e["question"] for e in Q_DATA.get(cat, [])]
    numbered = "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])
    await update.message.reply_text(
        f"الأسئلة المتوفرة ضمن قسم [{cat}]:\n\n{numbered}\n\n"
        "أرسل رقم السؤال للاطلاع على جوابه، أو أرسل (رجوع) أو (القائمة الرئيسية) للعودة.",
        reply_markup=get_back_main_markup(),
        protect_content=True
    )
    context.user_data.pop("awaiting_free_answer", None)
    return States.QUESTION.value

async def spam_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚫 لا تقبل الروابط أو الرسائل المباشرة، يرجى استخدام أزرار البوت فقط.",
        protect_content=True
    )
    return