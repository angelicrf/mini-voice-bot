from __future__ import annotations
import torch
import whisper

from .base import Agent, Message


class SpeechToTextAgent(Agent):
    """Agent 1: converts speech to text in the original spoken language."""

    name = "stt"

    def __init__(self, next_agent: str = "translator", model_name: str = "base") -> None:
        super().__init__()
        self.next_agent = next_agent
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = whisper.load_model(model_name, device=self.device)

    def handle(self, msg: Message) -> None:
        audio_path = str(msg.payload["audio_path"])
        audio = whisper.pad_or_trim(whisper.load_audio(audio_path))
        mel = whisper.log_mel_spectrogram(audio).to(self.model.device)
        _, probs = self.model.detect_language(mel)
        lang = max(probs, key=probs.get)
        result = self.model.transcribe(
            audio_path, task="transcribe", language=lang, fp16=(self.device == "cuda")
        )
        self.send(
            self.next_agent,
            "transcript",
            text=result["text"].strip(),
            language=lang,
            confidence=float(probs[lang]),
        )
