from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu_inline_markup(categories):
    keys = list(categories.keys())
    keyboard = []
    # أزرار التصنيفات
    for i in range(0, len(keys), 2):
        row = []
        for j in range(2):
            if i + j < len(keys):
                row.append(InlineKeyboardButton(keys[i + j], callback_data=keys[i + j]))
        keyboard.append(row)
    # أزرار الاشتراك وعن المنصة
    keyboard.append([
        InlineKeyboardButton("اشتراك شهري", callback_data="اشتراك شهري"),
        InlineKeyboardButton("عن المنصة", callback_data="عن المنصة")
    ])
    # زر العودة لمنصة محامي.كوم
    keyboard.append([
        InlineKeyboardButton("العودة الى منصة محامي.كوم", url="https://t.me/mohamy_law_bot")
    ])
    return InlineKeyboardMarkup(keyboard)

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

def get_sub_admin_options_markup(user_id):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⏳ تمديد 3 أيام", callback_data=f"extend_{user_id}"),
            InlineKeyboardButton("❌ حذف الاشتراك", callback_data=f"delete_{user_id}")
        ],
        [
            InlineKeyboardButton("⬅️ رجوع", callback_data="subs_back")
        ]
    ])