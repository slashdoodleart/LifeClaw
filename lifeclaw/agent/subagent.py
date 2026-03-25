"""Sub-agent system — spawn isolated agents for parallel task execution.

Each sub-agent gets its own memory context and can work independently.
"""

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Coroutine

from loguru import logger


@dataclass
class SubAgentTask:
    id: str
    name: str
    prompt: str
    status: str = "pending"  # pending, running, completed, failed
    result: str = ""
    started_at: str = ""
    completed_at: str = ""
    error: str = ""


class SubAgentManager:
    """Manages parallel sub-agent execution for complex multi-step tasks."""

    def __init__(self, agent_factory: Callable[[], Any]):
        """agent_factory should return a new AgentLoop instance with fresh memory."""
        self.agent_factory = agent_factory
        self.tasks: dict[str, SubAgentTask] = {}
        self._running_tasks: dict[str, asyncio.Task] = {}

    def spawn(self, name: str, prompt: str) -> SubAgentTask:
        """Create a new sub-agent task (doesn't start execution yet)."""
        task = SubAgentTask(
            id=str(uuid.uuid4())[:8],
            name=name,
            prompt=prompt,
        )
        self.tasks[task.id] = task
        return task

    async def execute(self, task_id: str) -> str:
        """Execute a single sub-agent task."""
        task = self.tasks.get(task_id)
        if not task:
            return f"Task {task_id} not found"

        task.status = "running"
        task.started_at = datetime.now().isoformat()

        try:
            agent = self.agent_factory()
            result = await agent.process(task.prompt)
            task.result = result
            task.status = "completed"
            task.completed_at = datetime.now().isoformat()
            return result
        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            task.completed_at = datetime.now().isoformat()
            logger.error(f"Sub-agent '{task.name}' failed: {e}")
            return f"Error: {e}"

    async def execute_parallel(self, task_ids: list[str]) -> dict[str, str]:
        """Execute multiple sub-agent tasks in parallel."""
        results = {}
        coros = []
        for tid in task_ids:
            coros.append(self.execute(tid))

        completed = await asyncio.gather(*coros, return_exceptions=True)
        for tid, result in zip(task_ids, completed):
            if isinstance(result, Exception):
                results[tid] = f"Error: {result}"
            else:
                results[tid] = result
        return results

    async def run_workflow(self, steps: list[dict]) -> list[str]:
        """Execute a multi-step workflow.

        Each step is a dict with:
          - name: str
          - prompt: str
          - parallel: bool (optional, default False)
          - depends_on: list[str] (optional, task IDs to wait for)
        """
        results = []
        for step in steps:
            task = self.spawn(step["name"], step["prompt"])
            if step.get("parallel"):
                # Don't await, just start
                self._running_tasks[task.id] = asyncio.create_task(self.execute(task.id))
            else:
                result = await self.execute(task.id)
                results.append(result)
        # Wait for any remaining parallel tasks
        for tid, atask in self._running_tasks.items():
            result = await atask
            results.append(result)
        self._running_tasks.clear()
        return results

    def list_tasks(self) -> list[SubAgentTask]:
        return list(self.tasks.values())

    def get_task(self, task_id: str) -> SubAgentTask | None:
        return self.tasks.get(task_id)
