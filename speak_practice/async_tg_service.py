import asyncio
import os
import subprocess
from typing import Dict, Any
from pydub import AudioSegment
from dotenv import load_dotenv

load_dotenv()
import time
import aioschedule

from speak_practice.utils import get_logger

from aiogram import Bot, Dispatcher, types
from aiogram import Router, F
from speak_practice.backend import AssistantBackend, ConversationYieldObject
from telegram.parsemode import ParseMode
from speak_practice.speech_to_text import SpeechToTextModel
from speak_practice.utils import save_voice_message

logger = get_logger(__name__)

SPEECH_2_TEXT_MODEL = SpeechToTextModel()

router = Router()

bot = Bot(token=os.getenv("TOKEN"))
dp = Dispatcher()


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


@dp.message(F.voice)
async def convert_audio(message: types.Voice):
    global SPEECH_2_TEXT_MODEL
    downloaded_file = await bot.download(message.voice.file_id)
    wav_file = save_voice_message(f'./../data/{message.from_user.id}', downloaded_file)
    transcription = SPEECH_2_TEXT_MODEL.predict_file(wav_file)
    await message.reply(f"Transcription: {transcription}")


@dp.message(F.text)
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


async def main():
    await dp.start_polling(bot, skip_updates=False, on_startup=on_startup)


if __name__ == '__main__':
    asyncio.run(main())