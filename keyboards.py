from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

def get_categories_markup(categories):
    return ReplyKeyboardMarkup([[cat] for cat in categories.keys()] + [["اشتراك شهري", "عن البوت"]], resize_keyboard=True)

def get_questions_markup(questions):
    return ReplyKeyboardMarkup([[q] for q in questions] + [["رجوع"]], resize_keyboard=True)

def get_payment_markup():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("تم التحويل", callback_data="paid")],
        [InlineKeyboardButton("إلغاء", callback_data="cancel")]
    ])

def get_admin_payment_action_markup(user_id):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("نعم ✅", callback_data=f"approve_sub_{user_id}"),
            InlineKeyboardButton("رفض ❌", callback_data=f"reject_sub_{user_id}")
        ]
    ])