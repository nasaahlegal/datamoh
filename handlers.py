from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from config import (
    CATEGORIES, ANSWERS, FREE_QUESTIONS_LIMIT, QUESTION_PRICE,
    SUBSCRIPTION_PRICE, SUBSCRIPTION_DAYS, PAY_MSG, SINGLE_PAY_MSG,
    ADMIN_TELEGRAM_ID, ADMIN_USERNAME, SUPPORT_USERNAME
)
from keyboards import get_categories_markup, get_questions_markup, get_payment_markup, get_admin_payment_action_markup
from users import (
    init_users_db, create_or_get_user, decrement_free_questions, reset_free_questions,
    set_subscription, is_subscribed, get_user
)

CHOOSE_CATEGORY, CHOOSE_QUESTION, WAIT_PAYMENT = range(3)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    create_or_get_user(user.id, user.username, user.full_name)
    await update.message.reply_text(
        "مرحباً بك في بوت الاستشارات القانونية التلقائية!\nاختر التصنيف:",
        reply_markup=get_categories_markup(CATEGORIES)
    )
    return CHOOSE_CATEGORY

async def category_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    create_or_get_user(user.id, user.username, user.full_name)
    cat = update.message.text
    if cat in CATEGORIES:
        context.user_data["category"] = cat
        await update.message.reply_text("اختر السؤال:", reply_markup=get_questions_markup(CATEGORIES[cat]))
        return CHOOSE_QUESTION
    elif cat == "اشتراك شهري":
        await update.message.reply_text(PAY_MSG, reply_markup=get_payment_markup())
        context.user_data["awaiting_subscription"] = True
        return WAIT_PAYMENT
    elif cat == "عن البوت":
        await update.message.reply_text(
            f"هذا بوت استشارات قانونية تلقائية. أول {FREE_QUESTIONS_LIMIT} أسئلة مجانية، بعد ذلك كل سؤال {QUESTION_PRICE:,} دينار.\n"
            f"يوجد اشتراك شهري بـ {SUBSCRIPTION_PRICE:,} دينار لأسئلة غير محدودة.\n"
            f"للدعم أو الاستفسار: @{SUPPORT_USERNAME}",
            reply_markup=get_categories_markup(CATEGORIES)
        )
        return CHOOSE_CATEGORY
    else:
        await update.message.reply_text("يرجى اختيار تصنيف صحيح.", reply_markup=get_categories_markup(CATEGORIES))
        return CHOOSE_CATEGORY

async def question_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_info = get_user(user.id)
    question = update.message.text
    if question == "رجوع":
        await update.message.reply_text("اختر التصنيف:", reply_markup=get_categories_markup(CATEGORIES))
        return CHOOSE_CATEGORY

    if question not in ANSWERS:
        await update.message.reply_text("يرجى اختيار سؤال من القائمة.", reply_markup=get_questions_markup(CATEGORIES[context.user_data["category"]]))
        return CHOOSE_QUESTION

    if is_subscribed(user.id):
        await update.message.reply_text(f"الإجابة:\n{ANSWERS[question]}", reply_markup=get_categories_markup(CATEGORIES))
        return CHOOSE_CATEGORY

    if user_info["free_questions_left"] > 0:
        decrement_free_questions(user.id)
        await update.message.reply_text(
            f"الإجابة:\n{ANSWERS[question]}\n\n(تبقى لديك {user_info['free_questions_left']-1} سؤال مجاني)",
            reply_markup=get_categories_markup(CATEGORIES)
        )
        return CHOOSE_CATEGORY
    else:
        await update.message.reply_text(
            SINGLE_PAY_MSG, reply_markup=get_payment_markup()
        )
        context.user_data["pending_answer"] = question
        context.user_data.pop("awaiting_subscription", None)
        return WAIT_PAYMENT

async def payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    await query.answer()
    if context.user_data.get("awaiting_subscription"):
        # إشعار للأدمن مع أزرار
        await query.message.reply_text("تم إرسال طلبك وسيتم تفعيل الاشتراك بعد التأكد من التحويل.")
        await context.bot.send_message(
            chat_id=ADMIN_TELEGRAM_ID,
            text=f"طلب اشتراك جديد:\nالاسم: {user.full_name}\nالمعرف: @{user.username or 'بدون'}\nID: {user.id}",
            reply_markup=get_admin_payment_action_markup(user.id)
        )
        context.user_data.pop("awaiting_subscription", None)
        return ConversationHandler.END
    elif "pending_answer" in context.user_data:
        # إشعار للأدمن مع أزرار
        question = context.user_data["pending_answer"]
        await query.message.reply_text("تم إرسال طلبك وسيتم تفعيل الخدمة بعد التأكد من التحويل.")
        await context.bot.send_message(
            chat_id=ADMIN_TELEGRAM_ID,
            text=f"طلب دفع لسؤال:\nالاسم: {user.full_name}\nالمعرف: @{user.username or 'بدون'}\nID: {user.id}\nالسؤال: {question}",
            reply_markup=get_admin_payment_action_markup(f"{user.id}_q")
        )
        context.user_data.pop("pending_answer", None)
        return ConversationHandler.END
    else:
        await query.message.reply_text("حدث خطأ! يرجى المحاولة مرة أخرى.")
        return ConversationHandler.END

async def admin_action_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()
    if data.startswith("approve_sub_"):
        id_part = data.replace("approve_sub_", "")
        if "_q" in id_part:
            # دفع لسؤال مفرد (يمكنك توسيعها لحفظ التقديم)
            user_id = int(id_part.split("_")[0])
            user = get_user(user_id)
            question = None  # يمكن توسيع منطق الربط مع السؤال
            await context.bot.send_message(
                chat_id=user_id,
                text="تم تأكيد الدفع. إليك الإجابة على سؤالك:\n(يرجى مراسلة الدعم إذا لم تظهر الإجابة خلال دقيقة)\n"
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
    await update.message.reply_text("اختر التصنيف:", reply_markup=get_categories_markup(CATEGORIES))
    return CHOOSE_CATEGORY