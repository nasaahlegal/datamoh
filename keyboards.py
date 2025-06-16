# keyboards
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_menu = ReplyKeyboardMarkup(resize_keyboard=True)
main_menu.add(KeyboardButton("📝 إرسال سؤال"), KeyboardButton("ℹ️ المساعدة"))
