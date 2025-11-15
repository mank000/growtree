from datetime import datetime, timedelta, timezone

from db import models
from fsm import FSMstates
from maxapi.bot import ParseMode
from maxapi.context import MemoryContext
from maxapi.dispatcher import Router
from maxapi.filters import F
from maxapi.types import (
    BotStarted,
    BotStopped,
    ButtonsPayload,
    CallbackButton,
    Command,
    MessageButton,
    MessageCallback,
    MessageCreated,
)
from utils.lexicon import LEXICON_RU
from utils.logger import logger

logger.getChild("[APS]")


scheduler_router = Router()


async def ask_user(bot, task):
    BUTTONS_FOR_ASK = ButtonsPayload(
        buttons=[
            [
                CallbackButton(
                    text="✅ Да, выполнено",
                    payload=f"done_{task.id}",
                )
            ],
            [
                CallbackButton(
                    text="❌ Нет, позже",
                    payload=f"fail_{task.id}",
                ),
            ],
        ]
    ).pack()
    try:
        await bot.send_message(
            user_id=task.user.id,
            text=LEXICON_RU["task_question"].format(task_name=task.name),
            attachments=[BUTTONS_FOR_ASK],
            parse_mode=ParseMode.HTML,
        )
        task.status = "pending_confirmation"
        await task.save()
    except Exception as e:
        logger.exception(f"Ошибка при вопросе у юзера: {e}")


async def sweep_db(bot):
    try:
        now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
        tasks = await models.Task.filter(status="active").prefetch_related(
            "user"
        )
        for task in tasks:
            if task.end_at and task.end_at <= now:
                await ask_user(bot, task)
    except Exception as e:
        logger.exception(f"Ошибка в задаче обхода БД: {e}")


@scheduler_router.message_callback(F.callback.payload.contains("done_"))
async def task_done(event: MessageCallback, context: MemoryContext):
    try:
        task_id = int(event.callback.payload.replace("done_", ""))
        task = await models.Task.get(id=task_id)
        tree = await models.Tree.get(task=task)
        tree.status = "active"
        task.status = "success"
        await tree.save()
        await task.save()

        await event.message.delete()
        await context.set_state(FSMstates.is_asking_for_periodic)
        await context.update_data(
            completed_task_id=str(task.id), completed_task_name=task.name
        )

        await event.message.answer(
            text=LEXICON_RU["sucess_task"].format(task_name=task.name),
            attachments=[
                ButtonsPayload(
                    buttons=[
                        [
                            CallbackButton(
                                text="🔄 Начать заново",
                                payload="restart_task",
                            )
                        ],
                    ]
                ).pack(),
            ],
        )
    except Exception as e:
        logger.error(f"Ошибка при подтверждении task_done {e}")


@scheduler_router.message_callback(F.callback.payload.contains("fail_"))
async def task_fail(event: MessageCallback, context: MemoryContext):
    try:
        task_id = int(event.callback.payload.replace("fail_", ""))
        task = await models.Task.get(id=task_id)
        tree = await models.Tree.get(task=task)
        task.status = "failed"
        tree.status = "died"
        await tree.save()
        await task.save()
        await event.message.delete()
        await context.set_state(FSMstates.is_asking_for_periodic)
        await context.update_data(
            completed_task_id=str(task.id), completed_task_name=task.name
        )

        await event.message.answer(
            text=LEXICON_RU["failed_task"].format(task_name=task.name),
            attachments=[
                ButtonsPayload(
                    buttons=[
                        [
                            CallbackButton(
                                text="🔄 Начать заново",
                                payload="restart_task",
                            )
                        ],
                    ]
                ).pack(),
            ],
        )
    except Exception as e:
        logger.error(f"Ошибка при подтверждении task_fail {e}")


@scheduler_router.message_callback(
    F.callback.payload.contains("restart_task")
)
async def restart_task_handler(
    event: MessageCallback, context: MemoryContext
):
    try:
        await event.message.delete()
        data = await context.get_data()
        task_name = data.get("completed_task_name")

        await event.message.answer(
            text=f"🔄 Начинаем «{task_name}» заново!\n\n"
            "⏰ Сколько минут потребуется на задачу?",
            attachments=[
                ButtonsPayload(
                    buttons=[
                        [
                            CallbackButton(text="10 мин", payload="time_10"),
                            CallbackButton(text="25 мин", payload="time_25"),
                        ],
                        [
                            CallbackButton(text="45 мин", payload="time_45"),
                            CallbackButton(text="60 мин", payload="time_60"),
                        ],
                        [
                            CallbackButton(
                                text="Другое время", payload="custom_time"
                            ),
                        ],
                    ]
                ).pack(),
            ],
        )
    except Exception as e:
        logger.error(f"Ошибка при restart_task_handler {e}")


@scheduler_router.message_callback(F.callback.payload.startswith("time_"))
async def set_task_time(event: MessageCallback, context: MemoryContext):
    try:
        await event.message.delete()
        minutes = event.callback.payload.split("_")[1]
        data = await context.get_data()
        task_name = data.get("completed_task_name")

        user = await models.User.get(id=event.from_user.user_id)
        start_time = datetime.now(timezone.utc)
        end_time = start_time + timedelta(minutes=int(minutes))

        new_task = await models.Task.create(
            name=task_name,
            start_at=start_time,
            end_at=end_time,
            user=user,
            status="active",
        )

        # Создаем новое дерево для задачи
        await models.Tree.create(
            type_tree=user.chosen_tree,
            user=user,
            task=new_task,
            status="alive",
        )

        await event.message.answer(
            text=f"🌱 Задача «{task_name}» начата заново!\n\n"
            f"⏰ Время: {minutes} минут\n"
        )
        await context.clear()

    except Exception as e:
        logger.error(f"Ошибка при set_task_time {e}")


@scheduler_router.message_callback(F.callback.payload == "custom_time")
async def ask_custom_time(event: MessageCallback, context: MemoryContext):
    await event.message.answer(
        text="⏰ Напиши, сколько минут нужно на задачу:\n\n"
        "Например: 15, 30, 90"
    )
    await context.set_state(FSMstates.is_setting_custom_time)


@scheduler_router.message_created(FSMstates.is_setting_custom_time)
async def process_custom_time(event: MessageCreated, context: MemoryContext):
    try:
        await event.message.delete()
        minutes = int(event.message.body.text)
        if minutes <= 0:
            await event.message.answer("❌ Введи положительное число минут")
            return

        data = await context.get_data()
        task_name = data.get("completed_task_name")

        user = await models.User.get(id=event.from_user.user_id)
        start_time = datetime.now(timezone.utc)
        end_time = start_time + timedelta(minutes=minutes)

        new_task = await models.Task.create(
            name=task_name,
            start_at=start_time,
            end_at=end_time,
            user=user,
            status="active",
        )

        await models.Tree.create(
            type_tree=user.chosen_tree,
            user=user,
            task=new_task,
            status="alive",
        )

        await event.message.answer(
            text=f"🌱 Задача «{task_name}» начата заново!\n\n"
            f"⏰ Время: {minutes} минут\n"
        )

        await context.clear()

    except ValueError:
        await event.message.answer(
            "❌ Пожалуйста, введи число минут (только цифры)"
        )
    except Exception as e:
        logger.error(f"Ошибка при process_custom_time {e}")
