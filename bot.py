# main bot logic
from handlers import admin, user, payment
from aiogram import executor
from users import dp

if __name__ == "__main__":
    from handlers import admin, user, payment
    executor.start_polling(dp, skip_updates=True)
