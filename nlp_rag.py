"""
NLP analysis, categorization, and domain-partitioned RAG pipeline.
"""

from __future__ import annotations
import math
import re
from pathlib import Path
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from llm_guard import scan_prompt, scan_output
from llm_guard.input_scanners import Anonymize, PromptInjection, Toxicity
from llm_guard.output_scanners import Deanonymize, Sensitive
from llm_guard.vault import Vault

from transformers import pipeline


@dataclass
class KnowledgeDocument:
    doc_id: str
    category: str
    title: str
    content: str
    solution_steps: List[str]


PBS_DIR = Path(__file__).resolve().parent / "pbs"

DEFAULT_PLAYBOOKS: Dict[str, str] = {
    "image_file_troubleshooting.md": """# Image and File Troubleshooting Playbook

## File Header and Format Validation
- Validate raw file headers, mime-types, and magic bytes before running vision pipelines.
- Check read and write permissions for the image upload and temporary processing directories.
- Ensure upload streams are fully flushed and size conforms to limits.

## Vision Model and Tensor Normalization
- Normalize image dimensions and color channels to 3-channel RGB using PIL or OpenCV.
- Inspect vision inference logs for unhandled tensor shape or decoding errors.
- Verify corrupt input handling and fallback to thumbnail generation if image decode fails.
""",
    "engineering_task_assignment.md": """# Engineering Task Assignment Playbook

## Issue Triage and Diagnostic Collection
- Collect reproducing image or audio files, error logs, trace IDs, and environment details.
- Aggregate Whisper transcriptions and classification tags into an incident report.

## Ticket Escalation and On-Call Dispatch
- Create an engineering ticket in Jira or Linear with priority and component service tags.
- Assign the troubleshooting task directly to the on-call engineer or team lead.
- Post automated escalation notification to the engineering triage Slack/Teams channel.
""",
    "technical_support.md": """# Technical Support Playbook

## Audio Device and Microphone Configuration
- Check OS microphone permissions and hardware audio input settings.
- Run audio normalization pass (`clean_audio.py`) to eliminate background noise.
- Confirm audio sample rate matches 16kHz required by Whisper models.
""",
    "billing.md": """# Billing Support Playbook

## Invoices and Payment Inquiries
- Verify the registered billing email on customer account.
- Check payment gateway logs for failed card authorizations or renewal attempts.
""",
    "account_access.md": """# Account Access Playbook

## Credentials and Authentication
- Trigger one-time password (OTP) reset token to verified email.
- Check if account is locked due to consecutive failed authentication attempts.
"""
}


def _parse_playbook_sections(filepath: Path) -> List[KnowledgeDocument]:
    """
    Parses a playbook file into full semantic section blocks without character-slicing.
    Preserves context by keeping complete paragraphs/sections intact.
    """
    content = filepath.read_text(encoding="utf-8").strip()
    if not content:
        return []

    filename_stem = filepath.stem.lower()
    matched_category = filename_stem
    for key, val in CATEGORY_LABELS.items():
        if val in filename_stem or filename_stem in val:
            matched_category = val
            break

    # Split along markdown headings (e.g., # or ##) while keeping the full text block intact
    raw_sections = re.split(r"(?m)^(?=#{1,4}\s+)", content)
    docs: List[KnowledgeDocument] = []

    for idx, block in enumerate(raw_sections):
        block = block.strip()
        if not block:
            continue
        first_line, _, _ = block.partition("\n")
        section_title = first_line.lstrip("#").strip() if first_line.startswith("#") else f"{filepath.stem} - Section {idx + 1}"

        # Context Preservation: extract distinct bulleted action steps if present,
        # otherwise keep complete sentence/paragraph blocks intact without character slicing
        action_steps = [
            line.strip().lstrip("-*0123456789. ")
            for line in block.splitlines()
            if re.match(r"^\s*([-*]|\d+\.)\s+", line)
        ]
        if not action_steps:
            action_steps = [
                line.strip()
                for line in block.splitlines()
                if line.strip() and not line.startswith("#")
            ]
        if not action_steps:
            action_steps = [block]

        docs.append(
            KnowledgeDocument(
                doc_id=f"{filepath.stem}_{idx}",
                category=matched_category,
                title=f"{filepath.stem}: {section_title}",
                content=block,
                solution_steps=action_steps,
            )
        )
    return docs


