from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler
from users import get_active_subscriptions, remove_subscription, set_subscription
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
        await query.edit_message_text("خطأ، يرجى إعادة المحاولة.", protect_content=True)
        return
    data = query.data
    sub = context.user_data["selected_sub"]
    user_id = sub["user_id"]
    if data.startswith("extend_"):
        set_subscription(user_id, sub["username"], sub["full_name"], days= sub["days_left"] + 3)
        await query.edit_message_text("✅ تم تمديد الاشتراك 3 أيام.", protect_content=True)
    elif data.startswith("delete_"):
        remove_subscription(user_id)
        await query.edit_message_text("❌ تم حذف الاشتراك.", protect_content=True)
    context.user_data.pop("selected_sub", None)
    context.user_data["awaiting_sub_select"] = True

async def handle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = int(data.split("_")[1])
    if data.startswith("accept_"):
        set_subscription(user_id, "", "", 30)
        await query.edit_message_text(f"✅ تم تفعيل الاشتراك للمستخدم {user_id}", protect_content=True)
    else:
        await query.edit_message_text(f"❌ تم رفض الطلب للمستخدم {user_id}", protect_content=True)
