from aiogram import Bot, Dispatcher
from config import TOKEN
from aiogram.contrib.fsm_storage.memory import MemoryStorage

bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
