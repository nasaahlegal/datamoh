from telegram import ReplyKeyboardMarkup, KeyboardButton

def get_main_menu_markup():
    return ReplyKeyboardMarkup(
        [["القائمة الرئيسية"]],
        resize_keyboard=True
    )

def get_back_main_markup():
    return ReplyKeyboardMarkup(
        [["رجوع", "القائمة الرئيسية"]],
        resize_keyboard=True
    )

def get_payment_reply_markup():
    return ReplyKeyboardMarkup(
        [["تم التحويل", "الغاء"]],
        resize_keyboard=True
    )

def get_about_markup():
    return ReplyKeyboardMarkup(
        [["القائمة الرئيسية"]],
        resize_keyboard=True
    )

def get_free_confirm_markup():
    return ReplyKeyboardMarkup(
        [["نعم", "رجوع", "القائمة الرئيسية"]],
        resize_keyboard=True
    )

def get_subscription_markup():
    return ReplyKeyboardMarkup(
        [["موافق", "رجوع"]],
        resize_keyboard=True
    )

def get_lawyer_platform_markup(categories):
    # categories: list of category strings
    buttons = [[cat] for cat in categories]
    buttons.append(["اشتراك شهري"])
    buttons.append(["عن المنصة"])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)