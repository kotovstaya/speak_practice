import asyncio
import os
from typing import Dict, Any

from dotenv import load_dotenv

load_dotenv()
import time
import aioschedule

from speak_practice.utils import get_logger

from aiogram import Bot, Dispatcher, types
from aiogram import Router, F
from speak_practice.backend import AssistantBackend, ConversationYieldObject
from speak_practice.speech_to_text import SpeechToTextModel
from speak_practice.text_to_speech import TextToSpeechModel
from speak_practice.utils import save_voice_message

logger = get_logger(__name__)

SPEECH_2_TEXT_MODEL = SpeechToTextModel()
TEXT_2_SPEECH = TextToSpeechModel()

router = Router()

bot = Bot(token=os.getenv("TOKEN"))
dp = Dispatcher()


assist_backend: Dict[int, AssistantBackend] = {}
assist_user_info: Dict[int, Dict[Any, Any]] = {}
assist_backend_process = {}
is_message_send: Dict[int, bool] = {}
user_session_time: Dict[int, Any] = {}


def update_global_variables(user_id: int, text: str) -> bool:
    global assist_user_info , user_session_time, is_message_send, assist_backend, assist_backend_process
    user_session_time[user_id] = time.time()

    if user_id not in assist_user_info.keys():
        is_message_send[user_id] = True
        assist_user_info[user_id] = {"id": user_id}
        assist_backend[user_id] = AssistantBackend()
        assist_backend_process[user_id] = assist_backend[user_id].main_loop(text, tg_user=assist_user_info[user_id])

    if not is_message_send[user_id]:
        logger.info(f"Skip this message: {text}")
        return False

    if user_id in assist_backend.keys():
        assist_backend_process[user_id] = assist_backend[user_id].main_loop(text, tg_user=assist_user_info[user_id])
    return True


async def clean_sessions() -> None:
    global user_session_time
    _t = time.time()
    keys = list(user_session_time.keys())
    for key in keys:
        if (_t - user_session_time[key]) g/ 60 > 10:
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
    global SPEECH_2_TEXT_MODEL, TEXT_2_SPEECH, assist_backend, assist_backend_process, assist_user_info, is_message_send, user_session_time

    user_id = message.from_user.id

    downloaded_file = await bot.download(message.voice.file_id)
    wav_file = save_voice_message(f'./../data/{user_id}', downloaded_file)
    transcription = SPEECH_2_TEXT_MODEL.predict_file(wav_file)

    if not update_global_variables(user_id, transcription):
        return

    conversation_object: ConversationYieldObject = await anext(assist_backend_process[user_id])
    voice = TEXT_2_SPEECH.predict_with_save(conversation_object.text, "./../data/text_2_speech.wav")
    await message.reply(f"Transcription: {transcription}")
    await bot.send_voice(message.from_user.id, voice=voice)


@dp.message(F.text)
async def echo(message: types.Message):
    global assist_backend, assist_backend_process, assist_user_info, is_message_send, user_session_time

    user_id = message.from_user.id

    if not update_global_variables(user_id, message.text):
        return

    conversation_object: ConversationYieldObject = await anext(assist_backend_process[user_id])
    await message.reply(conversation_object.text)


async def on_startup(_):
    asyncio.create_task(scheduler())


async def main():
    await dp.start_polling(bot, skip_updates=False, on_startup=on_startup)


if __name__ == '__main__':
    asyncio.run(main())