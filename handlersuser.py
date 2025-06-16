from telegram import Update
from telegram.ext import ContextTypes
from config import Q_DATA, QUESTION_PRICE
from keyboards import (
    get_lawyer_platform_markup, get_back_main_markup,
    get_free_confirm_markup, get_payment_reply_markup
)
from users import (
    create_or_get_user, get_user,
    decrement_free_questions, is_subscribed
)
from states_enum import States

async def spam_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚫 لا تقبل الروابط أو الرسائل المباشرة، يرجى استخدام أزرار البوت فقط.",
        protect_content=True
    )
    return  # يمنع معالجة الرسالة لاحقاً

def get_answer(question_text):
    for cat, items in Q_DATA.items():
        for entry in items:
            if entry["question"] == question_text:
                return entry["answer"]
    return "لا توجد إجابة مسجلة لهذا السؤال."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    create_or_get_user(user.id, user.username, user.full_name)
    await update.message.reply_text(
        "👋 أهلاً بك في المنصة القانونية الذكية!",
        reply_markup=get_lawyer_platform_markup(Q_DATA),
        protect_content=True
    )
    return States.CATEGORY.value

async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👇 اختر التصنيف:",
        reply_markup=get_lawyer_platform_markup(Q_DATA),
        protect_content=True
    )
    return States.CATEGORY.value

async def category_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text in Q_DATA:
        context.user_data["category"] = text
        questions = [e["question"] for e in Q_DATA[text]]
        context.user_data["questions"] = questions
        numbered = "\n".join(f"{i+1}. {q}" for i, q in enumerate(questions))
        await update.message.reply_text(
            f"أسئلة [{text}]:\n{numbered}",
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
    idx = int(update.message.text) - 1
    questions = context.user_data.get("questions", [])
    if idx < 0 or idx >= len(questions):
        await update.message.reply_text(
            "رقم غير صحيح.",
            reply_markup=get_back_main_markup(),
            protect_content=True
        )
        return States.QUESTION.value

    question = questions[idx]
    context.user_data["pending_answer"] = question

    if is_subscribed(user.id):
        answer = get_answer(question)
        await update.message.reply_text(
            f"✅ الإجابة:\n{answer}",
            reply_markup=get_lawyer_platform_markup(Q_DATA),
            protect_content=True
        )
        return States.CATEGORY.value

    user_info = get_user(user.id)
    if user_info["free_questions_left"] > 0:
        await update.message.reply_text(
            f"لديك {user_info['free_questions_left']} سؤال مجاني. استخدام مجاني؟",
            reply_markup=get_free_confirm_markup(),
            protect_content=True
        )
        return States.FREE_OR_SUB_CONFIRM.value

    await update.message.reply_text(
        f"سعر السؤال: {QUESTION_PRICE} د.ع\nيرجى التحويل ثم اضغط (تم التحويل).",
        reply_markup=get_payment_reply_markup(),
        protect_content=True
    )
    return States.PAYMENT.value

async def confirm_free_or_sub_use_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "نعم":
        user = update.effective_user
        decrement_free_questions(user.id)
        question = context.user_data.pop("pending_answer")
        answer = get_answer(question)
        await update.message.reply_text(
            f"✅ الإجابة:\n{answer}",
            reply_markup=get_lawyer_platform_markup(Q_DATA),
            protect_content=True
        )
        return States.CATEGORY.value
    return await back_to_questions_handler(update, context)

async def back_to_questions_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cat = context.user_data.get("category")
    questions = [e["question"] for e in Q_DATA.get(cat, [])]
    numbered = "\n".join(f"{i+1}. {q}" for i, q in enumerate(questions))
    await update.message.reply_text(
        f"أسئلة [{cat}]:\n{numbered}",
        reply_markup=get_back_main_markup(),
        protect_content=True
    )
    return States.QUESTION.value
