from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from config import CATEGORIES, ANSWERS, FREE_QUESTIONS_LIMIT, QUESTION_PRICE, MONTHLY_SUBSCRIPTION_PRICE, TOKEN
from keyboards import get_categories_markup, get_questions_markup, get_payment_markup
from users_data import get_user_info, use_free_question, has_subscription, subscribe_user

CHOOSE_CATEGORY, CHOOSE_QUESTION, WAIT_PAYMENT = range(3)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "مرحباً بك في بوت الاستشارات القانونية التلقائية!\nاختر التصنيف:",
        reply_markup=get_categories_markup(CATEGORIES)
    )
    return CHOOSE_CATEGORY

async def category_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cat = update.message.text
    if cat in CATEGORIES:
        context.user_data["category"] = cat
        await update.message.reply_text("اختر السؤال:", reply_markup=get_questions_markup(CATEGORIES[cat]))
        return CHOOSE_QUESTION
    elif cat == "اشتراك شهري":
        await update.message.reply_text(
            f"قيمة الاشتراك الشهري {MONTHLY_SUBSCRIPTION_PRICE:,} دينار. بعد التحويل اضغط تم الدفع.\n"
            "يرجى التحويل إلى رقم الحساب: 9916153415\nقريباً سيتم دعم فاست باي وزين كاش وآسيا حوالة.",
            reply_markup=get_payment_markup()
        )
        context.user_data["awaiting_subscription"] = True
        return WAIT_PAYMENT
    elif cat == "حول البوت":
        await update.message.reply_text(
            "هذا بوت استشارات قانونية تلقائية. أول 3 أسئلة مجانية، وكل سؤال بعد ذلك 5000 دينار. يوجد اشتراك شهري بـ 50000 دينار لأسئلة غير محدودة.",
            reply_markup=get_categories_markup(CATEGORIES)
        )
        return CHOOSE_CATEGORY
    else:
        await update.message.reply_text("يرجى اختيار تصنيف صحيح.", reply_markup=get_categories_markup(CATEGORIES))
        return CHOOSE_CATEGORY

async def question_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    question = update.message.text
    info = get_user_info(user_id)
    if question not in ANSWERS:
        await update.message.reply_text("يرجى اختيار سؤال من القائمة.", reply_markup=get_questions_markup(CATEGORIES[context.user_data["category"]]))
        return CHOOSE_QUESTION

    if has_subscription(user_id):
        await update.message.reply_text(f"الإجابة:\n{ANSWERS[question]}", reply_markup=get_categories_markup(CATEGORIES))
        return CHOOSE_CATEGORY

    if info["free_questions_left"] > 0:
        use_free_question(user_id)
        await update.message.reply_text(
            f"الإجابة:\n{ANSWERS[question]}\n\n(تبقى لديك {info['free_questions_left']} سؤال مجاني)",
            reply_markup=get_categories_markup(CATEGORIES)
        )
        return CHOOSE_CATEGORY
    else:
        await update.message.reply_text(
            f"لقد استنفدت الأسئلة المجانية.\nسعر الإجابة على كل سؤال: {QUESTION_PRICE:,} دينار.\nيرجى تحويل المبلغ إلى رقم الحساب: 9916153415 ثم اضغط تم الدفع.\nقريباً سيتم دعم فاست باي وزين كاش وآسيا حوالة.",
            reply_markup=get_payment_markup()
        )
        context.user_data["pending_answer"] = question
        return WAIT_PAYMENT

async def payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    if query.data == "paid":
        if context.user_data.get("awaiting_subscription"):
            subscribe_user(user_id, months=1)
            await query.message.reply_text("تم تفعيل الاشتراك الشهري! يمكنك الآن طرح عدد غير محدود من الأسئلة.", reply_markup=get_categories_markup(CATEGORIES))
            context.user_data.pop("awaiting_subscription", None)
            return CHOOSE_CATEGORY
        elif "pending_answer" in context.user_data:
            question = context.user_data["pending_answer"]
            await query.message.reply_text(f"الإجابة:\n{ANSWERS[question]}", reply_markup=get_categories_markup(CATEGORIES))
            context.user_data.pop("pending_answer", None)
            return CHOOSE_CATEGORY
    elif query.data == "subscribe":
        await query.message.reply_text(
            f"قيمة الاشتراك الشهري {MONTHLY_SUBSCRIPTION_PRICE:,} دينار. بعد التحويل اضغط تم الدفع.\n"
            "يرجى التحويل إلى رقم الحساب: 9916153415\nقريباً سيتم دعم فاست باي وزين كاش وآسيا حوالة.",
            reply_markup=get_payment_markup()
        )
        context.user_data["awaiting_subscription"] = True
        return WAIT_PAYMENT
    elif query.data == "back":
        await query.message.reply_text("اختر التصنيف:", reply_markup=get_categories_markup(CATEGORIES))
        return CHOOSE_CATEGORY

async def back_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("اختر التصنيف:", reply_markup=get_categories_markup(CATEGORIES))
    return CHOOSE_CATEGORY