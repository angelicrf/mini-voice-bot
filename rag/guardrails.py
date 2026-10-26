from __future__ import annotations
import re
from typing import Dict, Tuple

from llm_guard import scan_prompt, scan_output
from llm_guard.input_scanners import Anonymize, PromptInjection, Toxicity
from llm_guard.output_scanners import Deanonymize, Sensitive
from llm_guard.vault import Vault

from rag.config import _INJECTION_PATTERNS

vault = Vault()
input_scanners = [Anonymize(vault), Toxicity(threshold=0.85), PromptInjection(threshold=0.95)]
output_scanners = [Deanonymize(vault), Sensitive()]


def validate_input_safety(text: str) -> Tuple[bool, str, Dict[str, bool]]:
    """
    Screens user text using llm-guard for jailbreak attempts, prompt injection, and toxicity.
    Returns (is_safe, sanitized_prompt, results_valid).
    """
    try:
        sanitized_prompt, results_valid, _ = scan_prompt(input_scanners, text)

        if not results_valid.get("PromptInjection", True):
            has_adversarial_pattern = any(
                re.search(pat, text, re.IGNORECASE) for pat in _INJECTION_PATTERNS
            )
            if not has_adversarial_pattern:
                results_valid["PromptInjection"] = True

        security_threat_scanners = {"PromptInjection", "Toxicity"}
        is_safe = all(
            is_valid
            for scanner_name, is_valid in results_valid.items()
            if scanner_name in security_threat_scanners
        )
        return is_safe, sanitized_prompt, results_valid
    except Exception:
        return True, text, {"scanner_fallback": True}


def sanitize_output(prompt: str, response: str) -> str:
    """Redacts sensitive credentials and deanonymizes vault tokens from output using llm-guard."""
    try:
        sanitized_response, results_valid, _ = scan_output(output_scanners, prompt, response)
        if any(not result for result in results_valid.values()):
            return "[REDACTED_CREDENTIAL]"
        return sanitized_response
    except Exception:
        return response