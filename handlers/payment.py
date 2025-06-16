from telegram import Update
from telegram.ext import ContextTypes
from users import set_subscription, get_user, is_subscribed
from keyboards import (
    get_payment_reply_markup, get_lawyer_platform_markup, get_subscription_markup, get_admin_decision_markup
)
from config import PAY_ACCOUNT, SUBSCRIPTION_PRICE, PAY_MSG, SINGLE_PAY_MSG, ADMIN_TELEGRAM_ID, Q_DATA
from states_enum import States

async def subscription_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_info = get_user(user.id)
    if is_subscribed(user.id):
        now = int(__import__('time').time())
        days_left = int((user_info["sub_expiry"] - now) // (24*60*60))
        await update.message.reply_text(
            f"لديك اشتراك شهري فعّال بالفعل.\nعدد الأيام المتبقية: {days_left} يومًا.\n"
            "يمكنك الاستمرار في استخدام جميع ميزات المنصة.",
            reply_markup=get_lawyer_platform_markup(Q_DATA)
        )
        return States.CATEGORY.value
    await update.message.reply_text(
        PAY_MSG,
        reply_markup=get_subscription_markup()
    )
    return States.SUBSCRIBE.value

async def subscription_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "موافق":
        await update.message.reply_text(
            f"يرجى تحويل رسوم الاشتراك الى الحساب التالي:\n"
            f"{PAY_ACCOUNT}\n\n"
            "بعد التحويل يرجى الضغط على (تم التحويل) وسيتم تفعيل الاشتراك بعد التأكد من قبل المختص",
            reply_markup=get_payment_reply_markup()
        )
        context.user_data["subscription_request"] = True
        context.user_data["payment_type"] = "subscription"
        return States.PAYMENT.value
    elif text == "رجوع":
        from handlers.user import main_menu_handler
        return await main_menu_handler(update, context)
    else:
        await update.message.reply_text("يرجى الاختيار من الأزرار المتوفرة فقط.", reply_markup=get_subscription_markup())
        return States.SUBSCRIBE.value

async def payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text

    if text == "تم التحويل":
        if context.user_data.get("subscription_request", False):
            await update.message.reply_text(
                "✅ تم إرسال طلب اشتراكك بنجاح!\n"
                "سيتم تفعيل الاشتراك خلال 24 ساعة بعد التحقق من التحويل.\n"
                "يمكنك متابعة استخدام البوت الآن:",
                reply_markup=get_lawyer_platform_markup(Q_DATA)
            )
            # إشعار الأدمن مع أزرار القبول والرفض
            await update.get_bot().send_message(
                chat_id=ADMIN_TELEGRAM_ID,
                text=(
                    f"📬 طلب اشتراك جديد:\n"
                    f"👤 الاسم: {user.full_name}\n"
                    f"🔗 المعرف: @{user.username or 'بدون'}\n"
                    f"🆔 ID: {user.id}\n"
                    f"💳 المبلغ: {SUBSCRIPTION_PRICE:,} دينار عراقي\n"
                    f"⏳ المدة: 30 يوم"
                ),
                reply_markup=get_admin_decision_markup(user.id)
            )
        else:
            pending_answer = context.user_data.get("pending_answer", "سؤال غير محدد")
            await update.message.reply_text(
                "✅ تم إرسال طلبك بنجاح!\n"
                "سيتم الرد على سؤالك خلال 24 ساعة بعد التحقق من التحويل.\n"
                "يمكنك متابعة استخدام البوت الآن:",
                reply_markup=get_lawyer_platform_markup(Q_DATA)
            )
            # إشعار الأدمن مع أزرار قبول/رفض
            await update.get_bot().send_message(
                chat_id=ADMIN_TELEGRAM_ID,
                text=(
                    f"📬 طلب دفع جديد لسؤال واحد:\n"
                    f"👤 الاسم: {user.full_name}\n"
                    f"🔗 المعرف: @{user.username or 'بدون'}\n"
                    f"🆔 ID: {user.id}\n"
                    f"💬 السؤال: {pending_answer}\n"
                    f"💳 المبلغ: 5,000 دينار عراقي"
                ),
                reply_markup=get_admin_decision_markup(user.id)
            )
        context.user_data.pop("pending_answer", None)
        context.user_data.pop("pending_category", None)
        context.user_data.pop("subscription_request", None)
        return States.CATEGORY.value

    elif text == "الغاء":
        from handlers.user import main_menu_handler
        await update.message.reply_text(
            "تم إلغاء عملية الدفع.\n"
            "يمكنك العودة للقائمة الرئيسية:",
            reply_markup=get_lawyer_platform_markup(Q_DATA)
        )
        return States.CATEGORY.value

    await update.message.reply_text("يرجى استخدام الأزرار فقط.", reply_markup=get_payment_reply_markup())
    return States.PAYMENT.value