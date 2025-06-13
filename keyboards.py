from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

def get_categories_markup(categories):
    keys = list(categories.keys())
    markup_arr = [keys[i:i+2] for i in range(0, len(keys), 2)]
    markup_arr.append(["اشتراك شهري", "عن المنصة"])
    markup_arr.append(["القائمة الرئيسية"])
    return ReplyKeyboardMarkup(markup_arr, resize_keyboard=True)

def get_main_menu_markup(categories):
    return get_categories_markup(categories)

def get_back_main_markup():
    # فقط زر رجوع والقائمة الرئيسية
    return ReplyKeyboardMarkup([["رجوع", "القائمة الرئيسية"]], resize_keyboard=True)

def get_about_markup():
    # فقط زر القائمة الرئيسية
    return ReplyKeyboardMarkup([["القائمة الرئيسية"]], resize_keyboard=True)

def get_payment_markup():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("تم التحويل", callback_data="paid")],
        [InlineKeyboardButton("رجوع", callback_data="back")]
    ])

def get_subscribe_confirm_markup():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("قبول الاشتراك", callback_data="sub_accept")],
        [InlineKeyboardButton("رجوع", callback_data="sub_cancel")]
    ])

def get_admin_payment_action_markup(user_id):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("نعم ✅", callback_data=f"approve_sub_{user_id}"),
            InlineKeyboardButton("رفض ❌", callback_data=f"reject_sub_{user_id}")
        ]
    ])