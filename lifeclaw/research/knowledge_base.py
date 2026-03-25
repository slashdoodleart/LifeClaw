"""Per-run knowledge base — structured knowledge across 6 categories.

Every research run builds a queryable KB that persists across stages.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class KBEntry:
    category: str  # decisions, experiments, findings, literature, questions, reviews
    content: str
    stage: str = ""
    timestamp: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class RunKnowledgeBase:
    """Structured knowledge base for a single research run."""

    CATEGORIES = [
        "decisions",    # PROCEED/REFINE/PIVOT decisions with rationale
        "experiments",  # Experiment configs, results, metrics
        "findings",     # Key insights and observations
        "literature",   # Papers found, summaries, gaps identified
        "questions",    # Open research questions and hypotheses
        "reviews",      # Peer review comments, quality assessments
    ]

    def __init__(self, run_dir: Path):
        self.run_dir = run_dir
        self.kb_dir = run_dir / "knowledge_base"
        self.kb_dir.mkdir(parents=True, exist_ok=True)
        self.entries: list[KBEntry] = []
        self._load()

    def _load(self):
        kb_file = self.kb_dir / "kb.json"
        if kb_file.exists():
            data = json.loads(kb_file.read_text())
            self.entries = [KBEntry(**e) for e in data]

    def _save(self):
        kb_file = self.kb_dir / "kb.json"
        data = [
            {
                "category": e.category,
                "content": e.content,
                "stage": e.stage,
                "timestamp": e.timestamp,
                "metadata": e.metadata,
            }
            for e in self.entries
        ]
        kb_file.write_text(json.dumps(data, indent=2))

    def add(self, category: str, content: str, stage: str = "", **metadata) -> KBEntry:
        entry = KBEntry(
            category=category,
            content=content,
            stage=stage,
            metadata=metadata,
        )
        self.entries.append(entry)
        self._save()
        return entry

    def query(self, category: str | None = None, keyword: str = "") -> list[KBEntry]:
        results = self.entries
        if category:
            results = [e for e in results if e.category == category]
        if keyword:
            kw = keyword.lower()
            results = [e for e in results if kw in e.content.lower()]
        return results

    def get_context_for_stage(self, stage: str) -> str:
        """Build context string from KB entries relevant to a stage."""
        relevant = self.entries[-50:]  # Last 50 entries
        if not relevant:
            return ""

        lines = ["[Knowledge Base — accumulated from previous stages]"]
        by_cat: dict[str, list[str]] = {}
        for e in relevant:
            by_cat.setdefault(e.category, []).append(e.content[:200])

        for cat, items in by_cat.items():
            lines.append(f"\n## {cat.title()}")
            for item in items[-5:]:  # Last 5 per category
                lines.append(f"- {item}")

        return "\n".join(lines)

    def export_markdown(self) -> str:
        """Export full KB as markdown."""
        lines = ["# Research Knowledge Base\n"]
        for cat in self.CATEGORIES:
            entries = self.query(category=cat)
            if entries:
                lines.append(f"\n## {cat.title()} ({len(entries)} entries)\n")
                for e in entries:
                    lines.append(f"- **[{e.stage}]** {e.content[:300]}")
        return "\n".join(lines)

    @property
    def stats(self) -> dict:
        by_cat = {}
        for cat in self.CATEGORIES:
            by_cat[cat] = len(self.query(category=cat))
        return {"total": len(self.entries), "by_category": by_cat}
