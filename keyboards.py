from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

LEGAL_CATEGORIES = [
    "أحوال شخصية",
    "عقارات",
    "عمل",
    "جنائي",
    "مرور",
    "أخرى"
]

MAIN_MENU = [[cat] for cat in LEGAL_CATEGORIES] + [["اشتراك شهري (أسئلة غير محدودة)"]]

BACK_TO_MENU = [[KeyboardButton("العودة إلى القائمة الرئيسية")]]
ONLY_BACK_MARKUP = ReplyKeyboardMarkup(BACK_TO_MENU, resize_keyboard=True)
def get_questions_markup(questions):
    return ReplyKeyboardMarkup([[q] for q in questions] + BACK_TO_MENU, resize_keyboard=True)

def get_payment_markup():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("تم التحويل", callback_data="paid")]
    ])

def get_subscribe_markup():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("تم الاشتراك", callback_data="sub_paid")]
    ])