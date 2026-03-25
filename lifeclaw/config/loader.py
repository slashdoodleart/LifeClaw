"""Load and save LifeClaw configuration."""

import json
from pathlib import Path

from lifeclaw.config.schema import Config, get_config_path


def load_config() -> Config:
    path = get_config_path()
    if path.exists():
        data = json.loads(path.read_text())
        return Config(**data)
    return Config()


def save_config(config: Config) -> None:
    path = get_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(config.model_dump_json(indent=2))


def merge_claude_mcp(config: Config) -> Config:
    """Import MCP servers from ~/.claude/mcp.json if available.

    Imports ALL servers including their environment variables.
    Sensitive keys (tokens, secrets) are imported but stored locally
    in ~/.lifeclaw/config.json which should not be committed to git.
    """
    claude_mcp = Path.home() / ".claude" / "mcp.json"
    if not claude_mcp.exists():
        return config

    data = json.loads(claude_mcp.read_text())
    servers = data.get("mcpServers", {})
    from lifeclaw.config.schema import MCPServerConfig

    for name, srv in servers.items():
        if name not in config.mcp_servers:
            config.mcp_servers[name] = MCPServerConfig(
                command=srv.get("command", ""),
                args=srv.get("args", []),
                env=srv.get("env", {}),
            )
    return config


def merge_claude_skills(config: Config) -> list[dict]:
    """Discover skills from Claude Code plugins directory.

    Returns a list of skill definitions that can be registered with SkillsManager.
    """
    skills = []
    plugins_dir = Path.home() / ".claude" / "plugins"

    if not plugins_dir.exists():
        return skills

    # Scan for skill files in plugin cache
    cache_dir = plugins_dir / "cache"
    if cache_dir.exists():
        for skill_file in cache_dir.rglob("*.md"):
            if "skills" in str(skill_file) and skill_file.stem not in ("README", "CHANGELOG"):
                try:
                    content = skill_file.read_text(errors="replace")
                    # Extract name from frontmatter or filename
                    name = skill_file.stem
                    desc = ""
                    for line in content.split("\n")[:10]:
                        if line.startswith("description:"):
                            desc = line.split(":", 1)[1].strip()
                            break
                    if not desc:
                        desc = f"Imported skill: {name}"

                    skills.append({
                        "name": f"cc-{name}",
                        "description": desc,
                        "system_prompt": content[:2000],
                        "tools": ["read_file", "write_file", "run_command", "search_files", "search_content"],
                        "category": "claude-code",
                        "version": "1.0.0",
                    })
                except Exception:
                    pass

    return skills
