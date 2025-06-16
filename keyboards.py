from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

def get_lawyer_platform_markup(categories):
    keys = list(categories.keys())
    markup = [keys[i:i+2] for i in range(0, len(keys), 2)]
    markup.append(["القائمة الرئيسية"])
    return ReplyKeyboardMarkup(markup, resize_keyboard=True)

def get_back_main_markup():
    return ReplyKeyboardMarkup([["رجوع", "القائمة الرئيسية"]], resize_keyboard=True)

def get_free_confirm_markup():
    return ReplyKeyboardMarkup([["نعم"], ["رجوع"]], resize_keyboard=True)

def get_payment_reply_markup():
    return ReplyKeyboardMarkup([["تم التحويل", "الغاء"]], resize_keyboard=True)

def get_sub_admin_options_markup(user_id):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⏳ تمديد 3 أيام", callback_data=f"extend_{user_id}"),
            InlineKeyboardButton("❌ حذف الاشتراك", callback_data=f"delete_{user_id}")
        ],
        [InlineKeyboardButton("⬅️ رجوع", callback_data="subs_back")]
    ])
