from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

def get_categories_markup(categories):
    keys = list(categories.keys())
    markup_arr = [keys[i:i+2] for i in range(0, len(keys), 2)]
    markup_arr.append(["اشتراك شهري", "عن المنصة"])
    markup_arr.append(["القائمة الرئيسية"])
    return ReplyKeyboardMarkup(markup_arr, resize_keyboard=True)

def get_main_menu_markup(categories):
    return get_categories_markup(categories)

def get_lawyer_platform_markup(categories):
    keys = list(categories.keys())
    markup_arr = [keys[i:i+2] for i in range(0, len(keys), 2)]
    markup_arr.append(["اشتراك شهري", "عن المنصة"])
    markup_arr.append(["العودة إلى منصة محامي.كوم"])
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

def get_admin_menu_markup():
    return ReplyKeyboardMarkup([
        ["إدارة المشتركين", "إدارة الأسئلة"],
        ["القائمة الرئيسية"]
    ], resize_keyboard=True)

def get_questions_list_markup(qs):
    markup_arr = [[q[0]] for q in qs]
    markup_arr.append(["إضافة سؤال جديد"])
    markup_arr.append(["رجوع"])
    return ReplyKeyboardMarkup(markup_arr, resize_keyboard=True)

def get_question_manage_markup():
    return ReplyKeyboardMarkup([
        ["تعديل السؤال", "حذف السؤال"],
        ["رجوع"]
    ], resize_keyboard=True)