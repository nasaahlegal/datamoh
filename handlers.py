from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from config import (
    CATEGORIES, ANSWERS, FREE_QUESTIONS_LIMIT, QUESTION_PRICE,
    SINGLE_PAY_MSG, ADMIN_TELEGRAM_ID, ADMIN_USERNAME, SUPPORT_USERNAME,
    ABOUT_MSG, SUBSCRIPTION_PRICE, PAY_ACCOUNT, PAY_MSG, WELCOME_MSG
)
from keyboards import (
    get_main_menu_markup, get_payment_reply_markup,
    get_back_main_markup, get_about_markup, get_free_confirm_markup,
    get_subscription_markup, get_admin_decision_markup, get_sub_admin_options_markup,
    get_lawyer_platform_markup
)
from users import (
    create_or_get_user, decrement_free_questions,
    get_user, set_subscription, get_connection,
    get_active_subscriptions, extend_subscription, remove_subscription, is_subscribed
)
from questions import fetch_answer_by_question, fetch_questions_by_category, fetch_all_categories
from logger import get_logger
import time

logger = get_logger("handlers")

CHOOSE_CATEGORY, CHOOSE_QUESTION, WAIT_PAYMENT, FREE_OR_SUB_CONFIRM, SUBSCRIPTION_FLOW = range(5)

admin_active_subs_cache = {}

pending_paid_questions = {}

def get_answer_from_questions(question_text):
    answer = fetch_answer_by_question(question_text)
    if answer:
        return answer
    return ANSWERS.get(question_text, "لا توجد إجابة مسجلة لهذا السؤال.")

async def admin_only(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_TELEGRAM_ID:
        if hasattr(update, "message") and update.message:
            await update.message.reply_text("⛔ هذا الأمر للمشرفين فقط!")
        elif hasattr(update, "callback_query") and update.callback_query:
            await update.callback_query.answer("⛔ هذا الأمر للمشرفين فقط!", show_alert=True)
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

async def admin_subs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update, context):
        return
    subs = get_active_subscriptions()
    if not subs:
        await update.message.reply_text("لا يوجد اشتراكات شهرية فعالة حاليًا.")
        return
    msg = "📋 قائمة الاشتراكات الفعالة:\n"
    admin_active_subs_cache[update.effective_user.id] = subs
    for idx, sub in enumerate(subs, 1):
        if sub['username']:
            identity = f"@{sub['username']}"
        elif sub['full_name']:
            identity = sub['full_name']
        else:
            identity = f"ID:{sub['user_id']}"
        msg += f"{idx}. {sub['full_name']} ({identity}) — {sub['days_left']} يوم متبقٍ\n"
    msg += "\nأرسل رقم المشترك للتعديل عليه."
    await update.message.reply_text(msg)
    context.user_data["awaiting_sub_select"] = True

async def admin_subscription_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting_sub_select"):
        return
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text("يرجى إرسال رقم تسلسل صحيح.")
        return
    idx = int(text) - 1
    subs = admin_active_subs_cache.get(update.effective_user.id, [])
    if idx < 0 or idx >= len(subs):
        await update.message.reply_text("رقم غير صحيح.")
        return
    sub = subs[idx]
    context.user_data["selected_sub"] = sub
    await update.message.reply_text(
        f"المستخدم: {sub['full_name']} (@{sub['username'] or 'بدون'})\n"
        f"الايام المتبقية: {sub['days_left']}"
    )
    await update.message.reply_text(
        "اختر إجراء:",
        reply_markup=get_sub_admin_options_markup(sub["user_id"])
    )
    context.user_data["awaiting_sub_action"] = True
    context.user_data["awaiting_sub_select"] = False

async def admin_subs_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update, context):
        return
    query = update.callback_query
    await query.answer()
    data = query.data
    user_data = context.user_data
    sub = user_data.get("selected_sub")
    if data == "subs_back":
        await admin_subs(update, context)
        return
    if not sub:
        await query.edit_message_text("حدث خطأ. الرجاء إعادة المحاولة.")
        return
    user_id = sub["user_id"]
    if data.startswith("extend_"):
        extend_subscription(user_id, 3)
        await query.edit_message_text("✅ تم تمديد الاشتراك 3 أيام.")
        await context.bot.send_message(
            chat_id=user_id,
            text="🎁 تم تمديد اشتراكك لمدة 3 أيام إضافية كهدية لتميزك من الإدارة!"
        )
    elif data.startswith("delete_"):
        remove_subscription(user_id)
        await query.edit_message_text("❌ تم حذف الاشتراك لهذا المستخدم.")
        await context.bot.send_message(
            chat_id=user_id,
            text="⚠️ تم إلغاء اشتراكك الشهري من قبل الإدارة. إذا كان لديك اعتراض يرجى مراسلتنا."
        )
    user_data.pop("selected_sub", None)
    user_data["awaiting_sub_select"] = True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    create_or_get_user(user.id, user.username, user.full_name)
    logger.info(f"User started: {user.id} | @{user.username}")
    await update.message.reply_text(
        WELCOME_MSG,
        reply_markup=get_lawyer_platform_markup(CATEGORIES)
    )
    return CHOOSE_CATEGORY

