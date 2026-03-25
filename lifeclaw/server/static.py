"""Simple HTTP server to serve the web dashboard."""

import asyncio
import os
from pathlib import Path

from loguru import logger


async def serve_web(host: str = "127.0.0.1", port: int = 3120):
    """Serve the built web dashboard via a simple HTTP handler."""
    web_dir = Path(__file__).parent.parent.parent / "web" / "out"
    if not web_dir.exists():
        web_dir = Path(__file__).parent.parent.parent / "web" / ".next"

    # Use Python's built-in http.server in a thread
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
    logger.info(f"Static server at http://{host}:{port}")

    await loop.run_in_executor(None, server.serve_forever)
