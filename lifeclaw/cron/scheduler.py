"""Lightweight cron scheduler for recurring agent tasks."""

import asyncio
import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Coroutine

from loguru import logger


@dataclass
class CronJob:
    id: str
    name: str
    prompt: str  # What to tell the agent
    schedule: str  # Cron expression or interval like "5m", "1h", "daily"
    enabled: bool = True
    last_run: str | None = None
    channel: str | None = None  # Optional: route output to a channel
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


def _parse_interval(schedule: str) -> float:
    """Parse interval strings like '5m', '1h', '30s', 'daily'."""
    shortcuts = {"daily": 86400, "hourly": 3600, "weekly": 604800}
    if schedule.lower() in shortcuts:
        return shortcuts[schedule.lower()]
    match = re.match(r"^(\d+)(s|m|h|d)$", schedule.strip())
    if not match:
        raise ValueError(f"Invalid schedule: {schedule}. Use '5m', '1h', '30s', 'daily', etc.")
    value, unit = int(match.group(1)), match.group(2)
    multipliers = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    return value * multipliers[unit]


class CronScheduler:
    """Manages and executes scheduled agent tasks."""

    def __init__(self, cron_dir: str | Path = "~/.lifeclaw/cron"):
        self.cron_dir = Path(cron_dir).expanduser()
        self.cron_dir.mkdir(parents=True, exist_ok=True)
        self.jobs: dict[str, CronJob] = {}
        self._tasks: dict[str, asyncio.Task] = {}
        self._handler: Callable[[str], Coroutine[Any, Any, str]] | None = None
        self._load_jobs()

    def _load_jobs(self) -> None:
        jobs_file = self.cron_dir / "jobs.json"
        if jobs_file.exists():
            data = json.loads(jobs_file.read_text())
            for item in data:
                job = CronJob(**item)
                self.jobs[job.id] = job

    def _save_jobs(self) -> None:
        jobs_file = self.cron_dir / "jobs.json"
        data = []
        for job in self.jobs.values():
            data.append({
                "id": job.id,
                "name": job.name,
                "prompt": job.prompt,
                "schedule": job.schedule,
                "enabled": job.enabled,
                "last_run": job.last_run,
                "channel": job.channel,
                "created_at": job.created_at,
            })
        jobs_file.write_text(json.dumps(data, indent=2))

    def add_job(self, name: str, prompt: str, schedule: str, channel: str | None = None) -> CronJob:
        import hashlib
        job_id = hashlib.md5(f"{name}{prompt}{schedule}".encode()).hexdigest()[:8]
        job = CronJob(id=job_id, name=name, prompt=prompt, schedule=schedule, channel=channel)
        self.jobs[job_id] = job
        self._save_jobs()
        return job

    def remove_job(self, job_id: str) -> bool:
        if job_id in self.jobs:
            del self.jobs[job_id]
            self._save_jobs()
            if job_id in self._tasks:
                self._tasks[job_id].cancel()
                del self._tasks[job_id]
            return True
        return False

    def list_jobs(self) -> list[CronJob]:
        return list(self.jobs.values())

    async def start(self, handler: Callable[[str], Coroutine[Any, Any, str]]) -> None:
        """Start all enabled cron jobs."""
        self._handler = handler
        for job_id, job in self.jobs.items():
            if job.enabled:
                self._tasks[job_id] = asyncio.create_task(self._run_job(job))
        if self.jobs:
            logger.info(f"Cron: {len(self._tasks)} jobs scheduled")

    async def stop(self) -> None:
        for task in self._tasks.values():
            task.cancel()
        self._tasks.clear()

    async def _run_job(self, job: CronJob) -> None:
        interval = _parse_interval(job.schedule)
        while True:
            try:
                await asyncio.sleep(interval)
                if self._handler:
                    logger.info(f"Cron: executing '{job.name}'")
                    result = await self._handler(job.prompt)
                    job.last_run = datetime.now().isoformat()
                    self._save_jobs()
                    # Log output
                    log_file = self.cron_dir / f"{job.id}.log"
                    with open(log_file, "a") as f:
                        f.write(f"\n--- {job.last_run} ---\n{result}\n")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cron job '{job.name}' failed: {e}")
                await asyncio.sleep(60)  # Back off on error
