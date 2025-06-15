from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu_markup(categories):
    keys = list(categories.keys())
    markup_arr = [keys[i:i+2] for i in range(0, len(keys), 2)]
    markup_arr.append(["اشتراك شهري", "عن المنصة"])
    markup_arr.append(["القائمة الرئيسية"])
    return ReplyKeyboardMarkup(markup_arr, resize_keyboard=True)

def get_back_main_markup():
    return ReplyKeyboardMarkup([["رجوع", "القائمة الرئيسية"]], resize_keyboard=True)

def get_about_markup():
    return ReplyKeyboardMarkup([["القائمة الرئيسية"]], resize_keyboard=True)

def get_payment_reply_markup():
    return ReplyKeyboardMarkup([["تم التحويل", "الغاء"]], resize_keyboard=True)

def get_free_confirm_markup():
    return ReplyKeyboardMarkup([["نعم"], ["رجوع", "القائمة الرئيسية"]], resize_keyboard=True)

def get_subscription_markup():
    return ReplyKeyboardMarkup([["موافق"], ["رجوع"]], resize_keyboard=True)

def get_admin_decision_markup(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ قبول", callback_data=f"accept_{user_id}"),
         InlineKeyboardButton("❌ رفض", callback_data=f"reject_{user_id}")]
    ])

def get_admin_back_markup():
    return ReplyKeyboardMarkup([["رجوع"]], resize_keyboard=True)

def get_admin_sub_actions_markup():
    return ReplyKeyboardMarkup([
        ["تمديد 3 أيام", "حذف الاشتراك"],
        ["رجوع"]
    ], resize_keyboard=True)