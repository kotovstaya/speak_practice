import asyncio
import os
from typing import Dict, Any

from dotenv import load_dotenv

load_dotenv()
import time
import aioschedule

from speak_practice.utils import get_logger

from aiogram import Bot, Dispatcher, executor, types
from speak_practice.backend import AssistantBackend, ConversationYieldObject
from telegram.parsemode import ParseMode

logger = get_logger(__name__)

bot = Bot(token=os.getenv("TOKEN"))
dp = Dispatcher(bot)


assist_backend: Dict[int, AssistantBackend] = {}
assist_user_info: Dict[int, Dict[Any, Any]] = {}
assist_backend_process = {}
is_message_send: Dict[int, bool] = {}
user_session_time: Dict[int, Any] = {}


async def clean_sessions():
    global user_session_time
    _t = time.time()
    keys = list(user_session_time.keys())
    for key in keys:
        if (_t - user_session_time[key])/ 60 > 10:
            logger.info(f"key: {key}")
            if key in assist_backend:
                del assist_backend[key]
            if key in assist_user_info:
                del assist_user_info[key]
            if key in assist_backend_process:
                del assist_backend_process[key]
            if key in is_message_send:
                del is_message_send[key]
            if key in user_session_time:
                del user_session_time[key]


async def scheduler():
    aioschedule.every(10).minutes.do(clean_sessions)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


@dp.message_handler(content_types=['location'])
@dp.message_handler()
async def echo(message: types.Message):
    global assist_backend, assist_backend_process, assist_user_info, is_message_send, user_session_time

    user_id = message.from_user.id
    user_session_time[user_id] = time.time()

    user_id = message.from_user.id
    if user_id not in assist_user_info.keys():
        is_message_send[user_id] = True
        assist_user_info[user_id] = {"id": user_id}
        assist_backend[user_id] = AssistantBackend()
        assist_backend_process[user_id] = assist_backend[user_id].main_loop(message.text, tg_user=assist_user_info[user_id])

    if is_message_send[user_id] == False:
        logger.info(f"Skip this message: {message.text}")
        return

    if user_id in assist_backend.keys() and user_id not in assist_backend_process.keys():
        assist_backend_process[user_id] = assist_backend[user_id].main_loop(message.text, tg_user=assist_user_info[user_id])

    while True:
        try:
            is_message_send[user_id] = False
            conversation_object: ConversationYieldObject = await anext(assist_backend_process[user_id])
        except Exception as ex:
            empty_conversation_object = ConversationYieldObject(text=str(ex), is_the_end=True)
            logger.info(f"tg_bot {message.from_user.id}: {empty_conversation_object}")
            conversation_object = empty_conversation_object

        await message.answer(conversation_object.text, parse_mode=ParseMode.HTML)

        if conversation_object.is_the_end:
            is_message_send[user_id] = True
            del assist_backend_process[user_id]
            break


async def on_startup(_):
    asyncio.create_task(scheduler())


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=False, on_startup=on_startup)