# -*- coding: utf-8 -*-
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import Router
from handlers import register_handlers
from utils import API_TOKEN

# Настройка логирования
logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

# Регистрация обработчиков
register_handlers(router, bot)

if __name__ == '__main__':
    dp.run_polling(bot)