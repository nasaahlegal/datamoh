from telegram import Update
from telegram.ext import ContextTypes
from config import (
    Q_DATA, QUESTION_PRICE, FREE_QUESTIONS_LIMIT,
    ABOUT_MSG, WELCOME_MSG, SINGLE_PAY_MSG, ADMIN_TELEGRAM_ID
)
from keyboards import (
    get_main_categories_markup, get_back_main_markup,
    get_free_confirm_markup, get_payment_reply_markup, get_about_markup,
    get_pay_confirm_markup, get_choose_payment_method_markup,
    get_subcategories_markup
)
from users import (
    create_or_get_user, get_user,
    decrement_free_questions, is_subscribed
)
from states_enum import States

from utils.anti_spam import anti_spam

async def spam_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚫 لا تقبل الروابط أو الرسائل المباشرة، يرجى استخدام أزرار البوت فقط.",
        protect_content=True
    )
    return

def get_answer(question_text):
    for main_cat in Q_DATA.values():
        for sub_cat in main_cat.values():
            for entry in sub_cat:
                if entry["question"] == question_text:
                    return entry["answer"]
    return "لا توجد إجابة مسجلة لهذا السؤال."

@anti_spam()
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    create_or_get_user(user.id, user.username, user.full_name)
    await update.message.reply_text(
        WELCOME_MSG,
        reply_markup=get_main_categories_markup(),
        protect_content=True
    )
    return States.CATEGORY.value

@anti_spam()
async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👇 اختر القسم المناسب من القائمة للبدء:",
        reply_markup=get_main_categories_markup(),
        protect_content=True
    )
    return States.CATEGORY.value

@anti_spam()
async def lawyer_platform_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "للدخول إلى منصة محاميكم يرجى الضغط على الرابط التالي:\n\n"
        "@mohamy_law_bot",
        protect_content=True
    )
    return States.CATEGORY.value

@anti_spam()
async def category_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "اشتراك شهري":
        from handlers.payment import subscription_handler
        return await subscription_handler(update, context)
    if text == "عن المنصة":
        await update.message.reply_text(
            ABOUT_MSG,
            reply_markup=get_about_markup(),
            protect_content=True
        )
        return States.CATEGORY.value
    if text == "العودة إلى منصة محاميكم":
        return await lawyer_platform_handler(update, context)
    if text == "القائمة الرئيسية":
        return await main_menu_handler(update, context)

    main_categories = ["الأسرة", "مدني", "الوظيفة والعمل", "جنائي"]
    
    if text in main_categories:
        context.user_data["main_category"] = text
        subcategories = list(Q_DATA.get(text, {}).keys())
        if not subcategories:
            await update.message.reply_text(
                "لا توجد تصنيفات فرعية متاحة حالياً.",
                reply_markup=get_back_main_markup(),
                protect_content=True
            )
            return States.CATEGORY.value
        context.user_data["subcategories"] = subcategories
        await update.message.reply_text(
            f"اختر تصنيفاً فرعياً من قائمة {text}:",
            reply_markup=get_subcategories_markup(subcategories),
            protect_content=True
        )
        return "SUBCATEGORY"

    await update.message.reply_text(
        "يرجى اختيار تصنيف صحيح.",
        reply_markup=get_main_categories_markup(),
        protect_content=True
    )
    return States.CATEGORY.value

@anti_spam()
async def subcategory_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "رجوع":
        return await main_menu_handler(update, context)
    if text == "القائمة الرئيسية":
        return await main_menu_handler(update, context)

    main_category = context.user_data.get("main_category")
    if not main_category:
        return await main_menu_handler(update, context)

    subcategories = context.user_data.get("subcategories", [])
    if text not in subcategories:
        await update.message.reply_text(
            "يرجى اختيار تصنيف فرعي صحيح.",
            reply_markup=get_subcategories_markup(subcategories),
            protect_content=True
        )
        return "SUBCATEGORY"

    context.user_data["subcategory"] = text
    questions_data = Q_DATA.get(main_category, {}).get(text, [])
    questions = [q["question"] for q in questions_data]
    if not questions:
        await update.message.reply_text(
            "لا توجد أسئلة في هذا التصنيف حالياً.",
            reply_markup=get_subcategories_markup(subcategories),
            protect_content=True
        )
        return "SUBCATEGORY"

    context.user_data["questions"] = questions
    numbered = "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])
    await update.message.reply_text(
        f"الأسئلة المتوفرة في تصنيف {text}:\n\n{numbered}\n\n"
        "أرسل رقم السؤال للاطلاع على جوابه.",
        reply_markup=get_back_main_markup(),
        protect_content=True
    )
    return States.QUESTION.value

@anti_spam()
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
            reply_markup=get_main_categories_markup(),
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

    await update.message.reply_text(
        "اختر طريقة الدفع المناسبة:",
        reply_markup=get_choose_payment_method_markup(),
        protect_content=True
    )
    context.user_data["awaiting_payment_method"] = True
    return "CHOOSE_PAYMENT_METHOD"

@anti_spam()
async def choose_payment_method_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if context.user_data.get("awaiting_payment_method"):
        if text == "التحويل اليدوي":
            from keyboards import get_pay_confirm_markup
            await update.message.reply_text(
                f"طريقة الدفع: عبر تطبيق كي المدعوم من قبل مصرف الرافدين.\n"
                f"المبلغ: {QUESTION_PRICE:,} دينار عراقي.\n"
                "هل تقبل الدفع للإجابة على هذا السؤال؟",
                reply_markup=get_pay_confirm_markup(),
                protect_content=True
            )
            context.user_data["awaiting_pay_confirm"] = True
            context.user_data.pop("awaiting_payment_method", None)
            return "PAY_CONFIRM"
        elif text == "الدفع الإلكتروني":
            from handlers.electronic_payment import electronic_payment_handler
            await electronic_payment_handler(update, context)
            return "CHOOSE_PAYMENT_METHOD"
        elif text in ["رجوع", "القائمة الرئيسية"]:
            context.user_data.pop("awaiting_payment_method", None)
            return await main_menu_handler(update, context)
        else:
            from keyboards import get_choose_payment_method_markup
            await update.message.reply_text(
                "يرجى اختيار طريقة الدفع من الأزرار فقط.",
                reply_markup=get_choose_payment_method_markup(),
                protect_content=True
            )
            return "CHOOSE_PAYMENT_METHOD"

@anti_spam()
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

@anti_spam()
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
            reply_markup=get_main_categories_markup(),
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

@anti_spam()
async def back_to_questions_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    main_category = context.user_data.get("main_category")
    subcategory = context.user_data.get("subcategory")
    if not main_category or not subcategory:
        return await main_menu_handler(update, context)
    
    questions_data = Q_DATA.get(main_category, {}).get(subcategory, [])
    questions = [q["question"] for q in questions_data]
    numbered = "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])
    await update.message.reply_text(
        f"الأسئلة المتوفرة في تصنيف {subcategory}:\n\n{numbered}\n\n"
        "أرسل رقم السؤال للاطلاع على جوابه، أو أرسل (رجوع) أو (القائمة الرئيسية) للعودة.",
        reply_markup=get_back_main_markup(),
        protect_content=True
    )
    context.user_data.pop("awaiting_free_answer", None)
    return States.QUESTION.value