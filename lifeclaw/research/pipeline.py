"""23-stage autonomous research pipeline inspired by AutoResearchClaw.

Turns a research idea into a conference-ready paper with real literature,
experiments, statistical analysis, and multi-agent peer review.
"""

import asyncio
import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Coroutine

from loguru import logger


STAGES = [
    "topic-refinement",
    "research-question",
    "hypothesis-generation",
    "literature-search",
    "literature-synthesis",
    "gap-analysis",
    "methodology-design",
    "variable-definition",
    "experiment-design",
    "code-generation",
    "experiment-execution",
    "result-collection",
    "statistical-analysis",
    "visualization",
    "abstract-writing",
    "introduction-writing",
    "related-work-writing",
    "methodology-writing",
    "results-writing",
    "discussion-writing",
    "conclusion-writing",
    "peer-review",
    "final-revision",
]


@dataclass
class ResearchRun:
    """Tracks a single research pipeline execution."""
    topic: str
    run_id: str
    output_dir: Path
    current_stage: int = 0
    stages_completed: list[str] = field(default_factory=list)
    artifacts: dict[str, str] = field(default_factory=dict)
    started_at: str = ""
    completed_at: str | None = None
    status: str = "running"  # running, completed, failed, paused

    def __post_init__(self):
        if not self.started_at:
            self.started_at = datetime.now().isoformat()


