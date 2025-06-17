from telegram import Update
from telegram.ext import ContextTypes
from users import get_active_subscriptions, remove_subscription, set_subscription
from keyboards import get_sub_admin_options_markup
import time

admin_active_subs_cache = {}

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    subs = get_active_subscriptions()
    await update.message.reply_text(
        f"📊 الاشتراكات الشهرية الفعّالة: {len(subs)}\n"
        f"🕒 آخر تحديث: {time.strftime('%Y-%m-%d %H:%M')}",
        protect_content=True
    )

async def report_subscriptions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    subs = get_active_subscriptions()
    await update.message.reply_text(
        f"📈 تقرير الاشتراكات:\n"
        f"• فعّالة: {len(subs)}\n"
        f"• منتهية: (سجل الطلبات المنتهية في لوحة الويب لاحقاً)\n"
        f"🕒 {time.strftime('%Y-%m-%d %H:%M')}",
        protect_content=True
    )

async def admin_subs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    subs = get_active_subscriptions()
    if not subs:
        await update.message.reply_text("لا يوجد اشتراكات شهرية فعالة حاليًا.", protect_content=True)
        return
    msg = "📋 قائمة الاشتراكات الفعالة:\n"
    admin_active_subs_cache[update.effective_user.id] = subs
    for idx, sub in enumerate(subs, 1):
        identity = f"@{sub['username']}" if sub['username'] else f"ID:{sub['user_id']}"
        msg += f"{idx}. {sub['full_name']} ({identity}) — {sub['days_left']} يوم متبقٍ\n"
    msg += "\nأرسل رقم المشترك للتعديل عليه."
    await update.message.reply_text(msg, protect_content=True)
    context.user_data["awaiting_sub_select"] = True

async def admin_subscription_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting_sub_select"):
        return
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text("يرجى إرسال رقم صحيح.", protect_content=True)
        return
    idx = int(text) - 1
    subs = admin_active_subs_cache.get(update.effective_user.id, [])
    if idx < 0 or idx >= len(subs):
        await update.message.reply_text("رقم غير صحيح.", protect_content=True)
        return
    sub = subs[idx]
    context.user_data["selected_sub"] = sub
    await update.message.reply_text(
        f"المستخدم: {sub['full_name']} (@{sub['username'] or 'بدون'})\n"
        f"الأيام المتبقية: {sub['days_left']}",
        protect_content=True
    )
    await update.message.reply_text(
        "اختر إجراء:",
        reply_markup=get_sub_admin_options_markup(sub["user_id"]),
        protect_content=True
    )
    context.user_data["awaiting_sub_select"] = False
    context.user_data["awaiting_action"] = True

async def admin_subs_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if "selected_sub" not in context.user_data:
        await query.edit_message_text("خطأ، يرجى إعادة المحاولة.")
        return
    data = query.data
    sub = context.user_data["selected_sub"]
    user_id = sub["user_id"]
    bot = context.bot
    if data.startswith("extend_"):
        set_subscription(user_id, sub["username"], sub["full_name"], days= sub["days_left"] + 3)
        await query.edit_message_text("✅ تم تمديد الاشتراك 3 أيام.")
        # إشعار المستخدم بالتمديد
        try:
            await bot.send_message(
                chat_id=user_id,
                text="🎁 تم تمديد اشتراكك لمدة 3 أيام إضافية كهدية من الإدارة."
            )
        except Exception as e:
            print(f"خطأ في إرسال إشعار التمديد للمستخدم {user_id}: {e}")
    elif data.startswith("delete_"):
        remove_subscription(user_id)
        await query.edit_message_text("❌ تم حذف الاشتراك.")
        # إشعار المستخدم بالحذف
        try:
            await bot.send_message(
                chat_id=user_id,
                text="⚠️ تم إلغاء اشتراكك الشهري من قبل الإدارة. إذا كان لديك اعتراض يرجى مراسلتنا."
            )
        except Exception as e:
            print(f"خطأ في إرسال إشعار الحذف للمستخدم {user_id}: {e}")
    context.user_data.pop("selected_sub", None)
    context.user_data["awaiting_sub_select"] = True

async def handle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    bot = context.bot

    # pattern: (accept|reject)_(sub|question)_user_id
    if data.startswith("accept_sub_"):
        user_id = int(data.split("_")[2])
        set_subscription(user_id, "", "", 30)
        await query.edit_message_text(f"✅ تم تفعيل الاشتراك للمستخدم {user_id}")
        try:
            await bot.send_message(
                chat_id=user_id,
                text="🎉 تم تفعيل اشتراكك بنجاح لمدة 30 يومًا! يمكنك الآن استخدام جميع الأسئلة بدون قيود."
            )
        except Exception as e:
            print(f"خطأ في إرسال إشعار التفعيل للمستخدم {user_id}: {e}")
    elif data.startswith("reject_sub_"):
        user_id = int(data.split("_")[2])
        await query.edit_message_text(f"❌ تم رفض طلب الاشتراك للمستخدم {user_id}")
        try:
            await bot.send_message(
                chat_id=user_id,
                text="⚠️ تم رفض طلبك للاشتراك الشهري. في حال وجود خطأ، يرجى التواصل مع الإدارة."
            )
        except Exception as e:
            print(f"خطأ في إرسال إشعار الرفض للمستخدم {user_id}: {e}")
    elif data.startswith("accept_question_"):
        user_id = int(data.split("_")[2])
        await query.edit_message_text(f"✅ تم قبول دفع المستخدم {user_id} لسؤال واحد.")
        try:
            await bot.send_message(
                chat_id=user_id,
                text="✅ تم تأكيد دفعك وسيتم الرد عليك قريبًا على سؤالك."
            )
        except Exception as e:
            print(f"خطأ في إشعار المستخدم للسؤال المدفوع {user_id}: {e}")
    elif data.startswith("reject_question_"):
        user_id = int(data.split("_")[2])
        await query.edit_message_text(f"❌ تم رفض دفع المستخدم {user_id} لسؤال واحد.")
        try:
            await bot.send_message(
                chat_id=user_id,
                text="⚠️ تم رفض طلبك للإجابة المدفوعة. في حال وجود خطأ يرجى التواصل مع الإدارة."
            )
        except Exception as e:
            print(f"خطأ في إرسال إشعار الرفض للسؤال المدفوع {user_id}: {e}")