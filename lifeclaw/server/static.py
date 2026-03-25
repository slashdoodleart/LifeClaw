"""Simple HTTP server to serve the web dashboard."""

import asyncio
import threading
from pathlib import Path

from loguru import logger


_server = None


async def serve_web(host: str = "127.0.0.1", port: int = 3120):
    """Serve the built web dashboard via a simple HTTP handler."""
    global _server

    # Try Vite build output first, then dev fallbacks
    base = Path(__file__).parent.parent.parent / "web"
    for candidate in ["dist", "out", ".next", "."]:
        web_dir = base / candidate
        if web_dir.exists() and (web_dir / "index.html").exists():
            break
    else:
        web_dir = base
        if not (web_dir / "index.html").exists():
            logger.warning("No web build found. Run: cd web && npm install && npm run build")
            return

    import http.server
    import functools

    handler = functools.partial(
        http.server.SimpleHTTPRequestHandler,
        directory=str(web_dir),
    )

    _server = http.server.HTTPServer((host, port), handler)
    logger.info(f"Web dashboard at http://{host}:{port}")

    # Run in daemon thread so it dies with the main process
    t = threading.Thread(target=_server.serve_forever, daemon=True)
    t.start()


async def stop_web():
    """Shut down the static file server cleanly."""
    global _server
    if _server:
        _server.shutdown()
        _server = None
