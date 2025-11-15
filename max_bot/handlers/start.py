from datetime import datetime, timedelta, timezone

from db import models
from fsm import FSMstates
from maxapi import filters
from maxapi.bot import ParseMode
from maxapi.context import MemoryContext
from maxapi.dispatcher import Event, Router
from maxapi.exceptions.dispatcher import MiddlewareException
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
from maxapi.utils.inline_keyboard import InlineKeyboardBuilder
from utils.lexicon import LEXICON_RU
from utils.logger import logger

st_router = Router()


@st_router.bot_started(BotStarted)
async def on_bot_started(event, context: MemoryContext):
    # Добавляем пользователя в бд
    user, created = await models.User.get_or_create(
        id=event.from_user.user_id
    )
    await event.bot.send_message(
        chat_id=event.chat.chat_id,
        text=LEXICON_RU["start"].format(username=event.from_user.first_name),
    )
    await context.set_state(FSMstates.is_choosing_goal)


@st_router.message_created(Command("plant"))
@st_router.message_created(FSMstates.is_choosing_goal)
async def event_message(event: MessageCreated, context: MemoryContext):
    await event.message.delete()
    user = await models.User.get(id=event.from_user.user_id)
    await user.save()
    await context.set_state(FSMstates.is_choosing_tree)
    if await user.tasks.all().exists():
        return await event.message.answer(
            LEXICON_RU["chose_goal_sec"],
            parse_mode=ParseMode.HTML,
        )
    await event.message.answer(
        LEXICON_RU["chose_goal"],
        parse_mode=ParseMode.HTML,
    )


@st_router.message_created(FSMstates.is_choosing_tree)
async def choosing_tree(event: MessageCreated, context: MemoryContext):
    await event.message.delete()
    user = await models.User.get(id=event.from_user.user_id)
    buttons_tree = [
        [
            CallbackButton(
                text="Посадить" + LEXICON_RU["standard_tree"],
                payload="standard_tree",
            )
        ],
        [
            CallbackButton(
                text="Посадить" + LEXICON_RU["fir_tree"],
                payload="fir_tree",
            )
        ],
        [
            CallbackButton(
                text="Посадить" + LEXICON_RU["palm_tree"],
                payload="palm_tree",
            )
        ],
        [
            CallbackButton(
                text="Посадить" + LEXICON_RU["cactus"],
                payload="cactus",
            )
        ],
    ]
    payload_tree = ButtonsPayload(buttons=buttons_tree).pack()
    if user.trees.all().exists():
        await event.bot.send_message(
            chat_id=event.chat.chat_id,
            text=LEXICON_RU["tree_text_sec"],
            attachments=[payload_tree],
            parse_mode=ParseMode.MARKDOWN,
        )
    else:
        await event.bot.send_message(
            chat_id=event.chat.chat_id,
            text=LEXICON_RU["tree_text_first"],
            attachments=[payload_tree],
            parse_mode=ParseMode.MARKDOWN,
        )
    await context.set_state(FSMstates.is_writing_task)
    await context.update_data(name=event.message.body.text)


@st_router.message_callback(FSMstates.is_writing_task)
async def first_time_task(event: MessageCallback, context: MemoryContext):
    await event.message.delete()
    builder = InlineKeyboardBuilder()
    builder.row(
        CallbackButton(text="10", payload="10"),
        CallbackButton(text="15", payload="15"),
        CallbackButton(text="30", payload="30"),
        CallbackButton(text="45", payload="45"),
        CallbackButton(text="60", payload="60"),
    )
    await context.set_state(FSMstates.is_choosing_time)
    await context.update_data(tree_type=event.callback.payload)
    await event.message.answer(
        text=LEXICON_RU["first_task_time"],
        attachments=[builder.as_markup()],
        parse_mode=ParseMode.HTML,
    )


@st_router.message_callback(
    FSMstates.is_choosing_time,
    F.callback.payload.in_(["10", "15", "30", "45", "60"]),
)
async def end_first_time_task(event: MessageCallback, context: MemoryContext):
    await event.message.delete()
    data = await context.get_data()
    user = await models.User.get(id=event.from_user.user_id)
    task = await models.Task.create(
        name=data.get("name"),
        end_at=datetime.now(timezone.utc).replace(second=0)
        + timedelta(minutes=int(event.callback.payload)),
        user=user,
    )
    await models.Tree.create(
        type_tree=data["tree_type"],
        user=user,
        task=task,
    )
    await event.message.answer(
        text=LEXICON_RU["success_task"].format(
            name=data.get("name"), time=event.callback.payload
        ),
        parse_mode=ParseMode.MARKDOWN,
    )
    await context.clear()


@st_router.message_created(FSMstates.is_choosing_time)
async def end_first_time_task_message(
    event: MessageCreated, context: MemoryContext
):
    await event.message.delete()
    text = event.message.body.text.strip()
    if text.isdigit():
        await context.update_data(time=text)
        data = await context.get_data()
        user = await models.User.get(id=event.from_user.user_id)
        task = await models.Task.create(
            name=data.get("name"),
            end_at=datetime.now(timezone.utc).replace(second=0)
            + timedelta(
                minutes=int(
                    data.get("time"),
                )
            ),
            user=user,
        )
        await models.Tree.create(
            type_tree=data["tree_type"],
            user=user,
            task=task,
        )
        await event.message.answer(
            text=LEXICON_RU["success_task"].format(
                name=data.get("name"), time=event.message.body.text
            ),
            parse_mode=ParseMode.MARKDOWN,
        )
        await context.clear()
    else:
        await event.message.answer(LEXICON_RU["time_error"])


@st_router.bot_stopped(BotStopped)
async def on_bot_stopped(event: Event):
    # Удаляем пользователя из бд.
    try:
        user = await models.User.get(id=event.from_user.user_id)
        await user.delete()
    except MiddlewareException:
        pass
