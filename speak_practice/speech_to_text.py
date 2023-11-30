from abc import ABC, abstractmethod
from typing import Tuple
import numpy as np
import wave
import torch
from scipy.io import wavfile
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline

from speak_practice.consts import SPEECH_2_TEXT_MODEL_PATH

device = "cuda:0" if torch.cuda.is_available() else "cpu"
torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32


class BaseSpeechToTextModel(ABC):

    @abstractmethod
    def predict(self, audio_record: np.ndarray, rate: int) -> str:
        ...


class SpeechToTextModel(BaseSpeechToTextModel):
    def __init__(self):
        self.model = AutoModelForSpeechSeq2Seq.from_pretrained(
            SPEECH_2_TEXT_MODEL_PATH,
            torch_dtype=torch_dtype,
            low_cpu_mem_usage=True,
            use_safetensors=True,
        )
        self.model.to(device)
        self.processor = AutoProcessor.from_pretrained(SPEECH_2_TEXT_MODEL_PATH)
        self.pipe = pipeline(
            "automatic-speech-recognition",
            model=self.model,
            tokenizer=self.processor.tokenizer,
            feature_extractor=self.processor.feature_extractor,
            max_new_tokens=128,
            torch_dtype=torch_dtype,
            device=device,
        )

    @staticmethod
    def convert_wav_to_float_record(filename: str) -> Tuple[int, np.ndarray]:
        def read_wav_file(filename: str) -> float:
            def get_int(bytes_obj):
                an_int = int.from_bytes(bytes_obj, 'little', signed=sampwidth != 1)
                return an_int - 128 * (sampwidth == 1)

            with wave.open(filename, 'rb') as file:
                sampwidth = file.getsampwidth()
                frames = file.readframes(-1)
            bytes_samples = (frames[i: i + sampwidth] for i in range(0, len(frames), sampwidth))
            return [get_int(b) / pow(2, sampwidth * 8 - 1) for b in bytes_samples]

        rate, _ = wavfile.read(filename)
        audio_record = np.array(read_wav_file(filename))
        return rate, audio_record

    def predict(self, audio_record: np.ndarray, rate: int) -> str:
        obj = {"array": audio_record, "path": "empty", "sampling_rate": rate,}
        result = self.pipe(obj)
        return result["text"]

    def predict_file(self, filename: str) -> str:
        rate, audio_record = self.convert_wav_to_float_record(filename)
        text = self.predict(audio_record, rate)
        return text


if __name__ == "__main__":
    model = SpeechToTextModel()
    # import wave
    #
    #
    # # audio_record = audio_record
    # print(audio_record)
    # text = model.predict(audio_record, rate=rate)
    # print(text)
