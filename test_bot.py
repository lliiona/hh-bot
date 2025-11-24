import asyncio
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    logger.info("🚀 Запуск тестового бота...")
    
    # Загружаем токен
    from dotenv import load_dotenv
    import os
    load_dotenv()
    
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN не найден в .env файле")
        return
    
    # Пробуем подключить БД
    db_status = "❌ Не подключена"
    try:
        from db.connection import create_tables
        success = await create_tables()
        if success:
            db_status = "✅ Подключена"
        else:
            db_status = "⚠️ Ошибка при создании таблиц"
    except Exception as e:
        logger.warning(f"⚠️ База данных не подключена: {e}")
        db_status = f"❌ Ошибка: {str(e)[:50]}..."
    
    # Создаем бота
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    
    @dp.message(Command("start"))
    async def cmd_start(message: types.Message):
        await message.answer(
            f"🤖 Тестовый бот работает!\n"
            f"📊 База данных: {db_status}\n"
            f"🆔 Ваш ID: {message.from_user.id}\n\n"
            f"Команды:\n"
            f"/start - эта информация\n"
            f"/test - тестовая команда\n"
            f"/db - статус базы данных"
        )
    
    @dp.message(Command("test"))
    async def cmd_test(message: types.Message):
        await message.answer("✅ Тест пройден! Бот отвечает на команды.")
    
    @dp.message(Command("db"))
    async def cmd_db(message: types.Message):
        await message.answer(f"📊 Статус базы данных: {db_status}")
    
    @dp.message()
    async def echo(message: types.Message):
        await message.answer(f"📨 Эхо: {message.text}")
    
    logger.info("🎯 Бот готов к работе!")
    logger.info("💬 Тестируйте команды: /start, /test, /db")
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен")
