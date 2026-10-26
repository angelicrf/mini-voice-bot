from __future__ import annotations
from typing import Any, Dict

from rag.classifier import classify_intent
from rag.guardrails import sanitize_output, validate_input_safety
from rag.retriever import retrieve_category_solutions, synthesize_solution


def research_query(text: str) -> Dict[str, Any]:
    """
    Performs the research stage: guardrails, intent classification,
    category-aware retrieval from the playbook directory, and solution synthesis.
    """
    is_safe, sanitized_prompt, results_valid = validate_input_safety(text)
    if not is_safe:
        threats = [
            scanner for scanner, is_valid in results_valid.items()
            if not is_valid and scanner in {"PromptInjection", "Toxicity"}
        ]
        return {
            "query": text,
            "category": "security_refusal",
            "primary_category": "security_refusal",
            "categories": ["security_refusal"],
            "confidence": 1.0,
            "matched_documents": [],
            "suggested_actions": [
                "I am unable to process requests attempting to alter instructions, contain toxicity, or violate security policy."
            ],
            "security_valid": results_valid,
            "threats_detected": threats,
        }

    category_info = classify_intent(sanitized_prompt)
    active_categories = category_info.get("predicted_categories", [category_info["predicted_category"]])
    matched_docs = retrieve_category_solutions(query=sanitized_prompt, categories=active_categories)
    raw_solution = synthesize_solution(sanitized_prompt, category_info, matched_docs)

    sanitized_actions = [
        sanitize_output(sanitized_prompt, action)
        for action in raw_solution.get("suggested_actions", [])
    ]
    raw_solution["suggested_actions"] = sanitized_actions
    return raw_solution


def build_user_summary(research_result: Dict[str, Any]) -> str:
    """Formats the retrieved playbook research into a user-facing summary."""
    category = research_result.get("primary_category", research_result.get("category", "general_inquiry"))
    docs = research_result.get("matched_documents", [])
    actions = research_result.get("suggested_actions", [])

    doc_text = ", ".join(docs[:3]) if docs else "no direct playbook match"
    action_text = "; ".join(actions[:3]) if actions else "No specific actions were identified."
    return f"I matched this to the '{category}' workflow and found the most relevant section(s): {doc_text}. Recommended steps: {action_text}"


def process_and_resolve(text: str) -> Dict[str, Any]:
    """Backward-compatible entry point used by existing API and scripts."""
    return research_query(text)