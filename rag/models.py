from __future__ import annotations
from dataclasses import dataclass
from typing import List


@dataclass
class KnowledgeDocument:
    doc_id: str
    category: str
    title: str
    content: str
    solution_steps: List[str]