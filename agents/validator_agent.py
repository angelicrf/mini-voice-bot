from __future__ import annotations

from .base import Agent, Message


class ValidatorAgent(Agent):
    """Checks whether the retrieved playbook matches are strong enough for final response synthesis."""

    name = "validator"

    def __init__(self, next_agent: str = "analyst") -> None:
        super().__init__()
        self.next_agent = next_agent

    def handle(self, msg: Message) -> None:
        payload = dict(msg.payload)
        confidence = float(payload.get("confidence", 0.0) or 0.0)
        matched_documents = payload.get("matched_documents", []) or []

        if payload.get("primary_category") == "security_refusal":
            self.send(self.next_agent, "validated_result", **payload)
            return

        if not matched_documents or confidence < 0.2:
            payload["validation_status"] = "needs_review"
            payload["fallback_action"] = "expand_query_and_retry"
            payload["retry_count"] = int(payload.get("retry_count", 0) or 0)
            self.send("supervisor", "retry_research", **payload)
            return

        payload["validation_status"] = "validated"
        payload["fallback_action"] = "none"
        self.send(self.next_agent, "validated_result", **payload)
