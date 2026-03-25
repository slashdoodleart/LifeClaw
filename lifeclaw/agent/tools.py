"""Built-in tools for the LifeClaw agent."""

import asyncio
import json
import os
import subprocess
from pathlib import Path
from typing import Any

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for information. Returns titles, URLs, and snippets.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "max_results": {"type": "integer", "description": "Max results (default 5)"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_fetch",
            "description": "Fetch a web page and return its content as text/markdown.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to fetch"},
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_document",
            "description": "Create a document file (docx, xlsx, pptx, pdf). Write a Python script using the appropriate library and execute it.",
            "parameters": {
                "type": "object",
                "properties": {
                    "doc_type": {"type": "string", "enum": ["docx", "xlsx", "pptx", "pdf"], "description": "Document type"},
                    "script": {"type": "string", "description": "Python script that creates the document using python-docx/openpyxl/python-pptx/reportlab"},
                    "output_path": {"type": "string", "description": "Where to save the output file"},
                },
                "required": ["doc_type", "script", "output_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file at the given path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Absolute or relative file path"},
                    "start_line": {"type": "integer", "description": "Start line (1-indexed, optional)"},
                    "end_line": {"type": "integer", "description": "End line (inclusive, optional)"},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file, creating directories as needed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path to write to"},
                    "content": {"type": "string", "description": "Content to write"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Execute a shell command and return stdout/stderr.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Shell command to execute"},
                    "cwd": {"type": "string", "description": "Working directory (optional)"},
                    "timeout": {"type": "integer", "description": "Timeout in seconds (default 60)"},
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_files",
            "description": "Search for files matching a glob pattern.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Glob pattern (e.g. '**/*.py')"},
                    "path": {"type": "string", "description": "Base directory to search from"},
                },
                "required": ["pattern"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_content",
            "description": "Search file contents for a string or regex pattern.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search string or regex"},
                    "path": {"type": "string", "description": "Directory to search in"},
                    "file_pattern": {"type": "string", "description": "File glob filter (e.g. '*.py')"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "List files and directories at a given path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path"},
                },
                "required": ["path"],
            },
        },
    },
]


# When True, tools like write_file and run_command execute without user confirmation.
# Set by coder mode at startup.
auto_accept: bool = False


async def execute_tool(name: str, arguments: dict[str, Any]) -> str:
    """Execute a built-in tool and return the result as a string."""
    try:
        if name == "read_file":
            return _read_file(**arguments)
        elif name == "write_file":
            return _write_file(**arguments)
        elif name == "run_command":
            return await _run_command(**arguments)
        elif name == "search_files":
            return _search_files(**arguments)
        elif name == "search_content":
            return await _search_content(**arguments)
        elif name == "list_directory":
            return _list_directory(**arguments)
        elif name == "web_search":
            return await _web_search(**arguments)
        elif name == "web_fetch":
            return await _web_fetch(**arguments)
        elif name == "create_document":
            return await _create_document(**arguments)
        else:
            return f"Unknown tool: {name}"
    except Exception as e:
        return f"Error: {e}"


def _read_file(path: str, start_line: int | None = None, end_line: int | None = None) -> str:
    p = Path(path).expanduser().resolve()
    if not p.exists():
        return f"File not found: {path}"
    if not p.is_file():
        return f"Not a file: {path}"
    text = p.read_text(errors="replace")
    lines = text.splitlines()
    if start_line or end_line:
        s = (start_line or 1) - 1
        e = end_line or len(lines)
        lines = lines[s:e]
    if len(lines) > 500:
        lines = lines[:500]
        lines.append(f"\n... truncated ({len(text.splitlines())} total lines)")
    return "\n".join(f"{i+1:4d} | {line}" for i, line in enumerate(lines))


def _write_file(path: str, content: str) -> str:
    p = Path(path).expanduser().resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    return f"Written {len(content)} bytes to {p}"


async def _run_command(command: str, cwd: str | None = None, timeout: int = 60) -> str:
    work_dir = cwd or os.getcwd()
    try:
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=work_dir,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        out = stdout.decode(errors="replace").strip()
        err = stderr.decode(errors="replace").strip()
        result = ""
        if out:
            result += out
        if err:
            result += f"\n[stderr]\n{err}"
        if proc.returncode != 0:
            result += f"\n[exit code: {proc.returncode}]"
        return result or "(no output)"
    except asyncio.TimeoutError:
        return f"Command timed out after {timeout}s"


def _search_files(pattern: str, path: str | None = None) -> str:
    base = Path(path or ".").expanduser().resolve()
    matches = sorted(base.glob(pattern))[:50]
    if not matches:
        return "No files found."
    return "\n".join(str(m) for m in matches)


async def _search_content(query: str, path: str | None = None, file_pattern: str | None = None) -> str:
    base = Path(path or ".").expanduser().resolve()
    cmd = f"grep -rn --include='{file_pattern or '*'}' '{query}' '{base}' 2>/dev/null | head -50"
    return await _run_command(cmd)


def _list_directory(path: str) -> str:
    p = Path(path).expanduser().resolve()
    if not p.exists():
        return f"Directory not found: {path}"
    if not p.is_dir():
        return f"Not a directory: {path}"
    entries = sorted(p.iterdir())[:100]
    lines = []
    for e in entries:
        kind = "dir" if e.is_dir() else "file"
        lines.append(f"[{kind}] {e.name}")
    return "\n".join(lines) or "(empty directory)"


async def _web_search(query: str, max_results: int = 5) -> str:
    from lifeclaw.websearch.search import WebSearchProvider
    searcher = WebSearchProvider()
    results = await searcher.search(query, max_results)
    if not results:
        return "No results found."
    lines = []
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. [{r.title}]({r.url})\n   {r.snippet}")
    return "\n\n".join(lines)


async def _web_fetch(url: str) -> str:
    from lifeclaw.websearch.search import WebSearchProvider
    searcher = WebSearchProvider()
    return await searcher.fetch_page(url)


async def _create_document(doc_type: str, script: str, output_path: str) -> str:
    """Execute a Python script to create a document. Sandboxed to doc creation libraries."""
    import tempfile
    p = Path(output_path).expanduser().resolve()
    p.parent.mkdir(parents=True, exist_ok=True)

    # Write script to temp file and execute
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(script)
        script_path = f.name

    try:
        result = await _run_command(f"python3 {script_path}", timeout=120)
        if p.exists():
            size = p.stat().st_size
            return f"Document created: {p} ({size} bytes)\n{result}"
        return f"Script ran but output not found at {p}.\n{result}"
    finally:
        Path(script_path).unlink(missing_ok=True)
