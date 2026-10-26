from __future__ import annotations
import re
from pathlib import Path
from typing import List, Optional

from rag.config import CATEGORY_LABELS, DEFAULT_PLAYBOOKS, PBS_DIR
from rag.models import KnowledgeDocument


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

    raw_sections = re.split(r"(?m)^(?=#{1,4}\s+)", content)
    docs: List[KnowledgeDocument] = []

    for idx, block in enumerate(raw_sections):
        block = block.strip()
        if not block:
            continue
        first_line, _, _ = block.partition("\n")
        section_title = first_line.lstrip("#").strip() if first_line.startswith("#") else f"{filepath.stem} - Section {idx + 1}"

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
    """Reads all playbook (.md and .txt) files inside the pbs directory."""
    target_dir = pbs_dir or PBS_DIR
    target_dir.mkdir(parents=True, exist_ok=True)

    playbook_files = sorted(list(target_dir.glob("*.md")) + list(target_dir.glob("*.txt")))
    if not playbook_files:
        for filename, content in DEFAULT_PLAYBOOKS.items():
            (target_dir / filename).write_text(content, encoding="utf-8")
        playbook_files = sorted(list(target_dir.glob("*.md")) + list(target_dir.glob("*.txt")))

    docs: List[KnowledgeDocument] = []
    for filepath in playbook_files:
        docs.extend(_parse_playbook_sections(filepath))
    return docs