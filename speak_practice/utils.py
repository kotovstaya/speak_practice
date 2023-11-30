import logging
import sys
from pydub import AudioSegment


def get_logger(name):
    logging.basicConfig(format=(
        f"%(asctime)s - %(name)s - "
        f"%(levelname)s - %(message)s"),
        level=logging.INFO)
    return logging.getLogger(name)


StdOutHandler = logging.StreamHandler(sys.stdout)
StdOutHandler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(name)s | %(levelname)s >>> %(message)s')
StdOutHandler.setFormatter(formatter)
StdOutHandler.setStream(stream=sys.stdout)


def save_voice_message(filename: str, downloaded_file) -> str:
    ogg_filename = filename + ".ogg"
    wav_filename = filename + ".wav"
    with open(filename + '.ogg', 'wb') as new_file:
        new_file.write(downloaded_file.getbuffer())
    song = AudioSegment.from_ogg(ogg_filename)
    song.export(wav_filename, format="wav")
    return wav_filename