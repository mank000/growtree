from maxapi.context import MemoryContext
from maxapi.dispatcher import Router
from maxapi.types import MessageCreated
from utils.lexicon import LEXICON_RU

Erouter = Router()


@Erouter.message_created()
async def unknown_message(event: MessageCreated, context: MemoryContext):
    await event.message.answer(
        text=LEXICON_RU["error_ms"].format(
            username=event.from_user.first_name
        )
    )