async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👇 اختر القسم المناسب من القائمة للبدء:",
        reply_markup=get_lawyer_platform_markup(CATEGORIES)
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

    # استخدام قاعدة البيانات الديناميكية للأسئلة
    if text == "اشتراك شهري":
        return await subscription_handler(update, context)
    elif text in CATEGORIES:
        context.user_data["category"] = text
        # ديناميكي: جلب الأسئلة من الجدول
        questions_db = fetch_questions_by_category(text)
        questions = [q[1] for q in questions_db] if questions_db else CATEGORIES[text]
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
            reply_markup=get_lawyer_platform_markup(CATEGORIES))
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
            reply_markup=get_lawyer_platform_markup(CATEGORIES)
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
    questions = context.user_data.get("questions", [])

    try:
        idx = int(update.message.text) - 1
        if idx < 0 or idx >= len(questions):
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

    question = questions[idx]
    context.user_data["pending_answer"] = question
    context.user_data["pending_category"] = context.user_data.get("category", "")

    if is_subscribed(user.id):
        await update.message.reply_text(
            f"الإجابة:\n{get_answer_from_questions(question)}\n\n"
            f"(اشتراكك الشهري فعّال، متبقٍ لك {int((user_info['sub_expiry']-int(time.time()))//(24*60*60))} يوم)",
            reply_markup=get_lawyer_platform_markup(CATEGORIES)
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
            reply_markup=get_lawyer_platform_markup(CATEGORIES)
        )
        context.user_data.pop("awaiting_free_answer", None)
        return CHOOSE_CATEGORY
    elif update.message.text == "رجوع":
        cat = context.user_data.get("category")
        # جلب الأسئلة من قاعدة البيانات
        questions_db = fetch_questions_by_category(cat)
        questions = [q[1] for q in questions_db] if questions_db else CATEGORIES.get(cat, [])
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
    questions_db = fetch_questions_by_category(cat)
    questions = [q[1] for q in questions_db] if questions_db else CATEGORIES.get(cat, [])
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
            await update.message.reply_text(
                "✅ تم إرسال طلب اشتراكك بنجاح!\n"
                "سيتم تفعيل الاشتراك خلال 24 ساعة بعد التحقق من التحويل.\n"
                "يمكنك متابعة استخدام البوت الآن:",
                reply_markup=get_lawyer_platform_markup(CATEGORIES)
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
                reply_markup=get_lawyer_platform_markup(CATEGORIES)
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
            reply_markup=get_lawyer_platform_markup(CATEGORIES)
        )
        return CHOOSE_CATEGORY

    else:
        await update.message.reply_text("يرجى استخدام الأزرار فقط.", reply_markup=get_payment_reply_markup())
        return WAIT_PAYMENT

async def handle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update, context):
        return
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = int(data.split('_')[1])

    if data.startswith("accept_"):
        if user_id in pending_paid_questions:
            question, category = pending_paid_questions[user_id]
            answer = get_answer_from_questions(question)
            await query.edit_message_text(f"✅ تم قبول طلب دفع لسؤال المستخدم {user_id}.\nتم إرسال الجواب.")
            await context.bot.send_message(
                chat_id=user_id,
                text=f"✅ تم التحقق من الدفع.\n\nالإجابة:\n{answer}\n\nشكراً لاستخدامك المنصة."
            )
            del pending_paid_questions[user_id]
        else:
            set_subscription(user_id, "", "", 30)
            await query.edit_message_text(f"✅ تم تفعيل الاشتراك للمستخدم {user_id}")
            await context.bot.send_message(
                chat_id=user_id,
                text="🎉 تم تفعيل اشتراكك بنجاح لمدة 30 يومًا!\n"
                     "يمكنك الآن استخدام جميع الأسئلة بدون قيود."
            )
    elif data.startswith("reject_"):
        await query.edit_message_text(f"❌ تم رفض طلب المستخدم {user_id}")
        await context.bot.send_message(
            chat_id=user_id,
            text="⚠️ تم رفض طلبك الجديد (دفع/اشتراك).\n"
                 "في حال وجود خطأ، يرجى التواصل مع @mohamycom"
        )
        if user_id in pending_paid_questions:
            del pending_paid_questions[user_id]