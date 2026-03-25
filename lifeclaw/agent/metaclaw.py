"""MetaClaw — cross-run learning system.

Extracts structured lessons from pipeline runs and injects them into
future sessions. Failures become reusable skills.

Inspired by MetaClaw (aiming-lab/MetaClaw).
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger


@dataclass
class Lesson:
    id: str
    category: str  # "error-recovery", "optimization", "pattern", "anti-pattern"
    trigger: str  # When to apply this lesson
    content: str  # What was learned
    source_run: str  # Which run produced this lesson
    confidence: float = 0.5  # 0.0-1.0 how reliable
    times_applied: int = 0
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


class MetaClawBridge:
    """Manages cross-run learning — failures become reusable lessons."""

    def __init__(self, store_path: str | Path = "~/.lifeclaw/metaclaw"):
        self.store_path = Path(store_path).expanduser()
        self.store_path.mkdir(parents=True, exist_ok=True)
        self.lessons: list[Lesson] = []
        self._load()

    def _load(self) -> None:
        lessons_file = self.store_path / "lessons.json"
        if lessons_file.exists():
            data = json.loads(lessons_file.read_text())
            self.lessons = [Lesson(**item) for item in data]

    def _save(self) -> None:
        lessons_file = self.store_path / "lessons.json"
        data = []
        for lesson in self.lessons:
            data.append({
                "id": lesson.id,
                "category": lesson.category,
                "trigger": lesson.trigger,
                "content": lesson.content,
                "source_run": lesson.source_run,
                "confidence": lesson.confidence,
                "times_applied": lesson.times_applied,
                "created_at": lesson.created_at,
            })
        lessons_file.write_text(json.dumps(data, indent=2))

    def extract_lesson(
        self,
        category: str,
        trigger: str,
        content: str,
        source_run: str,
        confidence: float = 0.5,
    ) -> Lesson:
        """Extract a lesson from a run and store it."""
        import hashlib
        lesson_id = hashlib.md5(f"{trigger}{content}".encode()).hexdigest()[:8]

        # Check for duplicate
        for existing in self.lessons:
            if existing.id == lesson_id:
                existing.confidence = min(1.0, existing.confidence + 0.1)
                self._save()
                return existing

        lesson = Lesson(
            id=lesson_id,
            category=category,
            trigger=trigger,
            content=content,
            source_run=source_run,
            confidence=confidence,
        )
        self.lessons.append(lesson)
        self._save()
        logger.info(f"MetaClaw: learned '{trigger}' ({category})")
        return lesson

    def get_relevant_lessons(self, context: str, max_results: int = 5) -> list[Lesson]:
        """Find lessons relevant to the current context."""
        scored = []
        context_lower = context.lower()
        for lesson in self.lessons:
            # Simple keyword matching (could be enhanced with embeddings)
            trigger_words = set(lesson.trigger.lower().split())
            context_words = set(context_lower.split())
            overlap = len(trigger_words & context_words)
            if overlap > 0:
                score = overlap * lesson.confidence
                scored.append((score, lesson))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [lesson for _, lesson in scored[:max_results]]

    def inject_lessons(self, context: str) -> str:
        """Generate a lessons injection string for the system prompt."""
        relevant = self.get_relevant_lessons(context)
        if not relevant:
            return ""

        lines = ["[MetaClaw Lessons — learned from previous runs]"]
        for lesson in relevant:
            lines.append(f"- [{lesson.category}] {lesson.content}")
            lesson.times_applied += 1
        self._save()
        return "\n".join(lines)

    def extract_from_error(self, error: str, fix: str, run_id: str) -> Lesson:
        """Learn from an error-fix pair."""
        return self.extract_lesson(
            category="error-recovery",
            trigger=error[:100],
            content=f"Error: {error[:200]}\nFix: {fix[:300]}",
            source_run=run_id,
            confidence=0.7,
        )

    def stats(self) -> dict:
        """Return learning statistics."""
        return {
            "total_lessons": len(self.lessons),
            "by_category": {},
            "avg_confidence": sum(l.confidence for l in self.lessons) / max(len(self.lessons), 1),
            "total_applications": sum(l.times_applied for l in self.lessons),
        }
