from __future__ import annotations

from .base import Agent, Message
from rag.pipeline import build_user_summary


class AnalysisAgent(Agent):
    """Turns the retrieved playbook research into a concise final answer for the user."""

    name = "analyst"

    def __init__(self, next_agent: str = "sink") -> None:
        super().__init__()
        self.next_agent = next_agent

    def handle(self, msg: Message) -> None:
        payload = dict(msg.payload)
        summary = build_user_summary(payload)
        response = {
            "query": payload.get("query", ""),
            "category": payload.get("primary_category", payload.get("category", "general_inquiry")),
            "confidence": payload.get("confidence", 0),
            "matched_documents": payload.get("matched_documents", []),
            "suggested_actions": payload.get("suggested_actions", []),
            "validation_status": payload.get("validation_status", "validated"),
            "user_response": summary,
        }
        self.send(self.next_agent, "final_analysis", **response)
