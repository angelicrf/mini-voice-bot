from __future__ import annotations

from typing import Any, Dict, List

from rag.pipeline import research_query

from .base import Agent, Message


class SupervisorAgent(Agent):
    """Coordinates retrieval retries and parallel research context for the multi-agent workflow."""

    name = "supervisor"

    def __init__(self, next_agent: str = "validator") -> None:
        super().__init__()
        self.next_agent = next_agent

    def _session_id(self, payload: Dict[str, Any]) -> str:
        return str(payload.get("session_id") or payload.get("query") or payload.get("text") or "default-session")

    def _run_parallel_research(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        store = getattr(self.bus, "memory_store", None)
        query = str(payload.get("query") or payload.get("text") or "")
        session_id = self._session_id(payload)
        if store is not None:
            store.register_query(session_id, query, route=payload.get("route"))

        candidates: List[str] = []
        if query:
            candidates.append(query)
            candidates.append(f"{query} troubleshooting steps")
            candidates.append(f"{query} best matching section")
            if store is not None:
                candidates.append(store.build_retry_query(session_id, query))

        deduped = []
        for candidate in candidates:
            if candidate and candidate not in deduped:
                deduped.append(candidate)
        if store is not None:
            store.set_parallel_branches(session_id, deduped)

        best_result: Dict[str, Any] = {}
        for candidate in deduped[:3]:
            result = research_query(candidate)
            if store is not None:
                store.record_attempt(session_id, candidate, result)
            if not best_result or float(result.get("confidence", 0.0) or 0.0) > float(best_result.get("confidence", 0.0) or 0.0):
                best_result = result

        if not best_result:
            return {
                "query": query,
                "primary_category": "general_inquiry",
                "category": "general_inquiry",
                "confidence": 0.0,
                "matched_documents": [],
                "suggested_actions": ["No matching guidance was found for this request."],
                "validation_status": "needs_review",
            }

        best_result["session_id"] = session_id
        best_result["parallel_branches"] = deduped
        best_result["retry_count"] = len((store.get_session(session_id).get("attempts", [])) if store is not None else [])
        return best_result

    def handle(self, msg: Message) -> None:
        payload = dict(msg.payload)
        if msg.topic == "retry_research":
            query = str(payload.get("query") or payload.get("text") or "")
            retry_count = int(payload.get("retry_count", 0) or 0)
            if retry_count >= 2:
                fallback = {
                    "query": query,
                    "primary_category": payload.get("primary_category", "general_inquiry"),
                    "category": payload.get("category", "general_inquiry"),
                    "confidence": float(payload.get("confidence", 0.0) or 0.0),
                    "matched_documents": payload.get("matched_documents", []) or [],
                    "suggested_actions": payload.get("suggested_actions", []) or ["The system could not reach a confident match after retrying."],
                    "validation_status": "needs_review",
                    "retry_count": retry_count,
                }
                self.send(self.next_agent, "research_complete", **fallback)
                return

            result = self._run_parallel_research({**payload, "query": query, "text": query})
            result["retry_count"] = retry_count + 1
            self.send(self.next_agent, "research_complete", **result)
            return

        if msg.topic in {"validated_text", "text", "plan"}:
            query = str(payload.get("text") or payload.get("query") or "")
            session_id = self._session_id(payload)
            if self.bus is not None and getattr(self.bus, "memory_store", None) is not None:
                self.bus.memory_store.register_query(session_id, query, route=payload.get("route"))
            result = self._run_parallel_research({**payload, "query": query, "text": query})
            result["session_id"] = session_id
            self.send(self.next_agent, "research_complete", **result)
            return

        if msg.topic == "audio":
            self.send("stt", "audio", **payload)
            return
