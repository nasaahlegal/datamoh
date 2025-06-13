from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from config import (
    CATEGORIES, ANSWERS, FREE_QUESTIONS_LIMIT, QUESTION_PRICE,
    SINGLE_PAY_MSG, ADMIN_TELEGRAM_ID, ADMIN_USERNAME, SUPPORT_USERNAME,
    ABOUT_MSG
)
from keyboards import (
    get_main_menu_markup, get_payment_reply_markup,
    get_back_main_markup, get_about_markup, get_free_confirm_markup
)
from users import (
    create_or_get_user, decrement_free_questions,
    get_user
)
import time

CHOOSE_CATEGORY, CHOOSE_QUESTION, WAIT_PAYMENT, MAIN_MENU, FREE_OR_SUB_CONFIRM = range(5)

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
        context.user_data["questions"] = questions
        numbered = "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])
        await update.message.reply_text(
            f"الأسئلة المتوفرة ضمن قسم [{cat}]:\n\n{numbered}\n\n"
            "أرسل رقم السؤال للاطلاع على جوابه، أو أرسل (رجوع) أو (القائمة الرئيسية) للعودة.",
            reply_markup=get_back_main_markup()
        )
        return CHOOSE_QUESTION
    elif cat == "عن المنصة":
        await update.message.reply_text(
            ABOUT_MSG,
            reply_markup=get_about_markup()
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
            reply_markup=get_back_main_markup()
        )
        return CHOOSE_QUESTION
    question = questions[idx]
    context.user_data["pending_answer"] = question

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
        return WAIT_PAYMENT

async def confirm_free_or_sub_use_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_info = get_user(user.id)
    pending_answer = context.user_data.get("pending_answer")

    if update.message.text == "نعم" and context.user_data.get("awaiting_free_answer"):
        decrement_free_questions(user.id)
        left = user_info['free_questions_left'] - 1
        await update.message.reply_text(
            f"الإجابة:\n{ANSWERS.get(pending_answer, 'لا توجد إجابة مسجلة لهذا السؤال.')}\n\n(تبقى لديك {left} سؤال مجاني)",
            reply_markup=get_main_menu_markup(CATEGORIES)
        )
        context.user_data.pop("awaiting_free_answer", None)
        return CHOOSE_CATEGORY

    elif update.message.text == "رجوع":
        cat = context.user_data.get("category")
        questions = CATEGORIES.get(cat, [])
        context.user_data["questions"] = questions
        numbered = "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])
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
    questions = CATEGORIES.get(cat, [])
    context.user_data["questions"] = questions
    numbered = "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])
    await update.message.reply_text(
        f"الأسئلة المتوفرة ضمن قسم [{cat}]:\n\n{numbered}\n\n"
        "أرسل رقم السؤال للاطلاع على جوابه، أو أرسل (رجوع) أو (القائمة الرئيسية) للعودة.",
        reply_markup=get_back_main_markup()
    )
    context.user_data.pop("awaiting_free_answer", None)
    return CHOOSE_QUESTION

async def payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if hasattr(update, "message") and update.message is not None:
        user = update.effective_user
        text = update.message.text
        pending_answer = context.user_data.get("pending_answer", None)
        if text == "تم التحويل":
            await update.message.reply_text("تم إرسال طلبك وسيتم تفعيل الخدمة بعد التأكد من التحويل.")
            await update.get_bot().send_message(
                chat_id=ADMIN_TELEGRAM_ID,
                text=f"طلب دفع لسؤال:\nالاسم: {user.full_name}\nالمعرف: @{user.username or 'بدون'}\nID: {user.id}\nالسؤال: {pending_answer}",
            )
            context.user_data.pop("pending_answer", None)
            return ConversationHandler.END
        elif text in ["رجوع", "القائمة الرئيسية"]:
            await main_menu_handler(update, context)
            return CHOOSE_CATEGORY
        else:
            await update.message.reply_text("يرجى استخدام الأزرار فقط.", reply_markup=get_payment_reply_markup())
            return WAIT_PAYMENT