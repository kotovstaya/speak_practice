from abc import ABC, abstractmethod

import numpy as np
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
            use_safetensors=True
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

    def predict(self, audio_record: np.ndarray, rate: int) -> str:
        obj = {"array": audio_record, "path": "empty", "sampling_rate": rate,}
        result = self.pipe(obj)
        return result["text"]


if __name__ == "__main__":
    model = SpeechToTextModel()
    rate, audio_record = wavfile.read('./test.wav')
    text = model.predict(audio_record, rate=rate)
    print(text)
