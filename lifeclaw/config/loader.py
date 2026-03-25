"""Load and save LifeClaw configuration."""

import json
from pathlib import Path

from lifeclaw.config.schema import Config, MCPServerConfig, get_config_path


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


def import_external_mcp(config: Config) -> Config:
    """Import MCP servers from external tool configs if available.

    Checks common config locations for MCP server definitions and
    imports them into LifeClaw's config. Sensitive keys (tokens, secrets)
    are stored locally in ~/.lifeclaw/config.json which should not be
    committed to git.
    """
    # Check ~/.claude/mcp.json (common MCP config location)
    mcp_path = Path.home() / ".claude" / "mcp.json"
    if mcp_path.exists():
        try:
            data = json.loads(mcp_path.read_text())
            servers = data.get("mcpServers", {})
            for name, srv in servers.items():
                if name not in config.mcp_servers:
                    config.mcp_servers[name] = MCPServerConfig(
                        command=srv.get("command", ""),
                        args=srv.get("args", []),
                        env=srv.get("env", {}),
                    )
        except Exception:
            pass

    # Check plugin cache for MCP definitions
    plugins_cache = Path.home() / ".claude" / "plugins" / "cache"
    if plugins_cache.exists():
        for mcp_file in plugins_cache.rglob(".mcp.json"):
            try:
                data = json.loads(mcp_file.read_text())
                # Handle both formats: {"name": {...}} and {"mcpServers": {"name": {...}}}
                servers = data.get("mcpServers", data)
                for name, srv in servers.items():
                    if name == "mcpServers":
                        continue
                    if name not in config.mcp_servers and isinstance(srv, dict):
                        srv_type = srv.get("type", "stdio")
                        if srv_type == "stdio":
                            config.mcp_servers[name] = MCPServerConfig(
                                command=srv.get("command", ""),
                                args=srv.get("args", []),
                                env=srv.get("env", {}),
                            )
                        # HTTP-based MCP servers stored for reference but need
                        # different handling (future enhancement)
            except Exception:
                pass

    return config


def discover_external_skills() -> list[dict]:
    """Discover skill definitions from external plugin directories.

    Looks for SKILL.md files in plugin caches. Each SKILL.md defines a skill
    with optional frontmatter (name, description). The skill name is derived
    from the parent directory name.

    Returns a list of skill dicts that can be registered with SkillsManager.
    """
    skills = []
    seen_names: set[str] = set()
    plugins_dir = Path.home() / ".claude" / "plugins"

    if not plugins_dir.exists():
        return skills

    cache_dir = plugins_dir / "cache"
    if not cache_dir.exists():
        return skills

    # Find all SKILL.md files — these are the canonical skill definitions
    for skill_file in cache_dir.rglob("SKILL.md"):
        try:
            content = skill_file.read_text(errors="replace")
            # Skill name from parent directory (e.g., .../skills/debugging/SKILL.md -> debugging)
            name = skill_file.parent.name

            # Skip duplicates
            if name in seen_names:
                continue
            seen_names.add(name)

            # Parse frontmatter for description
            desc = ""
            in_frontmatter = False
            for line in content.split("\n")[:20]:
                if line.strip() == "---":
                    in_frontmatter = not in_frontmatter
                    continue
                if in_frontmatter:
                    if line.startswith("description:"):
                        desc = line.split(":", 1)[1].strip().strip('"').strip("'")
                    elif line.startswith("name:"):
                        parsed_name = line.split(":", 1)[1].strip().strip('"').strip("'")
                        if parsed_name:
                            # Update name but check for duplicates
                            if parsed_name in seen_names:
                                continue
                            seen_names.discard(name)
                            name = parsed_name
                            seen_names.add(name)

            if not desc:
                # Try first non-frontmatter line as description
                for line in content.split("\n"):
                    line = line.strip()
                    if line and not line.startswith("---") and not line.startswith("#"):
                        desc = line[:120]
                        break
                if not desc:
                    desc = f"Imported skill: {name}"

            skills.append({
                "name": name,
                "description": desc,
                "system_prompt": content[:3000],
                "tools": ["read_file", "write_file", "run_command", "search_files", "search_content"],
                "category": "imported",
                "version": "1.0.0",
            })
        except Exception:
            pass

    return skills
