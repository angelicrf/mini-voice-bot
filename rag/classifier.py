from __future__ import annotations
from typing import Any, Dict, List, Optional, Set

from transformers import pipeline

from rag.config import CATEGORY_EXEMPLARS, CATEGORY_LABELS

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


def _tokenize(text: str) -> Set[str]:
    """Simple tokenizer removing non-alphanumeric characters."""
    return set("".join(c if c.isalnum() else " " for c in text.lower()).split())


def _matches_keyword(kw: str, tokens: Set[str], full_text: str) -> bool:
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
            pass

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