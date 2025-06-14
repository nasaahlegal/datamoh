from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler
from config import (
    CATEGORIES, ANSWERS, FREE_QUESTIONS_LIMIT, QUESTION_PRICE,
    SINGLE_PAY_MSG, ADMIN_TELEGRAM_ID, ADMIN_USERNAME, SUPPORT_USERNAME,
    ABOUT_MSG, SUBSCRIPTION_PRICE, PAY_ACCOUNT, PAY_MSG
)
from keyboards import (
    get_main_menu_markup, get_payment_reply_markup,
    get_back_main_markup, get_about_markup, get_free_confirm_markup,
    get_subscription_markup, get_admin_decision_markup
)
from users import (
    create_or_get_user, decrement_free_questions,
    get_user, set_subscription, get_connection
)
import time

CHOOSE_CATEGORY, CHOOSE_QUESTION, WAIT_PAYMENT, FREE_OR_SUB_CONFIRM, SUBSCRIPTION_FLOW = range(5)

async def admin_only(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_TELEGRAM_ID:
        await update.message.reply_text("⛔ هذا الأمر للمشرفين فقط!")
        return False
    return True

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update, context):
        return
    
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM users WHERE sub_expiry > %s", (int(time.time()),))
    active_subs = cur.fetchone()[0]
    conn.close()

    await update.message.reply_text(
        f"📊 إحصائيات البوت:\n"
        f"• إجمالي المستخدمين: {total_users}\n"
        f"• المشتركين النشطين: {active_subs}\n"
        f"• آخر تحديث: {time.strftime('%Y-%m-%d %H:%M')}"
    )

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
    text = update.message.text
    
    if text == "اشتراك شهري":
        return await subscription_handler(update, context)
    elif text in CATEGORIES:
        context.user_data["category"] = text
        questions = CATEGORIES[text]
        context.user_data["questions"] = questions
        numbered = "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])
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
            reply_markup=get_main_menu_markup(CATEGORIES))
        return CHOOSE_CATEGORY

async def subscription_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        context.user_data["subscription_request"] = False
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
    user = update.effective_user
    text = update.message.text
    user_id = user.id
    
    if text == "تم التحويل":
        if context.user_data.get("subscription_request", False):
            # طلب اشتراك
            await update.message.reply_text("تم إرسال طلب اشتراكك وسيتم تفعيله بعد التأكد من التحويل.")
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
        else:
            # طلب سؤال واحد
            pending_answer = context.user_data.get("pending_answer", "سؤال غير محدد")
            await update.message.reply_text("تم إرسال طلبك وسيتم تفعيل الخدمة بعد التأكد من التحويل.")
            await update.get_bot().send_message(
                chat_id=ADMIN_TELEGRAM_ID,
                text=f"📬 طلب دفع لسؤال:\n"
                     f"👤 الاسم: {user.full_name}\n"
                     f"🔗 المعرف: @{user.username or 'بدون'}\n"
                     f"🆔 ID: {user.id}\n"
                     f"❓ السؤال: {pending_answer}",
            )
        
        context.user_data.pop("pending_answer", None)
        context.user_data.pop("subscription_request", None)
        return ConversationHandler.END
        
    elif text == "الغاء":
        await update.message.reply_text(
            "تم إلغاء عملية الدفع.",
            reply_markup=get_main_menu_markup(CATEGORIES)
        )
        return CHOOSE_CATEGORY
        
    else:
        await update.message.reply_text("يرجى استخدام الأزرار فقط.", reply_markup=get_payment_reply_markup())
        return WAIT_PAYMENT

async def handle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = int(data.split('_')[1])
    
    if data.startswith("accept_"):
        set_subscription(user_id, "", "", 30)
        await query.edit_message_text(f"✅ تم تفعيل الاشتراك للمستخدم {user_id}")
        await context.bot.send_message(
            chat_id=user_id,
            text="🎉 تم تفعيل اشتراكك بنجاح لمدة 30 يومًا!\n"
                 "يمكنك الآن استخدام جميع الأسئلة بدون قيود."
        )
    elif data.startswith("reject_"):
        await query.edit_message_text(f"❌ تم رفض طلب اشتراك المستخدم {user_id}")
        await context.bot.send_message(
            chat_id=user_id,
            text="⚠️ تم رفض طلب اشتراكك.\n"
                 "في حال وجود خطأ، يرجى التواصل مع @mohamycom"
        )