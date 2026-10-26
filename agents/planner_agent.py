from __future__ import annotations

from .base import Agent, Message


class PlannerAgent(Agent):
    """Decides which branch should run before the main processing pipeline starts."""

    name = "planner"

    def __init__(self, next_agent: str = "safety") -> None:
        super().__init__()
        self.next_agent = next_agent

    def handle(self, msg: Message) -> None:
        payload = dict(msg.payload)
        audio_path = payload.get("audio_path")
        text = payload.get("text") or payload.get("query") or ""

        route = "audio" if audio_path else "text"
        self.send(
            self.next_agent,
            "plan",
            route=route,
            audio_path=str(audio_path) if audio_path else None,
            text=text,
            original_query=text,
        )
