from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu_markup(categories):
    """لوحة المفاتيح الرئيسية مع التصنيفات"""
    keys = list(categories.keys())
    markup_arr = [keys[i:i+2] for i in range(0, len(keys), 2)]
    markup_arr.append(["اشتراك شهري", "عن المنصة"])
    markup_arr.append(["القائمة الرئيسية"])
    return ReplyKeyboardMarkup(markup_arr, resize_keyboard=True)

def get_back_main_markup():
    """زر الرجوع والقائمة الرئيسية"""
    return ReplyKeyboardMarkup([["رجوع", "القائمة الرئيسية"]], resize_keyboard=True)

def get_about_markup():
    """لوحة مفاتيح شاشة 'عن المنصة'"""
    return ReplyKeyboardMarkup([["القائمة الرئيسية"]], resize_keyboard=True)

def get_payment_reply_markup():
    """لوحة مفاتيح تأكيد الدفع"""
    return ReplyKeyboardMarkup([["تم التحويل", "الغاء"]], resize_keyboard=True)

def get_free_confirm_markup():
    """لوحة مفاتيح تأكيد استخدام السؤال المجاني"""
    return ReplyKeyboardMarkup([["نعم"], ["رجوع", "القائمة الرئيسية"]], resize_keyboard=True)

def get_subscription_markup():
    """لوحة مفاتيح تأكيد الاشتراك"""
    return ReplyKeyboardMarkup([["موافق"], ["رجوع"]], resize_keyboard=True)

def get_admin_decision_markup(user_id):
    """لوحة مفاتيح للمشرف لقبول/رفض طلب اشتراك"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ قبول", callback_data=f"accept_{user_id}"),
         InlineKeyboardButton("❌ رفض", callback_data=f"reject_{user_id}")]
    ])

def get_admin_back_markup():
    """زر الرجوع لواجهة المشرفين"""
    return ReplyKeyboardMarkup([["رجوع"]], resize_keyboard=True)

def get_admin_sub_actions_markup():
    """أزرار إدارة الاشتراكات للمشرفين"""
    return ReplyKeyboardMarkup([
        ["تمديد 3 أيام", "حذف الاشتراك"],
        ["رجوع"]
    ], resize_keyboard=True)