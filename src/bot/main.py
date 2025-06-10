import sys
sys.path.append('../') # src/

from config import settings

from handlers import common, admin, orders, generations
from handlers.forms import create_order_form

from schedules import scheduler

from aiogram import Bot, Dispatcher, F
from aiogram.fsm.storage.memory import MemoryStorage

import asyncio
import threading


async def main() -> None:
    # Bot
    bot = Bot(token=settings.telegram_bot_token)
    dp = Dispatcher(storage=MemoryStorage())

    # Handlers routers
    dp.include_router(common.router)
    dp.include_router(admin.router)
    dp.include_router(orders.router)
    dp.include_router(generations.router)

    # Forms routers
    dp.include_router(create_order_form.router)
    
    # Others
    threading.Thread(target=scheduler, name='schedule', daemon=True).start()

    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, RuntimeError):
        print('Bot has been stopped.')
