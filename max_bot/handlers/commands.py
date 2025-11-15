from datetime import datetime, timezone

from db import models
from fsm import FSMstates
from maxapi import filters
from maxapi.bot import ParseMode
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

command_router = Router()


@command_router.message_created(Command("cancel"))
async def cancel_task(event: MessageCreated, context: MemoryContext):
    await event.bot.send_message(
        chat_id=event.chat.chat_id, text=LEXICON_RU["cancel"]
    )
    await context.clear()


@command_router.message_created(Command("profile"))
async def profile(event: MessageCreated, context: MemoryContext):
    user = await models.User.get(id=event.from_user.user_id).prefetch_related(
        "trees", "tasks"
    )
    buttons_tree = [
        [
            CallbackButton(
                text="Изменить цель",
                payload="change_goal",
            )
        ],
    ]
    payload_tree = ButtonsPayload(buttons=buttons_tree).pack()

    # Собираем деревья по статусам
    alive_trees = [t for t in user.trees if t.status == "active"]
    active_trees = [t for t in user.trees if t.status == "alive"]
    died_trees = [t for t in user.trees if t.status == "died"]

    # Статистика по задачам
    completed_tasks = len([t for t in user.tasks if t.status == "success"])
    active_tasks = len([t for t in user.tasks if t.status == "active"])

    # Создаем визуализацию леса
    forest_visualization = ""

    # Живые деревья (по типам)
    if alive_trees:
        forest_visualization += "*Живой лес:*\n"
        for tree in alive_trees:
            if tree.type_tree == "standard_tree":
                forest_visualization += "🌳 "  # Дуб
            elif tree.type_tree == "fir_tree":
                forest_visualization += "🌲 "  # Ель
            elif tree.type_tree == "palm_tree":
                forest_visualization += "🌴 "  # Пальма
            elif tree.type_tree == "cactus":
                forest_visualization += "🌵 "  # Кактус
            else:
                forest_visualization += "🌳 "  # Дефолт
        forest_visualization += "\n\n"

    # Активные ростки
    if active_trees:
        forest_visualization += "*Ростки:*\n"
        forest_visualization += "🌱 " * len(active_trees)
        forest_visualization += "\n\n"

    # Погибшие деревья
    if died_trees:
        forest_visualization += "*Погибшие:*\n"
        forest_visualization += "🪵 " * len(died_trees)
        forest_visualization += "\n\n"

    # Если лес пустой
    if not alive_trees and not active_trees and not died_trees:
        forest_visualization = "🪨 _Здесь пока нет деревьев..._\n_Посади первое дерево командой /plant_ 🌱\n\n"

    profile_text = (
        "🌿 *Лесная опушка путника* 🍂\n\n"
        # f"🎯 *Цель:* {user.goal}\n"
        f"📊 *Статистика леса:*\n"
        f"• Живых: {len(alive_trees)}\n"
        f"• Ростков: {len(active_trees)}\n"
        f"• Погибших: {len(died_trees)}\n"
        f"• ✅ Задач выполнено: {completed_tasks}\n\n"
        f"{forest_visualization}"
        f"📅 *В лесу с:* {user.created_at.strftime('%d.%m.%Y')}\n\n"
        "_Каждое дерево — твоё достижение!_ ✨"
    )
    await context.clear()
    await event.message.answer(
        profile_text,
        parse_mode=ParseMode.MARKDOWN,
    )


