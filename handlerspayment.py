from telegram import Update
from telegram.ext import ContextTypes
from users import set_subscription
from keyboards import get_payment_reply_markup, get_lawyer_platform_markup
from config import PAY_ACCOUNT, SUBSCRIPTION_PRICE
from states_enum import States

async def subscription_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"اشتراك شهري بقيمة {SUBSCRIPTION_PRICE} د.ع\n"
        f"يرجى التحويل إلى حساب {PAY_ACCOUNT} ثم اضغط (موافق).",
        reply_markup=get_payment_reply_markup(),
        protect_content=True
    )
    context.user_data["sub_request"] = True
    return States.PAYMENT.value

async def subscription_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "موافق" and context.user_data.get("sub_request"):
        await update.message.reply_text(
            "✅ طلب الاشتراك قيد المراجعة من الإدارة.",
            reply_markup=get_lawyer_platform_markup({}),
            protect_content=True
        )
    return States.CATEGORY.value

async def payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.effective_user
    if text == "تم التحويل":
        if context.user_data.get("sub_request"):
            set_subscription(user.id, user.username or "", user.full_name or "", days=30)
            await update.message.reply_text(
                "🎉 اشتراكك مفعل الآن لمدة 30 يومًا!",
                reply_markup=get_lawyer_platform_markup({}),
                protect_content=True
            )
        else:
            # الدفع لسؤال واحد: نرسل الجواب فوراً
            question = context.user_data.get("pending_answer", "")
            # استدعاء دالة get_answer من handlers.user
            from handlers.user import get_answer
            answer = get_answer(question)
            await update.message.reply_text(
                f"✅ تم التحقق من الدفع.\n\nالإجابة:\n{answer}",
                reply_markup=get_lawyer_platform_markup({}),
                protect_content=True
            )
        # تنظيف
        context.user_data.pop("sub_request", None)
        context.user_data.pop("pending_answer", None)
        return States.CATEGORY.value

    elif text == "الغاء":
        await update.message.reply_text(
            "❌ تم إلغاء العملية.",
            reply_markup=get_lawyer_platform_markup({}),
            protect_content=True
        )
        return States.CATEGORY.value

    await update.message.reply_text(
        "يرجى استخدام الأزرار فقط.",
        reply_markup=get_payment_reply_markup(),
        protect_content=True
    )
    return States.PAYMENT.value
