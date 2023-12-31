# Nithu/text-to-speech
from abc import ABC, abstractmethod
from typing import Tuple, Any
from pydub import AudioSegment
import numpy as np
from fairseq.checkpoint_utils import load_model_ensemble_and_task_from_hf_hub
from fairseq.models.text_to_speech.hub_interface import TTSHubInterface
from scipy.io.wavfile import write as write_wav
from aiogram.types import FSInputFile
from speak_practice.consts import TEXT_2_SPEECH_MODEL_PATH


class BaseTextToSpeechModel(ABC):

    @abstractmethod
    def predict(self, text: str) -> Any:
        ...

    @staticmethod
    def save(filepath: str, audio_record: np.ndarray, rate: int) -> None:
        write_wav(filepath, rate, audio_record)


class TextToSpeechModel(BaseTextToSpeechModel):
    def __init__(self):
        models, self.cfg, self.task = load_model_ensemble_and_task_from_hf_hub(
            TEXT_2_SPEECH_MODEL_PATH,
            arg_overrides={"vocoder": "hifigan", "fp16": False}
        )
        self.model = models[0]

        TTSHubInterface.update_cfg_with_data_cfg(self.cfg, self.task.data_cfg)
        self.generator = self.task.build_generator([self.model], self.cfg)

    def predict(self, text: str) -> Tuple[int, np.ndarray]:
        sample = TTSHubInterface.get_model_input(self.task, text)
        audio_record, rate = TTSHubInterface.get_prediction(self.task, self.model, self.generator, sample)
        print(f"rate: {rate}")
        return rate, audio_record.numpy()

    def predict_with_save(self, text: str, record_path: str) -> FSInputFile:
        rate, audio_record = self.predict(text)
        self.save(record_path, audio_record, rate)
        # song = AudioSegment.from_wav(record_path)
        # ogg_path = record_path.replace("wav", "ogg")
        # song.export(ogg_path, format="ogg")
        voice = FSInputFile(record_path, filename="voice")
        return voice


if __name__ == "__main__":
    text = "Hello, my name is Anton"
    text_2_speech_model = TextToSpeechModel()
    audio_record, rate = text_2_speech_model.predict(text)
    text_2_speech_model.save("./../data/text_2_speech.wav", rate, audio_record)
