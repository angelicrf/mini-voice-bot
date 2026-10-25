from __future__ import annotations
from typing import Dict

from transformers import MarianMTModel, MarianTokenizer

from .base import Agent, Message


class TranslationAgent(Agent):
    """Agent 2: translates transcript text to English (MarianMT, loaded per language)."""

    name = "translator"

    def __init__(self, next_agent: str = "sink") -> None:
        super().__init__()
        self.next_agent = next_agent
        self._models: Dict[str, tuple] = {}

    def _load(self, lang: str):
        if lang not in self._models:
            repo = f"Helsinki-NLP/opus-mt-{lang}-en"
            self._models[lang] = (
                MarianTokenizer.from_pretrained(repo),
                MarianMTModel.from_pretrained(repo),
            )
        return self._models[lang]

    def translate(self, text: str, lang: str) -> str:
        if lang == "en" or not text:
            return text
        tok, model = self._load(lang)
        batch = tok([text], return_tensors="pt", padding=True, truncation=True)
        out = model.generate(**batch)
        return tok.decode(out[0], skip_special_tokens=True)

    def handle(self, msg: Message) -> None:
        lang = msg.payload["language"]
        english = self.translate(msg.payload["text"], lang)
        self.send(
            self.next_agent,
            "english_text",
            original_text=msg.payload["text"],
            text=english,
            language=lang,
            confidence=msg.payload.get("confidence"),
        )
