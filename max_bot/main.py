import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import BOT_TOKEN, TORTOISE_ORM
from handlers import commands, errors, events, start
from maxapi import Bot, Dispatcher
from maxapi.types import BotCommand, PhotoAttachmentRequestPayload
from scheduler.scheduler import scheduler_router, sweep_db
from tortoise import Tortoise
from utils.lexicon import LEXICON_RU
from utils.logger import logger
from utils.wait_services import wait_for_services

logger = logger.getChild("polling")
bot = Bot(BOT_TOKEN)
dp = Dispatcher()


async def main():
    await wait_for_services()
    await Tortoise.init(config=TORTOISE_ORM)
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    scheduler.add_job(
        sweep_db,
        "interval",
        # minutes=1,
        seconds=30,
        id="db_sweep",
        max_instances=1,
        coalesce=True,
        replace_existing=True,
        kwargs={"bot": bot},
    )
    scheduler.start()
    await bot.change_info(
        first_name="Леший",
        description=LEXICON_RU["description"],
        commands=[
            BotCommand(name="plant", descripton="Создать новую задачу"),
            BotCommand(name="profile", descripton="Профиль"),
            BotCommand(name="tasks", descripton="Все задачи"),
        ],
        photo=PhotoAttachmentRequestPayload(
            url="https://mifolog.com/wp-content/uploads/2021/05/https-ufologov-net-wp-content-uploads-7-f-e-7fe5.jpeg"
        ),
    )
    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown(wait=False)
        await Tortoise.close_connections()


dp.include_routers(commands.command_router)
dp.include_routers(start.st_router)
dp.include_routers(scheduler_router)
dp.include_routers(events.event_router)
dp.include_routers(errors.Erouter)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    finally:
        pass
