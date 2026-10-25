from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class Message:
    sender: str
    recipient: str
    topic: str
    payload: Dict[str, Any] = field(default_factory=dict)


class MessageBus:
    """Routes messages between registered agents; 'sink' collects final results."""

    def __init__(self) -> None:
        self.agents: Dict[str, "Agent"] = {}
        self.results: List[Message] = []

    def register(self, agent: "Agent") -> None:
        self.agents[agent.name] = agent
        agent.bus = self

    def send(self, msg: Message) -> None:
        if msg.recipient == "sink":
            self.results.append(msg)
            return
        self.agents[msg.recipient].handle(msg)


class Agent:
    name = "agent"

    def __init__(self) -> None:
        self.bus: MessageBus | None = None

    def send(self, recipient: str, topic: str, **payload: Any) -> None:
        assert self.bus is not None, "Agent must be registered on a MessageBus"
        self.bus.send(Message(self.name, recipient, topic, payload))

    def handle(self, msg: Message) -> None:
        raise NotImplementedError
