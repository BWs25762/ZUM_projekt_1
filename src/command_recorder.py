import sounddevice as sd
from timeit import default_timer
import numpy as np
from pyctcdecode import BeamSearchDecoderCTC
from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC


class CommandRecorder:

    def __init__(
            self,
            volume_threshold: float,
            record_wait_time: int,
            initial_record_wait_time: int,
            max_command_time: int,
            decoder: BeamSearchDecoderCTC,
            processor: Wav2Vec2Processor,
            model: Wav2Vec2ForCTC

    ):
        self.fs = 16000
        self.volume_threshold = volume_threshold
        self.record_wait_time = record_wait_time
        self.initial_record_wait_time = initial_record_wait_time
        self.max_command_time = max_command_time
        self.decoder = decoder
        self.processor = processor
        self.model = model

    def _record_command(self):
        total_time = 0
        max_volume = 1.0
        total_audio = np.array([[0.]])
        record_wait_time = self.initial_record_wait_time
        print("recording command...")
        start = default_timer()
        while max_volume > self.volume_threshold and total_time < self.max_command_time:
            command_slice = sd.rec(int(record_wait_time * self.fs), samplerate=self.fs, channels=1)
            sd.wait()
            total_audio = np.concatenate((total_audio, command_slice))
            max_volume = command_slice.max()
            total_time += self.record_wait_time
            record_wait_time = self.record_wait_time
        print(f"done recording! {(default_timer()-start):2}s")
        total_audio = np.reshape(total_audio, total_audio.shape[0])
        return total_audio

    def record_command(self):
        command_audio = self._record_command()
        feats = self.processor(command_audio, sampling_rate=self.fs, return_tensors='pt', padding=True)
        out = self.model(input_values=feats.input_values)
        sent = self.decoder.decode(out.logits.cpu().detach().numpy()[0])
        return sent
