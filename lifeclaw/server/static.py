"""Simple HTTP server to serve the web dashboard."""

import asyncio
from pathlib import Path

from loguru import logger


async def serve_web(host: str = "127.0.0.1", port: int = 3120):
    """Serve the built web dashboard via a simple HTTP handler."""
    # Try Vite build output first, then dev fallbacks
    base = Path(__file__).parent.parent.parent / "web"
    for candidate in ["dist", "out", ".next", "."]:
        web_dir = base / candidate
        if web_dir.exists() and (web_dir / "index.html").exists():
            break
    else:
        # Fallback: serve the web/ root which has index.html
        web_dir = base
        if not (web_dir / "index.html").exists():
            logger.warning(f"No web build found. Run: cd web && npm install && npm run build")
            return

    import http.server
    import functools

    handler = functools.partial(
        http.server.SimpleHTTPRequestHandler,
        directory=str(web_dir),
    )

    loop = asyncio.get_event_loop()
    server = await loop.run_in_executor(
        None,
        lambda: http.server.HTTPServer((host, port), handler),
    )
    logger.info(f"Web dashboard at http://{host}:{port}")

    # Run in background thread
    loop.run_in_executor(None, server.serve_forever)
