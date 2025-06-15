from telegram import Update
from telegram.ext import ContextTypes
from config import ADMIN_TELEGRAM_ID
from questions_db import (
    add_question, update_question, delete_question,
    get_questions_by_category, get_all_questions, get_question_by_id
)
from app_logging import log_event, log_error

async def admin_only(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_TELEGRAM_ID:
        if hasattr(update, "message") and update.message:
            await update.message.reply_text("⛔ هذا الأمر للمشرفين فقط!")
        elif hasattr(update, "callback_query") and update.callback_query:
            await update.callback_query.answer("⛔ هذا الأمر للمشرفين فقط!", show_alert=True)
        return False
    return True

async def admin_add_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update, context):
        return
    try:
        # /addq category|question|answer
        text = update.message.text.replace('/addq', '').strip()
        parts = text.split('|')
        if len(parts) != 3:
            await update.message.reply_text('يرجى استخدام الصيغة: /addq القسم|السؤال|الجواب')
            return
        category, question, answer = parts
        add_question(category.strip(), question.strip(), answer.strip())
        await update.message.reply_text('✅ تم إضافة السؤال.')
        log_event(f"Admin added question: {question.strip()}")
    except Exception as e:
        await update.message.reply_text(f'خطأ: {str(e)}')
        log_error(f"Add question error: {str(e)}")

async def admin_update_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update, context):
        return
    try:
        # /updateq id|question|answer
        text = update.message.text.replace('/updateq', '').strip()
        parts = text.split('|')
        if len(parts) != 3:
            await update.message.reply_text('يرجى استخدام الصيغة: /updateq رقم_السؤال|السؤال|الجواب')
            return
        id, question, answer = parts
        update_question(int(id), question.strip(), answer.strip())
        await update.message.reply_text('✅ تم تحديث السؤال.')
        log_event(f"Admin updated question {id}: {question.strip()}")
    except Exception as e:
        await update.message.reply_text(f'خطأ: {str(e)}')
        log_error(f"Update question error: {str(e)}")

async def admin_delete_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update, context):
        return
    try:
        # /delq id
        text = update.message.text.replace('/delq', '').strip()
        delete_question(int(text))
        await update.message.reply_text('✅ تم حذف السؤال.')
        log_event(f"Admin deleted question {text}")
    except Exception as e:
        await update.message.reply_text(f'خطأ: {str(e)}')
        log_error(f"Delete question error: {str(e)}")

async def admin_list_questions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update, context):
        return
    try:
        questions = get_all_questions()
        if not questions:
            await update.message.reply_text('لا توجد أسئلة في القاعدة.')
            return
        msg = 'قائمة الأسئلة:\n'
        for q in questions:
            msg += f"{q[0]}. [{q[1]}] {q[2]} => {q[3][:30]}...\n"
        await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text(f'خطأ: {str(e)}')
        log_error(f"List questions error: {str(e)}")