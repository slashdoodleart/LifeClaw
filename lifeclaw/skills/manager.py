"""Skills manager - loads and manages agent skills."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from loguru import logger


@dataclass
class Skill:
    name: str
    description: str
    system_prompt: str
    tools: list[str]  # tool names this skill uses
    category: str = "general"
    version: str = "1.0.0"


# Built-in skills that come with LifeClaw
BUILTIN_SKILLS: list[Skill] = [
    Skill(
        name="coder",
        description="Expert coding assistant - writes, debugs, and refactors code",
        system_prompt=(
            "You are an expert software engineer. Write clean, efficient code. "
            "Use tools to read existing code before making changes. "
            "Always explain your approach before writing code."
        ),
        tools=["read_file", "write_file", "run_command", "search_files", "search_content"],
        category="development",
    ),
    Skill(
        name="shell",
        description="System administration and shell command expert",
        system_prompt=(
            "You are a system administration expert. Help users with shell commands, "
            "system configuration, and automation. Always explain what commands do."
        ),
        tools=["run_command", "read_file", "list_directory"],
        category="system",
    ),
    Skill(
        name="researcher",
        description="Research and analyze information from files and web",
        system_prompt=(
            "You are a research assistant. Analyze files, codebases, and information "
            "to provide comprehensive answers. Be thorough and cite sources."
        ),
        tools=["read_file", "search_files", "search_content", "list_directory"],
        category="research",
    ),
    Skill(
        name="writer",
        description="Technical writing assistant for docs, READMEs, and content",
        system_prompt=(
            "You are a technical writing expert. Help create clear, well-structured "
            "documentation, READMEs, blog posts, and other content."
        ),
        tools=["read_file", "write_file", "search_content"],
        category="writing",
    ),
    Skill(
        name="git-expert",
        description="Git workflow assistant - commits, branches, PRs, merge conflicts",
        system_prompt=(
            "You are a Git expert. Help with version control workflows, resolving "
            "merge conflicts, writing commit messages, and managing branches."
        ),
        tools=["run_command", "read_file", "search_content"],
        category="development",
    ),
]


class SkillsManager:
    def __init__(self, skills_dir: str | Path = "~/.lifeclaw/skills"):
        self.skills_dir = Path(skills_dir).expanduser()
        self.skills_dir.mkdir(parents=True, exist_ok=True)
        self._skills: dict[str, Skill] = {}
        self._load_builtins()
        self._load_custom()

    def _load_builtins(self) -> None:
        for skill in BUILTIN_SKILLS:
            self._skills[skill.name] = skill

    def _load_custom(self) -> None:
        """Load custom skills from skills directory."""
        for path in self.skills_dir.glob("*.json"):
            try:
                data = json.loads(path.read_text())
                skill = Skill(
                    name=data["name"],
                    description=data.get("description", ""),
                    system_prompt=data.get("system_prompt", ""),
                    tools=data.get("tools", []),
                    category=data.get("category", "custom"),
                    version=data.get("version", "1.0.0"),
                )
                self._skills[skill.name] = skill
            except Exception as e:
                logger.warning(f"Failed to load skill {path.name}: {e}")

    def get(self, name: str) -> Skill | None:
        return self._skills.get(name)

    def list_skills(self) -> list[Skill]:
        return list(self._skills.values())

    def install(self, skill_data: dict) -> Skill:
        """Install a skill from a dict definition."""
        skill = Skill(
            name=skill_data["name"],
            description=skill_data.get("description", ""),
            system_prompt=skill_data.get("system_prompt", ""),
            tools=skill_data.get("tools", []),
            category=skill_data.get("category", "custom"),
            version=skill_data.get("version", "1.0.0"),
        )
        # Save to disk
        path = self.skills_dir / f"{skill.name}.json"
        path.write_text(json.dumps(skill_data, indent=2))
        self._skills[skill.name] = skill
        return skill

    def remove(self, name: str) -> bool:
        if name in self._skills:
            path = self.skills_dir / f"{name}.json"
            if path.exists():
                path.unlink()
            del self._skills[name]
            return True
        return False