@command_router.message_created(Command("tasks"))
async def tasks(event: MessageCreated, context: MemoryContext):
    user = await models.User.get(id=event.from_user.user_id).prefetch_related(
        "tasks"
    )

    active_tasks = [t for t in user.tasks if t.status == "active"]
    completed_tasks = [t for t in user.tasks if t.status == "success"]
    failed_tasks = [t for t in user.tasks if t.status == "failed"]

    active_tasks.sort(key=lambda x: x.start_at, reverse=True)
    completed_tasks.sort(
        key=lambda x: x.last_completed_at or x.start_at, reverse=True
    )
    failed_tasks.sort(key=lambda x: x.end_at or x.start_at, reverse=True)

    message_text = "📋 *Твои лесные дела* 🍃\n\n"

    if active_tasks:
        message_text += "🌱 *Активные ростки:*\n"
        for i, task in enumerate(active_tasks, 1):
            time_info = ""
            if task.end_at:
                now_aware = datetime.now(timezone.utc)
                if task.end_at.tzinfo is None:
                    task_end_aware = task.end_at.replace(tzinfo=timezone.utc)
                else:
                    task_end_aware = task.end_at

                time_left = task_end_aware - now_aware
                if time_left.total_seconds() > 0:
                    hours = int(time_left.total_seconds() // 3600)
                    minutes = int((time_left.total_seconds() % 3600) // 60)
                    if hours > 0:
                        time_info = f" ⏰ {hours}ч {minutes}м"
                    else:
                        time_info = f" ⏰ {minutes}м"
                else:
                    time_info = " 🔥 время вышло!"

            message_text += f"{i}. {task.name}{time_info}\n"
        message_text += "\n"
    else:
        message_text += "🌱 *Активных задач пока нет*\n\n"

    if completed_tasks:
        message_text += "🌳 *Выполненные деревья:*\n"
        for i, task in enumerate(completed_tasks[:8], 1):
            date_info = ""
            if task.last_completed_at:
                date_info = f" 📅 {task.last_completed_at.strftime('%d.%m')}"

            message_text += f"{i}. ✅ {task.name}{date_info}\n"

        if len(completed_tasks) > 8:
            message_text += (
                f"\n... и ещё {len(completed_tasks) - 8} выполненных дел\n"
            )
        message_text += "\n"
    else:
        message_text += "🌳 *Выполненных задач пока нет*\n\n"

    if failed_tasks:
        message_text += "🪵 *Погибшие саженцы:*\n"
        for i, task in enumerate(failed_tasks[:5], 1):
            # Показываем причину провала (просрочка)
            reason = ""
            if task.end_at:
                now_aware = datetime.now(timezone.utc)
                if task.end_at.tzinfo is None:
                    task_end_aware = task.end_at.replace(tzinfo=timezone.utc)
                else:
                    task_end_aware = task.end_at

                if task_end_aware < now_aware:
                    reason = ""

            message_text += f"{i}. ❌ {task.name}{reason}\n"

        if len(failed_tasks) > 5:
            message_text += (
                f"\n... и ещё {len(failed_tasks) - 5} невыполненных дел\n"
            )
        message_text += "\n"
    else:
        message_text += "✨ *Погибших саженцев нет — отлично!*\n\n"

    total_tasks = len(active_tasks) + len(completed_tasks) + len(failed_tasks)
    if total_tasks > 0:
        completion_rate = (
            (len(completed_tasks) / total_tasks) * 100
            if total_tasks > 0
            else 0
        )
        message_text += f"📊 *Статистика леса:*\n"
        message_text += f"• Всего дел: {total_tasks}\n"
        message_text += f"• 🌱 Активных: {len(active_tasks)}\n"
        message_text += f"• 🌳 Выполнено: {len(completed_tasks)}\n"
        message_text += f"• 🪵 Погибло: {len(failed_tasks)}\n"
        message_text += f"• 🎯 Успешность: {completion_rate:.1f}%\n"

    if failed_tasks:
        if len(failed_tasks) > len(completed_tasks):
            message_text += "_💪 Не сдавайся! Даже великие леса начинались с первого деревца._\n"
        else:
            message_text += "_🌧️ Не все саженцы приживаются — это нормально! Главное продолжать._\n"
    elif completed_tasks:
        message_text += (
            "_✨ Твой лес растёт прекрасно! Продолжай в том же духе._\n"
        )
    else:
        message_text += "_🌱 Начни свой путь — посади первое дерево!_ \n"

    message_text += "_💡 Используй /plant чтобы посадить новое дерево_"
    await context.clear()
    await event.message.answer(message_text, parse_mode=ParseMode.MARKDOWN)


# @command_router.message_callback(F.callback.payload.contains("change_goal"))
# async def change_goal(event: MessageCallback, context: MemoryContext):
#     await event.message.answer(
#         text=LEXICON_RU["change_goal"],
#         parse_mode=ParseMode.MARKDOWN,
#     )
#     await context.set_state(FSMstates.is_changing_goal)


@command_router.message_created(FSMstates.is_changing_goal)
async def process_new_goal(event: MessageCreated, context: MemoryContext):

    new_goal = event.message.body.text
    user = await models.User.get(id=event.from_user.user_id)

    # Сохраняем старую цель для красивого сообщения
    old_goal = user.goal

    # Обновляем цель в базе
    user.goal = new_goal
    await user.save()

    await event.message.answer(
        text=f"🔄 *Путь переосмыслен!* 🔄\n\n"
        f"📜 *Старая цель:* {old_goal}\n"
        f"🎯 *Новая цель:* {new_goal}\n\n"
        "_Каждый новый путь — это шанс вырасти по-новому._ 🌱",
        parse_mode=ParseMode.MARKDOWN,
    )

    # Предлагаем сразу посадить дерево
    await event.message.answer(
        text="🌿 *Что дальше?*\n\n"
        "• /plant - посадить дерево к новой цели\n"
        "• /profile - посмотреть свой лес\n"
        "• /tasks - посмотреть текущие дела",
        parse_mode=ParseMode.MARKDOWN,
    )

    await context.set_state(None)
