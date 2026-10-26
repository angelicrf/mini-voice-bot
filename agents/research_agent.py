from __future__ import annotations

from .base import Agent, Message
from rag.pipeline import research_query


class ResearchAgent(Agent):
    """Looks through the PBS directory and finds the best-matching playbook sections."""

    name = "researcher"

    def __init__(self, next_agent: str = "analyst") -> None:
        super().__init__()
        self.next_agent = next_agent

    def handle(self, msg: Message) -> None:
        text = str(msg.payload.get("text") or msg.payload.get("query") or "")
        if not text:
            self.send(self.next_agent, "research_complete", text="", matched_documents=[], suggested_actions=[])
            return

        research_result = research_query(text)
        self.send(
            self.next_agent,
            "research_complete",
            **research_result,
        )
