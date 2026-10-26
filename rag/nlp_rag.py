"""
NLP analysis, categorization, and domain-partitioned RAG pipeline (Facade).
Re-exports functionality from the modular `rag` package.
"""

from __future__ import annotations

from rag import (
    CATEGORY_EXEMPLARS,
    CATEGORY_LABELS,
    DEFAULT_PLAYBOOKS,
    KnowledgeDocument,
    PBS_DIR,
    _get_classifier,
    _matches_keyword,
    _parse_playbook_sections,
    _tokenize,
    build_user_summary,
    classify_intent,
    input_scanners,
    load_playbooks,
    output_scanners,
    process_and_resolve,
    research_query,
    retrieve_category_solutions,
    sanitize_output,
    synthesize_solution,
    validate_input_safety,
    vault,
)

__all__ = [
    "KnowledgeDocument",
    "PBS_DIR",
    "DEFAULT_PLAYBOOKS",
    "CATEGORY_LABELS",
    "CATEGORY_EXEMPLARS",
    "load_playbooks",
    "_parse_playbook_sections",
    "vault",
    "input_scanners",
    "output_scanners",
    "validate_input_safety",
    "sanitize_output",
    "_tokenize",
    "_matches_keyword",
    "_get_classifier",
    "classify_intent",
    "retrieve_category_solutions",
    "synthesize_solution",
    "research_query",
    "build_user_summary",
    "process_and_resolve",
]