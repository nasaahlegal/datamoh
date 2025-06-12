import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from config import (
    WELCOME_MESSAGE, PAYMENT_TEXT, SUBSCRIPTION_TEXT, COMING_SOON_TEXT,
    FREE_QUESTIONS_LIMIT
)
from keyboards import (
    MAIN_MENU, ONLY_BACK_MARKUP, get_questions_markup,
    get_payment_markup, get_subscribe_markup
)
from questions import LEGAL_QUESTIONS
from users_data import load_user_data, save_user_data
from states_enum import States

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME_MESSAGE, reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True))
    await update.message.reply_text(COMING_SOON_TEXT)
    return States.CATEGORY

async def category_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "اشتراك شهري (أسئلة غير محدودة)":
        await update.message.reply_text(
            SUBSCRIPTION_TEXT,
            reply_markup=get_subscribe_markup()
        )
        return States.SUBSCRIBE

    if text in LEGAL_QUESTIONS:
        context.user_data['selected_cat'] = text
        questions = [q[0] for q in LEGAL_QUESTIONS[text]]
        await update.message.reply_text(
            "اختر السؤال الذي تريد معرفة إجابته:",
            reply_markup=get_questions_markup(questions)
        )
        return States.QUESTION
    else:
        await update.message.reply_text("يرجى اختيار تصنيف صحيح أو الاشتراك الشهري.", reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True))
        return States.CATEGORY

async def question_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    data = load_user_data()
    cat = context.user_data.get('selected_cat')
    question = update.message.text

    # سؤال صحيح؟
    for q, answer in LEGAL_QUESTIONS[cat]:
        if q == question:
            context.user_data['selected_q'] = (q, answer)
            user = data.get(user_id, {"free": 0, "sub": False})
            if user.get("sub") is True:
                await update.message.reply_text(f"الإجابة:\n{answer}", reply_markup=ONLY_BACK_MARKUP)
                return ConversationHandler.END
            elif user.get("free", 0) < FREE_QUESTIONS_LIMIT:
                user["free"] = user.get("free", 0) + 1
                data[user_id] = user
                save_user_data(data)
                await update.message.reply_text(
                    f"سؤالك مجاني رقم {user['free']} من {FREE_QUESTIONS_LIMIT}.\n\nالإجابة:\n{answer}",
                    reply_markup=ONLY_BACK_MARKUP
                )
                return ConversationHandler.END
            else:
                await update.message.reply_text(
                    PAYMENT_TEXT,
                    reply_markup=get_payment_markup()
                )
                return States.PAYMENT
    await update.message.reply_text("يرجى اختيار سؤال صحيح.", reply_markup=get_questions_markup([q[0] for q in LEGAL_QUESTIONS[cat]]))
    return States.QUESTION

async def payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    data = load_user_data()
    answer = context.user_data.get('selected_q', ("", "لا يوجد جواب."))
    await query.answer()
    await query.message.reply_text(f"الإجابة:\n{answer[1]}", reply_markup=ONLY_BACK_MARKUP)
    return ConversationHandler.END

async def subscription_paid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    data = load_user_data()
    data[user_id] = {"free": FREE_QUESTIONS_LIMIT, "sub": True}
    save_user_data(data)
    await query.answer()
    await query.message.reply_text("تم تفعيل اشتراكك الشهري بنجاح! يمكنك الآن طرح عدد غير محدود من الأسئلة.", reply_markup=ONLY_BACK_MARKUP)
    return ConversationHandler.END

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logging.exception("Exception in bot", exc_info=context.error)