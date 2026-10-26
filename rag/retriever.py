from __future__ import annotations
import math
from typing import Any, Dict, List, Optional, Union

from rag.classifier import _tokenize
from rag.models import KnowledgeDocument
from rag.playbooks import load_playbooks


def retrieve_category_solutions(
    query: str,
    categories: Union[str, List[str]],
    knowledge_base: Optional[List[KnowledgeDocument]] = None,
    top_k: int = 3
) -> List[KnowledgeDocument]:
    """
    RAG retrieval partitioned across detected categories: retrieves and ranks
    playbook sections matching active categories.
    """
    kb = knowledge_base if knowledge_base is not None else load_playbooks()
    category_list = [categories] if isinstance(categories, str) else categories
    partition = [doc for doc in kb if doc.category in category_list]
    if not partition:
        partition = kb

    query_tokens = _tokenize(query)

    def relevance_score(doc: KnowledgeDocument) -> float:
        doc_tokens = _tokenize(f"{doc.title} {doc.content} {' '.join(doc.solution_steps)}")
        overlap = 0.0
        for q in query_tokens:
            if q in doc_tokens:
                overlap += 1.0
            elif len(q) >= 4:
                for d in doc_tokens:
                    if len(d) >= 4 and (q.startswith(d) or d.startswith(q)):
                        overlap += 0.8
                        break
        return overlap / math.sqrt(len(query_tokens) * len(doc_tokens) + 1e-5)

    sorted_docs = sorted(partition, key=relevance_score, reverse=True)
    seen_ids = set()
    unique_docs = []
    for doc in sorted_docs:
        if doc.doc_id not in seen_ids:
            seen_ids.add(doc.doc_id)
            unique_docs.append(doc)
    return unique_docs[:top_k]


def synthesize_solution(
    query: str,
    category_info: Dict[str, Any],
    documents: List[KnowledgeDocument]
) -> Dict[str, Any]:
    """Builds a structured resolution payload merging multiple categories and actions."""
    categories = category_info.get("predicted_categories", [category_info.get("predicted_category", "general_inquiry")])
    primary_category = category_info.get("predicted_category", categories[0] if categories else "general_inquiry")
    aggregated_steps = []
    for doc in documents:
        aggregated_steps.extend(doc.solution_steps)

    return {
        "query": query,
        "category": primary_category,
        "primary_category": primary_category,
        "categories": categories,
        "confidence": category_info["confidence"],
        "matched_documents": [doc.title for doc in documents],
        "suggested_actions": list(dict.fromkeys(aggregated_steps))
    }