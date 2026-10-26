from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List


@dataclass
class ResearchAttempt:
    query: str
    result: Dict[str, Any]
    confidence: float
    attempted_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ResearchMemoryStore:
    """Shares context, retries, and parallel research outcomes across the agent workflow."""

    def __init__(self) -> None:
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def get_session(self, session_id: str) -> Dict[str, Any]:
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "query": "",
                "context": [],
                "parallel_branches": [],
                "attempts": [],
                "best_result": {},
                "retry_count": 0,
            }
        return self.sessions[session_id]

    def register_query(self, session_id: str, query: str, route: str | None = None) -> Dict[str, Any]:
        session = self.get_session(session_id)
        session["query"] = query
        session["route"] = route
        session["context"] = list(dict.fromkeys(session["context"] + ([query] if query else [])))
        return session

    def append_context(self, session_id: str, value: str) -> None:
        if not value:
            return
        session = self.get_session(session_id)
        session["context"] = list(dict.fromkeys(session["context"] + [value]))

    def set_parallel_branches(self, session_id: str, branches: List[str]) -> None:
        session = self.get_session(session_id)
        session["parallel_branches"] = [branch for branch in branches if branch]

    def record_attempt(self, session_id: str, query: str, result: Dict[str, Any]) -> Dict[str, Any]:
        session = self.get_session(session_id)
        attempt = ResearchAttempt(
            query=query,
            result=deepcopy(result),
            confidence=float(result.get("confidence", 0.0) or 0.0),
        )
        session["attempts"].append(attempt.__dict__)
        session["retry_count"] = len(session["attempts"])
        if not session["best_result"] or attempt.confidence > float(session["best_result"].get("confidence", 0.0) or 0.0):
            session["best_result"] = deepcopy(result)
        return session

    def build_retry_query(self, session_id: str, base_query: str) -> str:
        session = self.get_session(session_id)
        history = session.get("attempts", [])
        keywords: List[str] = []
        for attempt in history:
            docs = attempt.get("result", {}).get("matched_documents", []) or []
            for doc in docs:
                keywords.extend(doc.split())
        prior_context = " ".join(session.get("context", [])[:3])
        cleaned_keywords = [token for token in " ".join(keywords).split() if token.lower() not in {"the", "a", "an", "and", "or", "to", "for"}]
        combined = " ".join(dict.fromkeys(cleaned_keywords[:8]))
        if combined:
            fallback = f"{base_query} {combined} troubleshooting" if len(base_query.split()) < 8 else f"{base_query} {combined}"
        else:
            fallback = f"{base_query} troubleshoot and confirm the best matching section"
        if prior_context:
            return f"{fallback} {prior_context}"
        return fallback

    def get_best_result(self, session_id: str) -> Dict[str, Any]:
        session = self.get_session(session_id)
        return deepcopy(session.get("best_result", {}))
