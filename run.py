import asyncio
import logging
from aiogram import Bot, Dispatcher
from sqlalchemy import text

from config import TOKEN
from app.handlers import router
from app.admin_handlers import router as admin_router
from app.report import router as report_router
from app.database.models import async_session, engine, Base
from app.database.Init import initialize_reference_data

from sqlalchemy import text

bot = Bot(token=TOKEN)
dp = Dispatcher()

async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session() as session:
        await initialize_reference_data(session)

    #подключение роутеров в боте
    dp.include_router(admin_router)
    dp.include_router(router)
    dp.include_router(report_router)

    #Подключение бота
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Отключен')