def load_playbooks(pbs_dir: Optional[Path] = None) -> List[KnowledgeDocument]:
    """
    Reads all playbook (.md and .txt) files inside the pbs directory,
    extracting sections with complete contextual boundaries preserved.
    """
    target_dir = pbs_dir or PBS_DIR
    if not target_dir.exists():
        target_dir.mkdir(parents=True, exist_ok=True)

    playbook_files = sorted(list(target_dir.glob("*.md")) + list(target_dir.glob("*.txt")))
    # Auto-seed starter playbooks if directory is empty
    if not playbook_files:
        for filename, content in DEFAULT_PLAYBOOKS.items():
            (target_dir / filename).write_text(content, encoding="utf-8")
        playbook_files = sorted(list(target_dir.glob("*.md")) + list(target_dir.glob("*.txt")))

    docs: List[KnowledgeDocument] = []
    for filepath in playbook_files:
        docs.extend(_parse_playbook_sections(filepath))
    return docs

CATEGORY_LABELS: Dict[str, str] = {
    "image and file troubleshooting": "image_file_troubleshooting",
    "engineering task assignment": "engineering_task_assignment",
    "technical support and audio issues": "technical_support",
    "billing and payment inquiries": "billing",
    "account access and authentication": "account_access",
    "general inquiry": "general_inquiry",
}

CATEGORY_EXEMPLARS: Dict[str, List[str]] = {
    "image_file_troubleshooting": [
        "image", "photo", "picture", "file", "format", "corrupted", "upload", "png", "jpg", "jpeg", "tiff", "vision", "render"
    ],
    "engineering_task_assignment": [
        "engineer", "task", "assigned", "assign", "ticket", "developer", "jira", "escalate", "bug report", "dev team", "investigate"
    ],
    "technical_support": [
        "not working", "broken", "sound error", "error code", "bug", "crash", "audio fail", "noise"
    ],
    "billing": [
        "charge", "invoice", "refund", "subscription", "credit card", "payment", "cost", "pricing"
    ],
    "account_access": [
        "login", "sign in", "password", "locked out", "username", "2fa", "authentication"
    ],
    "general_inquiry": [
        "hello", "hours", "contact", "support", "information", "what is this"
    ]
}


# LLM Guard configuration
vault = Vault()
input_scanners = [Anonymize(vault), Toxicity(), PromptInjection()]
output_scanners = [Deanonymize(vault), Sensitive()]

_classifier_pipeline = None


def _get_classifier():
    """Lazy-initializes the Hugging Face zero-shot classification pipeline."""
    global _classifier_pipeline
    if _classifier_pipeline is None:
        try:
            _classifier_pipeline = pipeline("zero-shot-classification")
        except Exception:
            _classifier_pipeline = False
    return _classifier_pipeline if _classifier_pipeline is not False else None

def validate_input_safety(text: str) -> tuple[bool, str, Dict[str, bool]]:
    """
    Screens user text using llm-guard for jailbreak attempts, prompt injection, and toxicity.
    Returns (is_safe, sanitized_prompt, results_valid).
    """
    try:
        sanitized_prompt, results_valid, _ = scan_prompt(input_scanners, text)
        is_safe = not any(not result for result in results_valid.values())
        return is_safe, sanitized_prompt, results_valid
    except Exception:
        return True, text, {"scanner_fallback": True}


def sanitize_output(prompt: str, response: str) -> str:
    """
    Redacts sensitive credentials and deanonymizes vault tokens from output using llm-guard.
    """
    try:
        sanitized_response, results_valid, _ = scan_output(output_scanners, prompt, response)
        if any(not result for result in results_valid.values()):
            return "[REDACTED_CREDENTIAL]"
        return sanitized_response
    except Exception:
        return response


def _tokenize(text: str) -> set[str]:
    """Simple tokenizer removing non-alphanumeric characters."""
    return set("".join(c if c.isalnum() else " " for c in text.lower()).split())


