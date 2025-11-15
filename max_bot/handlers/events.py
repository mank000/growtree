from db import models
from fsm import FSMstates
from maxapi import filters
from maxapi.context import MemoryContext
from maxapi.dispatcher import Router
from maxapi.filters import F
from maxapi.types import (
    ButtonsPayload,
    CallbackButton,
    Command,
    MessageButton,
    MessageCallback,
    MessageCreated,
)
from maxapi.utils.inline_keyboard import InlineKeyboardBuilder
from utils.lexicon import LEXICON_RU

event_router = Router()


# @event_router.message_created(FSMstates.task_written)
# async def time_task(event: MessageCreated, context: MemoryContext):
#     builder = InlineKeyboardBuilder()
#     builder.row(
#         CallbackButton(text="10", payload="10"),
#         CallbackButton(text="15", payload="15"),
#         CallbackButton(text="30", payload="30"),
#         CallbackButton(text="45", payload="45"),
#         CallbackButton(text="60", payload="60"),
#     )
#     builder.row(
#         MessageButton(text="/cancel"),
#     )
#     await event.bot.send_message(
#         chat_id=event.chat.chat_id,
#         text=LEXICON_RU["new_task_time"],
#         attachments=[builder.as_markup()],
#     )
#     await context.set_state(FSMstates.to_time_writer)


# @event_router.message_created(FSMstates.to_time_writer)
# async def time_writer(event: MessageCreated, context: MemoryContext):
#     await event.bot.send_message(
#         chat_id=event.chat.chat_id,
#         text=LEXICON_RU["time_chosen"],
#     )
#     await context.set_state(FSMstates.time_written)


# @event_router.message_callback(
#     F.callback.payload.in_(["10", "15", "30", "45", "60"]),
#     FSMstates.to_time_writer,
# )
# async def time_writer_second(event: MessageCreated, context: MemoryContext):
#     await event.bot.send_message(
#         chat_id=event.chat.chat_id,
#         text=LEXICON_RU["time_chosen"],
#     )
#     await context.set_state(FSMstates.time_written)


# @event_router.message_created(FSMstates.time_written)
# async def plant_tree_task(event: MessageCreated, context: MemoryContext):
#     buttons_tree = [
#         [
#             CallbackButton(
#                 text="Посадить" + LEXICON_RU["standard_tree"],
#                 payload="standard_tree",
#             )
#         ],
#         [
#             CallbackButton(
#                 text="Посадить" + LEXICON_RU["fir_tree"], payload="fir_tree"
#             )
#         ],
#         [
#             CallbackButton(
#                 text="Посадить" + LEXICON_RU["palm_tree"], payload="palm_tree"
#             )
#         ],
#         [
#             CallbackButton(
#                 text="Посадить" + LEXICON_RU["cactus"], payload="cactus"
#             )
#         ],
#     ]
#     payload_tree = ButtonsPayload(buttons=buttons_tree).pack()
#     await event.bot.send_message(
#         chat_id=event.chat.chat_id,
#         text=LEXICON_RU["tree_text"],
#         attachments=[payload_tree],
#     )
#     await context.set_state(FSMstates.in_active_task)


# @event_router.message_callback(
#     F.callback.payload.in_(
#         ["standard_tree", "fir_tree", "palm_tree", "cactus"]
#     ),
#     FSMstates.in_active_task,
# )
# async def task_added(event: MessageCallback, context: MemoryContext):
#     user = await models.User.get(id=event.from_user.user_id)
#     if not user:
#         await event.bot.send_message(
#             chat_id=event.chat.chat_id, text="Пользователь не найден."
#         )
#         return

#     user.chosen_tree = event.callback.payload
#     await user.save()

#     await event.message.delete()

#     await event.bot.send_message(
#         chat_id=event.chat.chat_id,
#         text=LEXICON_RU["cancel_task"],
#     )
#     await context.set_state(None)
