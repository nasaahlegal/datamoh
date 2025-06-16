import logging
from telegram import Update
from telegram.ext import ContextTypes
from config import ADMIN_TELEGRAM_ID
from keyboards import (
    get_admin_menu_markup, get_categories_markup,
    get_questions_list_markup, get_question_manage_markup,
    get_admin_decision_markup, get_sub_admin_options_markup
)
from users import (
    get_active_subscriptions, extend_subscription, remove_subscription,
    get_user, set_subscription
)
import questions
import time

logger = logging.getLogger(__name__)

admin_active_subs_cache = {}

# ========== لوحات الأدمن العامة ==========
async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_TELEGRAM_ID:
        await update.message.reply_text("⛔ هذا الأمر للمشرفين فقط!")
        return
    context.user_data.clear()
    await update.message.reply_text(
        "لوحة تحكم الأدمن:\nاختر ما تريد إدارته:",
        reply_markup=get_admin_menu_markup()
    )

# ========== إحصائيات ==========
async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        from users import get_connection
        conn = get_connection()
        cur = conn.cursor()
        now = int(time.time())
        cur.execute("SELECT COUNT(*) FROM users")
        total_users = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM users WHERE sub_expiry > %s", (now,))
        active_subs = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM users WHERE sub_expiry <= %s AND sub_expiry > 0", (now,))
        expired_subs = cur.fetchone()[0]
        conn.close()
        await update.message.reply_text(
            f"📊 إحصائيات البوت:\n"
            f"• إجمالي المستخدمين: {total_users}\n"
            f"• المشتركين النشطين: {active_subs}\n"
            f"• المشتركين المنتهية اشتراكاتهم: {expired_subs}\n"
            f"• آخر تحديث: {time.strftime('%Y-%m-%d %H:%M')}"
        )
    except Exception as e:
        logger.error("admin_stats error: %s", e)
        await update.message.reply_text("حدث خطأ أثناء جلب الإحصائيات.")

# ========== إدارة المشتركين ==========
async def admin_subs(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    context.user_data.clear()
    context.user_data["awaiting_sub_select"] = True
    await update.message.reply_text(msg)

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
    if update.effective_user.id != ADMIN_TELEGRAM_ID:
        await update.callback_query.answer("⛔ هذا الأمر للمشرفين فقط!", show_alert=True)
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

async def handle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_TELEGRAM_ID:
        await update.callback_query.answer("⛔ هذا الأمر للمشرفين فقط!", show_alert=True)
        return
    from handlers import pending_paid_questions, get_answer_from_questions
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

# ========== إدارة الأسئلة ==========
# المرحلة 1: اختيار القسم
async def admin_manage_questions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_TELEGRAM_ID:
        return
    context.user_data.clear()
    context.user_data["admin_questions_state"] = "choose_category"
    await update.message.reply_text(
        "اختر القسم:",
        reply_markup=get_categories_markup(questions.LEGAL_QUESTIONS)
    )

# المرحلة 2: بعد اختيار القسم
async def admin_select_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("admin_questions_state") != "choose_category":
        return
    cat = update.message.text.strip()
    if cat not in questions.LEGAL_QUESTIONS:
        await update.message.reply_text("يرجى اختيار قسم صحيح.")
        return
    context.user_data["selected_category"] = cat
    context.user_data["admin_questions_state"] = "in_questions_list"
    qs = questions.LEGAL_QUESTIONS[cat]
    await update.message.reply_text(
        f"أسئلة قسم [{cat}]:",
        reply_markup=get_questions_list_markup(qs)
    )
    await update.message.reply_text(
        "لإضافة سؤال جديد، اضغط على (إضافة سؤال جديد)\n"
        "لتعديل أو حذف سؤال، اضغط على نص السؤال."
    )

# المرحلة 3: إدخال سؤال جديد أو اختيار سؤال لتعديله/حذفه
async def admin_select_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("admin_questions_state") != "in_questions_list":
        return
    cat = context.user_data.get("selected_category")
    text = update.message.text.strip()
    if text == "إضافة سؤال جديد":
        await update.message.reply_text("أرسل نص السؤال الجديد:")
        context.user_data["admin_questions_state"] = "add_question_text"
        return
    elif text == "رجوع":
        await admin_manage_questions(update, context)
        return
    # اختيار سؤال للتعديل أو الحذف
    qs = questions.LEGAL_QUESTIONS[cat]
    for idx, (q, a) in enumerate(qs):
        if q == text:
            context.user_data["selected_question_idx"] = idx
            context.user_data["admin_questions_state"] = "manage_question"
            await update.message.reply_text(
                f"اختر الإجراء للسؤال:\n{q}",
                reply_markup=get_question_manage_markup()
            )
            break

# المرحلة 4: استقبال نص السؤال الجديد
async def admin_receive_new_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("admin_questions_state") != "add_question_text":
        return
    question = update.message.text.strip()
    context.user_data["new_question_text"] = question
    context.user_data["admin_questions_state"] = "add_question_answer"
    await update.message.reply_text("أرسل جواب السؤال:")

# المرحلة 5: استقبال الجواب الجديد
async def admin_receive_new_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("admin_questions_state") != "add_question_answer":
        return
    cat = context.user_data.get("selected_category")
    question = context.user_data.pop("new_question_text")
    answer = update.message.text.strip()
    questions.add_question(cat, question, answer)
    await update.message.reply_text("✅ تم إضافة السؤال بنجاح.")
    context.user_data["admin_questions_state"] = "choose_category"
    await admin_manage_questions(update, context)

# المرحلة 6: التحكم في السؤال (تعديل/حذف)
async def admin_edit_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("admin_questions_state") != "manage_question":
        return
    idx = context.user_data.get("selected_question_idx")
    cat = context.user_data.get("selected_category")
    qs = questions.LEGAL_QUESTIONS[cat]
    q, a = qs[idx]
    await update.message.reply_text(f"السؤال الحالي:\n{q}\nأرسل النص الجديد (أو أرسل نفسه لعدم التغيير):")
    context.user_data["admin_questions_state"] = "edit_question_text"

async def admin_receive_edited_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("admin_questions_state") != "edit_question_text":
        return
    idx = context.user_data.get("selected_question_idx")
    cat = context.user_data.get("selected_category")
    qs = questions.LEGAL_QUESTIONS[cat]
    new_q = update.message.text.strip()
    _, old_a = qs[idx]
    questions.edit_question(cat, idx, new_q, old_a)
    await update.message.reply_text("أرسل الجواب الجديد (أو أرسل نفسه لعدم التغيير):")
    context.user_data["admin_questions_state"] = "edit_question_answer"
    context.user_data["edited_question_text"] = new_q

async def admin_receive_edited_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("admin_questions_state") != "edit_question_answer":
        return
    idx = context.user_data.get("selected_question_idx")
    cat = context.user_data.get("selected_category")
    new_q = context.user_data.pop("edited_question_text")
    new_a = update.message.text.strip()
    questions.edit_question(cat, idx, new_q, new_a)
    await update.message.reply_text("✅ تم تعديل السؤال والإجابة بنجاح.")
    context.user_data["admin_questions_state"] = "choose_category"
    await admin_manage_questions(update, context)

async def admin_delete_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("admin_questions_state") != "manage_question":
        return
    idx = context.user_data.get("selected_question_idx")
    cat = context.user_data.get("selected_category")
    questions.delete_question(cat, idx)
    await update.message.reply_text("✅ تم حذف السؤال بنجاح.")
    context.user_data["admin_questions_state"] = "choose_category"
    await admin_manage_questions(update, context)