def _matches_keyword(kw: str, tokens: set[str], full_text: str) -> bool:
    """Matches keywords including plurals, stems, and multi-word phrases."""
    if " " in kw:
        return kw in full_text
    if kw in tokens:
        return True
    for t in tokens:
        if len(kw) >= 4 and len(t) >= 4:
            if t.startswith(kw) or kw.startswith(t):
                return True
    return False


def classify_intent(
    text: str,
    categories: Optional[Dict[str, List[str]]] = None,
    multi_label_threshold: float = 0.35,
) -> Dict[str, Any]:
    """
    Classifies input text into one or more categories using an NLI zero-shot
    transformer model with multi-label support, falling back to keyword heuristics.
    """
    classifier = _get_classifier()
    if classifier is not None:
        try:
            candidate_labels = list(CATEGORY_LABELS.keys())
            result = classifier(
                text,
                candidate_labels=candidate_labels,
                multi_label=True,
                hypothesis_template="This request relates to {}."
            )
            scores: Dict[str, float] = {}
            for label, score in zip(result["labels"], result["scores"]):
                category_key = CATEGORY_LABELS[label]
                scores[category_key] = round(float(score), 4)

            # Gather categories meeting or exceeding the threshold
            predicted_categories = [
                cat for cat, score in scores.items() if score >= multi_label_threshold
            ]
            if not predicted_categories:
                predicted_categories = [max(scores, key=scores.get)]
            else:
                predicted_categories.sort(key=lambda cat: scores[cat], reverse=True)

            primary_category = predicted_categories[0]
            return {
                "text": text,
                "predicted_category": primary_category,
                "predicted_categories": predicted_categories,
                "confidence": scores[primary_category],
                "scores": scores,
                "classification_method": "transformer_zero_shot"
            }
        except Exception:
            pass  # Fall back to token-based matching if pipeline execution fails

    exemplars = categories or CATEGORY_EXEMPLARS
    tokens = _tokenize(text)
    normalized_text = text.lower()
    scores: Dict[str, float] = {}

    for category, keywords in exemplars.items():
        score = 0.0
        for kw in keywords:
            if _matches_keyword(kw, tokens, normalized_text):
                score += 1.0
        scores[category] = score

    matching_categories = [cat for cat, score in scores.items() if score > 0.0]
    if matching_categories:
        matching_categories.sort(key=lambda cat: scores[cat], reverse=True)
        primary_category = matching_categories[0]
        total_score = sum(scores.values()) or 1.0
        confidence = round(scores[primary_category] / total_score, 3)
    else:
        primary_category = "general_inquiry"
        matching_categories = ["general_inquiry"]
        confidence = 0.0

    return {
        "text": text,
        "predicted_category": primary_category,
        "predicted_categories": matching_categories,
        "confidence": confidence,
        "scores": scores,
        "classification_method": "keyword_fallback"
    }


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
    # Deduplicate documents while preserving ranking order
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
    """
    Builds a structured resolution payload merging multiple categories and actions.
    """
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


def process_and_resolve(text: str) -> Dict[str, Any]:
    """
    Orchestrates classification, domain-partitioned RAG retrieval,
    guardrails, and solution synthesis for an input query.
    """
    # Step 1: Input Guardrail Check using llm-guard
    is_safe, sanitized_prompt, results_valid = validate_input_safety(text)
    if not is_safe:
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
        }

    # Step 2: Intent Classification using sanitized prompt
    category_info = classify_intent(sanitized_prompt)

    # Step 3: Domain-Partitioned RAG Retrieval across all matching categories
    active_categories = category_info.get("predicted_categories", [category_info["predicted_category"]])
    matched_docs = retrieve_category_solutions(
        query=sanitized_prompt,
        categories=active_categories,
    )

    # Step 4: Solution Synthesis
    raw_solution = synthesize_solution(sanitized_prompt, category_info, matched_docs)

    # Step 5: Output Guardrail Sanitization using llm-guard
    sanitized_actions = [
        sanitize_output(sanitized_prompt, action)
        for action in raw_solution.get("suggested_actions", [])
    ]
    raw_solution["suggested_actions"] = sanitized_actions

    return raw_solution