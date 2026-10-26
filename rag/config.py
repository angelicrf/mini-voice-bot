from __future__ import annotations
from pathlib import Path
from typing import Dict, List

# Points to the 'pbs' directory located in the project root
PBS_DIR = Path(__file__).resolve().parent.parent / "pbs"

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

CATEGORY_LABELS: Dict[str, str] = {
    "image and file troubleshooting": "image_file_troubleshooting",
    "engineering task assignment": "engineering_task_assignment",
    "technical support and audio issues": "technical_support",
    "billing and payment inquiries": "billing",
    "account access and authentication": "account_access",
    "general inquiry": "general_inquiry",
}

CATEGORY_EXEMPLARS: Dict[str, List[str]] = {
    "image_file_troubleshooting": ["image", "photo", "picture", "file", "format", "corrupted", "upload", "png", "jpg", "jpeg", "tiff", "vision", "render"],
    "engineering_task_assignment": ["engineer", "task", "assigned", "assign", "ticket", "developer", "jira", "escalate", "bug report", "dev team", "investigate"],
    "technical_support": ["not working", "broken", "sound error", "error code", "bug", "crash", "audio fail", "noise"],
    "billing": ["charge", "invoice", "refund", "subscription", "credit card", "payment", "cost", "pricing"],
    "account_access": ["login", "sign in", "password", "locked out", "username", "2fa", "authentication"],
    "general_inquiry": ["hello", "hours", "contact", "support", "information", "what is this"]
}

_INJECTION_PATTERNS: List[str] = [
    r"ignore\s+(?:all\s+|any\s+|previous\s+|prior\s+|above\s+)?(?:instructions|prompts|rules)",
    r"disregard\s+(?:all\s+|previous\s+|prior\s+)?(?:instructions|prompts|rules)",
    r"(?:system\s+prompt|developer\s+mode|jailbreak|dan\s+mode)",
    r"bypass\s+(?:filter|safety|rules|guardrails)",
    r"(?:reveal|show|display|print)\s+(?:the\s+)?(?:system\s+prompt|secret|instructions)",
]