from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

MAIN_CATEGORIES = [
    "جنائي", "مدني", "الأسرة", "الوظيفة والعمل", "عن المنصة", "اشتراك شهري", "القائمة الرئيسية", "العودة إلى منصة محاميكم"
]

SUB_CATEGORIES = {
    "مدني": ["عقارات"],
    "الأسرة": ["الزواج", "الطلاق", "النفقة", "الحضانة", "النسب"],
    "الوظيفة والعمل": ["قضايا الموظفين", "القطاع الخاص"]
}

def get_categories_markup(categories):
    markup_arr = []
    for cat in MAIN_CATEGORIES[:4]:  # جنائي، مدني، الأسرة، الوظيفة والعمل
        markup_arr.append([cat])
    markup_arr.append([MAIN_CATEGORIES[4], MAIN_CATEGORIES[5]])  # عن المنصة، اشتراك شهري
    markup_arr.append([MAIN_CATEGORIES[6]])  # القائمة الرئيسية
    markup_arr.append([MAIN_CATEGORIES[7]])  # العودة إلى منصة محاميكم
    return ReplyKeyboardMarkup(markup_arr, resize_keyboard=True)

def get_subcategories_markup(main_category):
    subcats = SUB_CATEGORIES.get(main_category, [])
    if subcats:
        markup_arr = [[sub] for sub in subcats]
        markup_arr.append(["رجوع", "القائمة الرئيسية"])
        return ReplyKeyboardMarkup(markup_arr, resize_keyboard=True)
    return get_categories_markup({})  # fallback

def get_main_menu_markup(categories):
    return get_categories_markup(categories)

def get_lawyer_platform_markup(categories):
    return get_categories_markup(categories)

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

def get_pay_confirm_markup():
    return ReplyKeyboardMarkup([["نعم"], ["لا", "رجوع"]], resize_keyboard=True)

def get_admin_decision_markup(user_id, req_type="sub"):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ قبول", callback_data=f"accept_{req_type}_{user_id}"),
            InlineKeyboardButton("❌ رفض", callback_data=f"reject_{req_type}_{user_id}")
        ]
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

def get_choose_payment_method_markup():
    return ReplyKeyboardMarkup(
        [["التحويل اليدوي", "الدفع الإلكتروني"], ["رجوع", "القائمة الرئيسية"]],
        resize_keyboard=True
    )