import asyncio
import logging
from aiogram import Bot, Dispatcher, BaseMiddleware
from aiogram.client.default import DefaultBotProperties
from config import config
from db.connection import create_tables, get_session
from handlers import register_handlers
from utils.scheduler import setup_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DBSessionMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        async for session in get_session():
            data['session'] = session
            return await handler(event, data)

async def main():
    config.validate()

    bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()

    # Создать таблицы
    await create_tables()

    # Middleware для сессии
    dp.message.middleware(DBSessionMiddleware())
    dp.callback_query.middleware(DBSessionMiddleware())

    # Регистрировать handlers
    register_handlers(dp)

    # Настроить scheduler
    scheduler = setup_scheduler(bot)
    scheduler.start()

    try:
        logger.info("Bot started")
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("Bot stopped")
    finally:
        scheduler.shutdown()

if __name__ == "__main__":
    asyncio.run(main())