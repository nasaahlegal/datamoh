from telegram import Update
from telegram.ext import ContextTypes

async def electronic_payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚧 الدفع الإلكتروني غير مفعل حالياً.\n"
        "سيتم تفعيل الخدمة قريباً عبر فاست باي وزين كاش وآسيا حوالة.\n"
        "يمكنك العودة واختيار التحويل اليدوي حالياً.",
        protect_content=True
    )
    return None