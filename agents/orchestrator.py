from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Tuple

from .analysis_agent import AnalysisAgent
from .base import Message, MessageBus
from .memory_store import ResearchMemoryStore
from .planner_agent import PlannerAgent
from .research_agent import ResearchAgent
from .safety_agent import SafetyAgent
from .stt_agent import SpeechToTextAgent
from .supervisor_agent import SupervisorAgent
from .translation_agent import TranslationAgent
from .validator_agent import ValidatorAgent


def build_text_workflow() -> Tuple[MessageBus, Dict[str, Any]]:
    """Construct the dependency-aware text-processing workflow."""
    bus = MessageBus(memory_store=ResearchMemoryStore())
    bus.register(PlannerAgent())
    bus.register(SafetyAgent())
    bus.register(SupervisorAgent())
    bus.register(ResearchAgent())
    bus.register(ValidatorAgent())
    bus.register(AnalysisAgent())
    return bus, {}


def run_text_workflow(text: str) -> Dict[str, Any]:
    """Execute the end-to-end text-to-answer workflow with planner + safety + research + validation."""
    bus, _ = build_text_workflow()
    bus.send(Message("user", "planner", "text", {"text": text}))
    final = bus.results[-1].payload if bus.results else {}
    return final


def build_voice_workflow(audio_path: str | Path) -> Tuple[MessageBus, Dict[str, Any]]:
    """Construct the dependency-aware multi-agent workflow for audio inputs."""
    bus = MessageBus(memory_store=ResearchMemoryStore())
    bus.register(PlannerAgent())
    bus.register(SafetyAgent())
    bus.register(SupervisorAgent())
    bus.register(SpeechToTextAgent())
    bus.register(TranslationAgent(next_agent="researcher"))
    bus.register(ResearchAgent())
    bus.register(ValidatorAgent())
    bus.register(AnalysisAgent())

    bus.send(Message("user", "planner", "audio", {"audio_path": str(Path(audio_path))}))
    final = bus.results[-1].payload if bus.results else {}
    return bus, final


def run_voice_workflow(audio_path: str | Path) -> Dict[str, Any]:
    """Execute the end-to-end voice-to-research pipeline and return the final payload."""
    _, final = build_voice_workflow(audio_path)
    return final