class ResearchPipeline:
    """Executes the full autonomous research pipeline."""

    def __init__(
        self,
        agent_fn: Callable[[str], Coroutine[Any, Any, str]],
        output_base: str | Path = "./research_output",
    ):
        self.agent_fn = agent_fn
        self.output_base = Path(output_base)

    async def run(self, topic: str, auto_approve: bool = True) -> ResearchRun:
        """Execute the full 23-stage pipeline."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_id = f"rc-{ts}"
        output_dir = self.output_base / run_id
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "experiments").mkdir(exist_ok=True)
        (output_dir / "charts").mkdir(exist_ok=True)
        (output_dir / "deliverables").mkdir(exist_ok=True)

        run = ResearchRun(topic=topic, run_id=run_id, output_dir=output_dir)

        # Save run metadata
        self._save_state(run)
        logger.info(f"Research pipeline started: {run_id} — '{topic}'")

        for i, stage_name in enumerate(STAGES):
            run.current_stage = i
            try:
                prompt = self._stage_prompt(stage_name, topic, run)
                logger.info(f"Stage {i+1}/23: {stage_name}")

                result = await self.agent_fn(prompt)

                # Save stage output
                stage_file = output_dir / f"stage_{i+1:02d}_{stage_name}.md"
                stage_file.write_text(result)
                run.artifacts[stage_name] = str(stage_file)
                run.stages_completed.append(stage_name)
                self._save_state(run)

            except Exception as e:
                logger.error(f"Stage {stage_name} failed: {e}")
                run.status = "failed"
                self._save_state(run)
                # Self-healing: retry once
                try:
                    repair_prompt = (
                        f"The previous stage '{stage_name}' failed with error: {e}\n"
                        f"Please diagnose and retry. Context: researching '{topic}'.\n"
                        f"Completed stages so far: {', '.join(run.stages_completed)}"
                    )
                    result = await self.agent_fn(repair_prompt)
                    stage_file = output_dir / f"stage_{i+1:02d}_{stage_name}_repaired.md"
                    stage_file.write_text(result)
                    run.artifacts[stage_name] = str(stage_file)
                    run.stages_completed.append(stage_name)
                    run.status = "running"
                    self._save_state(run)
                except Exception as e2:
                    logger.error(f"Stage {stage_name} repair failed: {e2}")
                    break

        # Assemble final paper
        if len(run.stages_completed) >= 20:
            await self._assemble_paper(run)
            run.status = "completed"
        elif run.status != "failed":
            run.status = "completed"

        run.completed_at = datetime.now().isoformat()
        self._save_state(run)
        logger.info(f"Research pipeline {run.status}: {run_id}")
        return run

    def _stage_prompt(self, stage: str, topic: str, run: ResearchRun) -> str:
        """Generate the prompt for each research stage."""
        context = f"Research topic: {topic}\nOutput directory: {run.output_dir}\n"
        if run.stages_completed:
            context += f"Completed stages: {', '.join(run.stages_completed)}\n"

        stage_prompts = {
            "topic-refinement": (
                f"{context}\nRefine this research topic into a specific, novel research question. "
                "Identify the subfield, target audience, and potential contribution."
            ),
            "research-question": (
                f"{context}\nFormalize the research question. Define the scope, key variables, "
                "and what a successful answer would look like."
            ),
            "hypothesis-generation": (
                f"{context}\nGenerate 2-3 testable hypotheses based on the research question. "
                "Each hypothesis should be specific and falsifiable."
            ),
            "literature-search": (
                f"{context}\nSearch for relevant papers using web tools. "
                "Search arXiv, Semantic Scholar, and Google Scholar. "
                "Find 15-20 relevant papers. Record title, authors, year, key findings."
            ),
            "literature-synthesis": (
                f"{context}\nSynthesize the literature. Categorize papers by approach. "
                "Identify key themes, debates, and methodological trends."
            ),
            "gap-analysis": (
                f"{context}\nIdentify research gaps and opportunities. "
                "What hasn't been tried? Where are the contradictions? "
                "How does our approach differ from existing work?"
            ),
            "methodology-design": (
                f"{context}\nDesign the experimental methodology. "
                "Define variables, metrics, baselines, and evaluation criteria. "
                "Choose appropriate statistical tests."
            ),
            "variable-definition": (
                f"{context}\nFormally define all variables: independent, dependent, control. "
                "Specify measurement methods and expected ranges."
            ),
            "experiment-design": (
                f"{context}\nDesign specific experiments to test each hypothesis. "
                "Define datasets, parameter ranges, ablation studies, and baselines."
            ),
            "code-generation": (
                f"{context}\nWrite runnable Python experiment code. "
                "Use numpy, scipy, sklearn, or pytorch as needed. "
                "Save code to {run.output_dir}/experiments/. "
                "Include data generation, model training, and evaluation."
            ),
            "experiment-execution": (
                f"{context}\nExecute the experiment code. "
                "Run each experiment, collect results, handle errors. "
                "Save raw results to JSON files in {run.output_dir}/experiments/."
            ),
            "result-collection": (
                f"{context}\nCollect and organize all experiment results. "
                "Create structured JSON with all metrics, parameters, and outcomes."
            ),
            "statistical-analysis": (
                f"{context}\nPerform statistical analysis on results. "
                "Calculate significance tests, confidence intervals, effect sizes. "
                "Determine which hypotheses are supported."
            ),
            "visualization": (
                f"{context}\nCreate charts and visualizations using matplotlib. "
                "Save to {run.output_dir}/charts/. "
                "Include comparison charts, error bars, and confidence intervals."
            ),
            "abstract-writing": (
                f"{context}\nWrite the paper abstract (150-250 words). "
                "State the problem, approach, key results, and contribution."
            ),
            "introduction-writing": (
                f"{context}\nWrite the Introduction section. "
                "Motivate the problem, state contributions, outline the paper."
            ),
            "related-work-writing": (
                f"{context}\nWrite the Related Work section. "
                "Organize by theme. Cite all papers found. Position our contribution."
            ),
            "methodology-writing": (
                f"{context}\nWrite the Methodology section. "
                "Describe the approach formally. Include equations if applicable."
            ),
            "results-writing": (
                f"{context}\nWrite the Results section. "
                "Present all experimental findings with tables and figure references."
            ),
            "discussion-writing": (
                f"{context}\nWrite the Discussion section. "
                "Interpret results, discuss limitations, suggest future work."
            ),
            "conclusion-writing": (
                f"{context}\nWrite the Conclusion. Summarize contributions and key takeaways."
            ),
            "peer-review": (
                f"{context}\nConduct a self-review of the paper:\n"
                "1. Check for logical flow and clarity\n"
                "2. Verify all citations are real\n"
                "3. Check statistical claims match data\n"
                "4. Rate on: novelty, rigor, clarity, significance (1-10 each)\n"
                "5. List specific improvements needed"
            ),
            "final-revision": (
                f"{context}\nApply revisions from the peer review. "
                "Assemble the final paper draft in markdown. "
                "Save to {run.output_dir}/deliverables/paper_draft.md"
            ),
        }
        return stage_prompts.get(stage, f"{context}\nExecute stage: {stage}")

    async def _assemble_paper(self, run: ResearchRun) -> None:
        """Assemble final paper from stage outputs."""
        sections = [
            "abstract-writing", "introduction-writing", "related-work-writing",
            "methodology-writing", "results-writing", "discussion-writing",
            "conclusion-writing",
        ]
        paper = f"# {run.topic}\n\n"
        for section in sections:
            path = run.artifacts.get(section)
            if path and Path(path).exists():
                paper += Path(path).read_text() + "\n\n---\n\n"

        output = run.output_dir / "deliverables" / "paper_draft.md"
        output.write_text(paper)
        run.artifacts["final_paper"] = str(output)

    def _save_state(self, run: ResearchRun) -> None:
        state_file = run.output_dir / "run_state.json"
        state_file.write_text(json.dumps({
            "run_id": run.run_id,
            "topic": run.topic,
            "status": run.status,
            "current_stage": run.current_stage,
            "stages_completed": run.stages_completed,
            "started_at": run.started_at,
            "completed_at": run.completed_at,
        }, indent=2))
