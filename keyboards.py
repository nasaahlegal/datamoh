from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

def get_categories_markup(CATEGORIES):
    return ReplyKeyboardMarkup([[cat] for cat in CATEGORIES.keys()] + [["اشتراك شهري", "حول البوت"]], resize_keyboard=True)

def get_questions_markup(questions):
    return ReplyKeyboardMarkup([[q] for q in questions] + [["رجوع"]], resize_keyboard=True)

def get_payment_markup():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("تم التحويل", callback_data="paid")],
        [InlineKeyboardButton("اشتراك شهري", callback_data="subscribe")],
        [InlineKeyboardButton("رجوع", callback_data="back")]
    ])