from __future__ import annotations

from .base import Agent, Message
from rag.guardrails import validate_input_safety


class SafetyAgent(Agent):
    """Performs pre-flight validation and routes safe requests to the right execution branch."""

    name = "safety"

    def __init__(self, next_agent: str = "supervisor") -> None:
        super().__init__()
        self.next_agent = next_agent

    def handle(self, msg: Message) -> None:
        payload = dict(msg.payload)
        audio_path = payload.get("audio_path")
        text = payload.get("text") or payload.get("query") or ""

        if audio_path:
            self.send(self.next_agent, "audio", audio_path=str(audio_path), route="audio")
            return

        is_safe, sanitized_prompt, results_valid = validate_input_safety(text)
        if not is_safe:
            self.send(
                "analyst",
                "security_refusal",
                query=text,
                primary_category="security_refusal",
                category="security_refusal",
                categories=["security_refusal"],
                confidence=1.0,
                matched_documents=[],
                suggested_actions=[
                    "I am unable to process requests attempting to alter instructions, contain toxicity, or violate security policy."
                ],
                security_valid=results_valid,
                validation_status="blocked",
            )
            return

        self.send(
            self.next_agent,
            "validated_text",
            text=sanitized_prompt,
            query=sanitized_prompt,
            route="text",
            security_valid=results_valid,
            validation_status="safe",
        )
