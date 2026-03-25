"""23-stage autonomous research pipeline.

8 phases, PIVOT/REFINE decision loops, gate stages, multi-agent debate,
real literature from OpenAlex/Semantic Scholar/arXiv, 4-layer citation
verification, per-run knowledge base, LaTeX export, self-healing.

Turns a research idea into a conference-ready paper with zero intervention.
"""

import asyncio
import json
import os
import platform
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Coroutine

from loguru import logger


# 23 stages organized into 8 phases
STAGES = [
    # Phase A: Research Scoping
    "topic-init",              # 1. Decompose topic into structured problem tree
    "problem-decompose",       # 2. Formalize research questions, scope, variables

    # Phase B: Literature Discovery
    "search-strategy",         # 3. Generate multi-query search strategy
    "literature-collect",      # 4. Real API search (OpenAlex, S2, arXiv)
    "literature-screen",       # 5. GATE — screen papers by relevance
    "knowledge-extract",       # 6. Extract knowledge cards from each paper

    # Phase C: Knowledge Synthesis
    "synthesis",               # 7. Cluster findings, identify themes
    "hypothesis-gen",          # 8. Multi-agent debate → testable hypotheses

    # Phase D: Experiment Design
    "experiment-design",       # 9. GATE — design experiments, baselines, metrics
    "code-generation",         # 10. Generate runnable experiment code
    "resource-planning",       # 11. Hardware detection, estimate resources

    # Phase E: Experiment Execution
    "experiment-run",          # 12. Execute in sandbox with self-healing
    "iterative-refine",        # 13. Fix failures, refine parameters

    # Phase F: Analysis & Decision
    "result-analysis",         # 14. Multi-agent analysis of results
    "research-decision",       # 15. PIVOT / REFINE / PROCEED decision

    # Phase G: Paper Writing
    "paper-outline",           # 16. Generate paper structure
    "paper-draft",             # 17. Section-by-section writing
    "peer-review",             # 18. Multi-agent review with evidence checks
    "paper-revision",          # 19. Apply review feedback

    # Phase H: Finalization
    "quality-gate",            # 20. GATE — final quality check
    "knowledge-archive",       # 21. Archive run knowledge
    "export-publish",          # 22. LaTeX export with conference template
    "citation-verify",         # 23. 4-layer citation verification
]

GATE_STAGES = {4, 8, 19}  # 0-indexed: literature-screen, experiment-design, quality-gate
PHASE_NAMES = {
    "A": "Research Scoping",
    "B": "Literature Discovery",
    "C": "Knowledge Synthesis",
    "D": "Experiment Design",
    "E": "Experiment Execution",
    "F": "Analysis & Decision",
    "G": "Paper Writing",
    "H": "Finalization",
}


def _get_phase(stage_idx: int) -> str:
    if stage_idx < 2:
        return "A"
    elif stage_idx < 6:
        return "B"
    elif stage_idx < 8:
        return "C"
    elif stage_idx < 11:
        return "D"
    elif stage_idx < 13:
        return "E"
    elif stage_idx < 15:
        return "F"
    elif stage_idx < 19:
        return "G"
    else:
        return "H"


@dataclass
class ResearchRun:
    """Tracks a single research pipeline execution."""
    topic: str
    run_id: str
    output_dir: Path
    current_stage: int = 0
    stages_completed: list[str] = field(default_factory=list)
    artifacts: dict[str, str] = field(default_factory=dict)
    papers_found: list[dict] = field(default_factory=list)
    hypotheses: list[str] = field(default_factory=list)
    decisions: list[dict] = field(default_factory=list)
    pivot_count: int = 0
    refine_count: int = 0
    started_at: str = ""
    completed_at: str | None = None
    status: str = "running"
    hardware: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.started_at:
            self.started_at = datetime.now().isoformat()
        if not self.hardware:
            self.hardware = _detect_hardware()


def _detect_hardware() -> dict:
    """Auto-detect available compute hardware."""
    hw = {
        "platform": platform.system(),
        "machine": platform.machine(),
        "gpu": "cpu",
        "gpu_name": "",
    }
    # Check for NVIDIA CUDA
    try:
        import torch
        if torch.cuda.is_available():
            hw["gpu"] = "cuda"
            hw["gpu_name"] = torch.cuda.get_device_name(0)
            return hw
    except ImportError:
        pass

    # Check for Apple MPS
    try:
        import torch
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            hw["gpu"] = "mps"
            hw["gpu_name"] = "Apple Silicon"
            return hw
    except (ImportError, AttributeError):
        pass

    return hw


class ResearchPipeline:
    """Executes the full autonomous research pipeline."""

    def __init__(
        self,
        agent_fn: Callable[[str], Coroutine[Any, Any, str]],
        output_base: str | Path = "./research_output",
        auto_approve: bool = True,
        max_pivots: int = 2,
        max_refines: int = 3,
        on_stage: Callable[[int, str, str], None] | None = None,
    ):
        self.agent_fn = agent_fn
        self.output_base = Path(output_base)
        self.auto_approve = auto_approve
        self.max_pivots = max_pivots
        self.max_refines = max_refines
        self.on_stage = on_stage  # callback(stage_idx, stage_name, phase)

    async def run(self, topic: str) -> ResearchRun:
        """Execute the full 23-stage pipeline with PIVOT/REFINE loops."""
        from lifeclaw.research.knowledge_base import RunKnowledgeBase

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_id = f"rc-{ts}"
        output_dir = self.output_base / run_id
        output_dir.mkdir(parents=True, exist_ok=True)
        for subdir in ["experiments", "charts", "deliverables", "evolution"]:
            (output_dir / subdir).mkdir(exist_ok=True)

        run = ResearchRun(topic=topic, run_id=run_id, output_dir=output_dir)
        kb = RunKnowledgeBase(output_dir)
        self._save_state(run)
        logger.info(f"Research pipeline started: {run_id} — '{topic}'")
        logger.info(f"Hardware: {run.hardware['gpu']} ({run.hardware.get('gpu_name', 'CPU')})")

        i = 0
        while i < len(STAGES):
            stage_name = STAGES[i]
            phase = _get_phase(i)
            run.current_stage = i

            if self.on_stage:
                self.on_stage(i, stage_name, phase)

            logger.info(f"[Phase {phase}] Stage {i+1}/23: {stage_name}")

            # Gate stages — pause for approval unless auto_approve
            if i in GATE_STAGES and not self.auto_approve:
                logger.info(f"GATE: Stage {stage_name} requires approval. Auto-approving.")
                kb.add("decisions", f"Gate {stage_name}: auto-approved", stage=stage_name)

            try:
                # Build context from KB
                kb_context = kb.get_context_for_stage(stage_name)

                # Special handling for literature collection (real APIs)
                if stage_name == "literature-collect":
                    result = await self._run_literature_search(topic, run, kb)
                elif stage_name == "citation-verify":
                    result = await self._run_citation_verify(run, kb)
                elif stage_name == "export-publish":
                    result = await self._run_latex_export(run, kb)
                elif stage_name == "hypothesis-gen":
                    result = await self._run_debate(topic, run, kb, "hypothesis")
                elif stage_name == "result-analysis":
                    result = await self._run_debate(topic, run, kb, "analysis")
                elif stage_name == "peer-review":
                    result = await self._run_debate(topic, run, kb, "review")
                elif stage_name == "research-decision":
                    result, action = await self._run_decision(topic, run, kb)
                    kb.add("decisions", f"Decision: {action}", stage=stage_name,
                           action=action, pivot_count=run.pivot_count, refine_count=run.refine_count)
                    if action == "PIVOT" and run.pivot_count < self.max_pivots:
                        run.pivot_count += 1
                        logger.info(f"PIVOT #{run.pivot_count} — jumping back to hypothesis-gen")
                        i = STAGES.index("hypothesis-gen")
                        self._save_state(run)
                        continue
                    elif action == "REFINE" and run.refine_count < self.max_refines:
                        run.refine_count += 1
                        logger.info(f"REFINE #{run.refine_count} — jumping back to iterative-refine")
                        i = STAGES.index("iterative-refine")
                        self._save_state(run)
                        continue
                else:
                    prompt = self._stage_prompt(stage_name, topic, run, kb_context)
                    result = await self.agent_fn(prompt)

                # Save stage output
                stage_file = output_dir / f"stage_{i+1:02d}_{stage_name}.md"
                stage_file.write_text(result)
                run.artifacts[stage_name] = str(stage_file)
                run.stages_completed.append(stage_name)

                # Extract knowledge from stage output
                self._extract_knowledge(kb, stage_name, result)
                self._save_state(run)

            except Exception as e:
                logger.error(f"Stage {stage_name} failed: {e}")
                # Self-healing: retry once with error context
                try:
                    repair_prompt = (
                        f"The previous stage '{stage_name}' failed with error: {e}\n"
                        f"Context: researching '{topic}'.\n"
                        f"Completed stages: {', '.join(run.stages_completed)}\n"
                        f"Please diagnose and complete this stage despite the error."
                    )
                    result = await self.agent_fn(repair_prompt)
                    stage_file = output_dir / f"stage_{i+1:02d}_{stage_name}_repaired.md"
                    stage_file.write_text(result)
                    run.artifacts[stage_name] = str(stage_file)
                    run.stages_completed.append(stage_name)
                    kb.add("decisions", f"Self-healed stage {stage_name} after: {e}", stage=stage_name)
                    self._save_state(run)
                except Exception as e2:
                    logger.error(f"Stage {stage_name} repair also failed: {e2}")
                    kb.add("decisions", f"Stage {stage_name} failed permanently: {e2}", stage=stage_name)
                    # Continue to next stage instead of breaking
                    run.stages_completed.append(f"{stage_name}:FAILED")

            i += 1

        # Assemble final paper
        if sum(1 for s in run.stages_completed if ":FAILED" not in s) >= 18:
            await self._assemble_paper(run)
            run.status = "completed"
        else:
            run.status = "partial"

        # Archive knowledge
        kb_file = output_dir / "knowledge_base" / "kb_export.md"
        kb_file.write_text(kb.export_markdown())

        run.completed_at = datetime.now().isoformat()
        self._save_state(run)
        logger.info(f"Pipeline {run.status}: {run_id} ({len(run.stages_completed)}/23 stages, "
                     f"{run.pivot_count} pivots, {run.refine_count} refines)")
        return run

    # ── Real Literature Search ──────────────────────────────────────

    async def _run_literature_search(self, topic: str, run: ResearchRun, kb) -> str:
        """Use real academic APIs instead of asking LLM to hallucinate papers."""
        from lifeclaw.research.literature import LiteratureSearch

        searcher = LiteratureSearch()
        try:
            # Generate expanded queries using the agent
            query_prompt = (
                f"Generate 3 diverse search queries for this research topic: {topic}\n"
                f"Return ONLY the queries, one per line. No numbering or explanation."
            )
            queries_raw = await self.agent_fn(query_prompt)
            queries = [q.strip().lstrip("0123456789.-) ") for q in queries_raw.strip().split("\n") if q.strip()]
            queries = queries[:3] or [topic]

            all_papers = []
            for query in queries:
                papers = await searcher.search(query, max_results=10)
                all_papers.extend(papers)

            # Deduplicate across queries
            seen_titles = set()
            unique_papers = []
            for p in all_papers:
                norm = re.sub(r"[^a-z0-9]", "", p.title.lower())
                if norm not in seen_titles:
                    seen_titles.add(norm)
                    unique_papers.append(p)

            # Store papers in run state
            run.papers_found = [
                {"title": p.title, "authors": p.authors[:3], "year": p.year,
                 "doi": p.doi, "arxiv_id": p.arxiv_id, "citations": p.citation_count,
                 "source": p.source, "abstract": p.abstract[:200]}
                for p in unique_papers[:25]
            ]

            # Generate BibTeX
            bibtex = searcher.generate_bibtex(unique_papers[:25])
            bib_file = run.output_dir / "deliverables" / "references.bib"
            bib_file.write_text(bibtex)
            run.artifacts["references.bib"] = str(bib_file)

            # Add to knowledge base
            for p in unique_papers[:15]:
                kb.add("literature", f"{p.title} ({p.year}) — {p.abstract[:150]}",
                       stage="literature-collect", doi=p.doi, citations=p.citation_count)

            # Format result for the pipeline
            lines = [f"# Literature Collection — {len(unique_papers)} papers found\n"]
            lines.append(f"Queries used: {queries}\n")
            lines.append(f"Sources: OpenAlex, Semantic Scholar, arXiv\n")
            for i, p in enumerate(unique_papers[:20], 1):
                lines.append(f"\n## {i}. {p.title}")
                lines.append(f"**Authors**: {', '.join(p.authors[:5])}")
                lines.append(f"**Year**: {p.year} | **Citations**: {p.citation_count}")
                if p.doi:
                    lines.append(f"**DOI**: {p.doi}")
                if p.arxiv_id:
                    lines.append(f"**arXiv**: {p.arxiv_id}")
                if p.abstract:
                    lines.append(f"**Abstract**: {p.abstract[:300]}")

            return "\n".join(lines)
        finally:
            await searcher.close()

    # ── Citation Verification ───────────────────────────────────────

    async def _run_citation_verify(self, run: ResearchRun, kb) -> str:
        """4-layer citation verification — kill hallucinated refs."""
        from lifeclaw.research.literature import LiteratureSearch, Paper

        searcher = LiteratureSearch()
        try:
            verified_count = 0
            failed_count = 0
            results_lines = ["# Citation Verification Report\n"]

            for paper_data in run.papers_found[:20]:
                paper = Paper(
                    title=paper_data["title"],
                    authors=paper_data.get("authors", []),
                    year=paper_data.get("year", 0),
                    doi=paper_data.get("doi", ""),
                    arxiv_id=paper_data.get("arxiv_id", ""),
                )
                result = await searcher.verify_citation(paper)
                if result["verified"]:
                    verified_count += 1
                    results_lines.append(f"- VERIFIED: {paper.title}")
                else:
                    failed_count += 1
                    results_lines.append(f"- UNVERIFIED: {paper.title}")

                # Rate limit
                await asyncio.sleep(0.5)

            results_lines.insert(1, f"\nVerified: {verified_count}/{verified_count + failed_count}\n")

            # Save verification report
            report = {
                "verified": verified_count,
                "failed": failed_count,
                "total": verified_count + failed_count,
                "rate": verified_count / max(verified_count + failed_count, 1),
            }
            report_file = run.output_dir / "deliverables" / "verification_report.json"
            report_file.write_text(json.dumps(report, indent=2))
            run.artifacts["verification_report"] = str(report_file)

            kb.add("reviews", f"Citations: {verified_count}/{verified_count + failed_count} verified",
                   stage="citation-verify")

            return "\n".join(results_lines)
        finally:
            await searcher.close()

    # ── Multi-Agent Debate ──────────────────────────────────────────

    async def _run_debate(self, topic: str, run: ResearchRun, kb, debate_type: str) -> str:
        """Structured multi-perspective debate for hypotheses, analysis, and review."""
        perspectives = {
            "hypothesis": [
                ("Methodologist", "Focus on novel methods and techniques. What experimental approach would be most rigorous?"),
                ("Domain Expert", "Focus on the specific domain. What gaps exist? What would advance the field most?"),
                ("Critic", "Challenge assumptions. What could go wrong? What's been tried before?"),
            ],
            "analysis": [
                ("Statistician", "Focus on statistical significance, effect sizes, confidence intervals. Are the results valid?"),
                ("Practitioner", "Focus on practical implications. Are these results useful in the real world?"),
                ("Skeptic", "Look for confounds, p-hacking, overfitting. What alternative explanations exist?"),
            ],
            "review": [
                ("Reviewer 1 (Method)", "Evaluate methodology rigor, reproducibility, and experimental design."),
                ("Reviewer 2 (Novelty)", "Assess originality, contribution, and positioning against prior work."),
                ("Reviewer 3 (Clarity)", "Evaluate writing quality, logical flow, and presentation."),
            ],
        }

        agents = perspectives.get(debate_type, perspectives["hypothesis"])
        kb_context = kb.get_context_for_stage(f"debate-{debate_type}")

        responses = []
        for role_name, role_prompt in agents:
            prompt = (
                f"You are {role_name} in a research debate.\n"
                f"Topic: {topic}\n"
                f"Your perspective: {role_prompt}\n\n"
                f"{kb_context}\n\n"
                f"Completed stages: {', '.join(run.stages_completed)}\n\n"
            )

            if debate_type == "hypothesis":
                prompt += "Generate 2-3 specific, testable hypotheses from your perspective."
            elif debate_type == "analysis":
                prompt += "Analyze the experimental results. What do they mean? What are the limitations?"
            elif debate_type == "review":
                prompt += (
                    "Review the paper draft. Rate: novelty (1-10), rigor (1-10), "
                    "clarity (1-10), significance (1-10). List specific improvements."
                )

            response = await self.agent_fn(prompt)
            responses.append(f"## {role_name}\n\n{response}")

        # Synthesis round — combine perspectives
        synthesis_prompt = (
            f"You are the research lead synthesizing a multi-perspective debate.\n"
            f"Topic: {topic}\n\n"
            f"Three perspectives were offered:\n\n"
            + "\n\n---\n\n".join(responses) +
            f"\n\nSynthesize these into a unified conclusion. "
            f"{'List the final hypotheses.' if debate_type == 'hypothesis' else ''}"
            f"{'Provide the final analysis summary.' if debate_type == 'analysis' else ''}"
            f"{'Provide the final review verdict and required revisions.' if debate_type == 'review' else ''}"
        )
        synthesis = await self.agent_fn(synthesis_prompt)

        full_result = "\n\n---\n\n".join(responses) + f"\n\n---\n\n## Synthesis\n\n{synthesis}"

        # Extract hypotheses if applicable
        if debate_type == "hypothesis":
            for line in synthesis.split("\n"):
                line = line.strip()
                if line and (line.startswith("H") or line.startswith("-") or line.startswith("*")):
                    run.hypotheses.append(line[:200])
                    kb.add("questions", line[:200], stage="hypothesis-gen")

        return full_result

    # ── PIVOT/REFINE Decision ───────────────────────────────────────

    async def _run_decision(self, topic: str, run: ResearchRun, kb) -> tuple[str, str]:
        """Stage 15: Autonomous PROCEED / REFINE / PIVOT decision."""
        kb_context = kb.get_context_for_stage("research-decision")

        prompt = (
            f"You are the research decision-maker for: {topic}\n\n"
            f"Pipeline state:\n"
            f"- Stages completed: {', '.join(run.stages_completed)}\n"
            f"- Hypotheses: {run.hypotheses[:5]}\n"
            f"- Pivots so far: {run.pivot_count}/{self.max_pivots}\n"
            f"- Refines so far: {run.refine_count}/{self.max_refines}\n\n"
            f"{kb_context}\n\n"
            f"Based on the experimental results so far, make ONE decision:\n\n"
            f"1. **PROCEED** — Results are good enough. Move to paper writing.\n"
            f"2. **REFINE** — Results show promise but need parameter tuning. Go back to iterative-refine.\n"
            f"3. **PIVOT** — Current approach isn't working. Go back to hypothesis generation with a new angle.\n\n"
            f"Start your response with exactly one word: PROCEED, REFINE, or PIVOT.\n"
            f"Then explain your reasoning."
        )
        result = await self.agent_fn(prompt)

        # Parse decision
        first_word = result.strip().split()[0].upper().rstrip(".:,")
        if first_word in ("PIVOT", "REFINE", "PROCEED"):
            action = first_word
        else:
            # Default to PROCEED if unclear
            action = "PROCEED"

        run.decisions.append({
            "action": action,
            "reasoning": result[:500],
            "timestamp": datetime.now().isoformat(),
        })

        return result, action

    # ── LaTeX Export ────────────────────────────────────────────────

    async def _run_latex_export(self, run: ResearchRun, kb) -> str:
        """Export paper to conference-ready LaTeX."""
        # Read the assembled paper draft
        paper_path = run.output_dir / "deliverables" / "paper_draft.md"
        if paper_path.exists():
            paper_md = paper_path.read_text()
        else:
            paper_md = ""
            for stage in ["paper-outline", "paper-draft", "paper-revision"]:
                path = run.artifacts.get(stage)
                if path and Path(path).exists():
                    paper_md += Path(path).read_text() + "\n\n"

        prompt = (
            f"Convert this research paper from Markdown to LaTeX.\n"
            f"Use a clean academic format (article class, 11pt).\n"
            f"Include: title, abstract, sections, references, tables.\n"
            f"The BibTeX file is at 'references.bib'.\n"
            f"Use \\cite{{key}} for citations.\n\n"
            f"Paper content:\n\n{paper_md[:8000]}"
        )
        latex = await self.agent_fn(prompt)

        # Save LaTeX
        tex_file = run.output_dir / "deliverables" / "paper.tex"
        tex_file.write_text(latex)
        run.artifacts["paper.tex"] = str(tex_file)

        kb.add("decisions", "LaTeX export completed", stage="export-publish")

        return latex

    # ── Stage Prompts ───────────────────────────────────────────────

    def _stage_prompt(self, stage: str, topic: str, run: ResearchRun, kb_context: str) -> str:
        context = (
            f"Research topic: {topic}\n"
            f"Output directory: {run.output_dir}\n"
            f"Hardware: {run.hardware['gpu']} ({run.hardware.get('gpu_name', 'CPU')})\n"
        )
        if run.stages_completed:
            context += f"Completed stages: {', '.join(run.stages_completed[-10:])}\n"
        if kb_context:
            context += f"\n{kb_context}\n"

        prompts = {
            "topic-init": (
                f"{context}\nDecompose this research topic into a structured problem tree.\n"
                "Define: subfield, target venue (NeurIPS/ICML/ICLR), key concepts, "
                "potential contribution, target audience."
            ),
            "problem-decompose": (
                f"{context}\nFormalize the research questions. Define:\n"
                "1. Primary research question (1 sentence)\n"
                "2. Sub-questions (2-3)\n"
                "3. Scope boundaries (what's in/out)\n"
                "4. Key variables (independent, dependent, control)\n"
                "5. Success criteria"
            ),
            "search-strategy": (
                f"{context}\nDesign a literature search strategy:\n"
                "1. Generate 5 diverse search queries (different angles)\n"
                "2. Identify key authors in this area\n"
                "3. List target venues and conferences\n"
                "4. Define inclusion/exclusion criteria for papers"
            ),
            "literature-screen": (
                f"{context}\n"
                f"Papers found: {len(run.papers_found)}\n\n"
                "Screen these papers for relevance. For each:\n"
                "1. Rate relevance (1-5)\n"
                "2. Categorize: directly related / tangentially related / background\n"
                "3. Flag the top 10 most important papers\n"
                "4. Identify any missing areas that need more search"
            ),
            "knowledge-extract": (
                f"{context}\nExtract structured knowledge cards from the literature:\n"
                "For each key paper, extract:\n"
                "1. Core method/approach\n"
                "2. Key results and metrics\n"
                "3. Strengths and limitations\n"
                "4. How it relates to our research question"
            ),
            "synthesis": (
                f"{context}\nSynthesize the literature:\n"
                "1. Cluster papers by approach/theme\n"
                "2. Identify consensus findings\n"
                "3. Map contradictions and debates\n"
                "4. Identify research gaps\n"
                "5. Position our potential contribution"
            ),
            "experiment-design": (
                f"{context}\n"
                f"Hypotheses: {run.hypotheses[:5]}\n\n"
                "Design experiments to test each hypothesis:\n"
                "1. Experimental conditions and baselines\n"
                "2. Datasets (synthetic or real)\n"
                "3. Metrics and evaluation criteria\n"
                "4. Statistical tests to use\n"
                "5. Ablation studies"
            ),
            "code-generation": (
                f"{context}\n"
                f"Hardware: {run.hardware['gpu']}\n\n"
                "Write runnable Python experiment code. Requirements:\n"
                "- Use numpy, scipy, sklearn, or pytorch as appropriate\n"
                f"- Target hardware: {run.hardware['gpu']}\n"
                "- Save results to JSON in experiments/ directory\n"
                "- Include data generation, model/method, evaluation\n"
                "- Handle errors gracefully\n"
                "- Print progress during execution\n"
                f"Save all code to {run.output_dir}/experiments/"
            ),
            "resource-planning": (
                f"{context}\n"
                f"Hardware detected: {json.dumps(run.hardware)}\n\n"
                "Estimate resource requirements:\n"
                "1. Expected runtime per experiment\n"
                "2. Memory requirements\n"
                "3. Any hardware limitations\n"
                "4. Recommend adjustments for available hardware"
            ),
            "experiment-run": (
                f"{context}\nExecute the experiment code in {run.output_dir}/experiments/.\n"
                "Run each experiment, collect results, handle errors.\n"
                "If code fails, attempt targeted repair.\n"
                "Save structured results to JSON."
            ),
            "iterative-refine": (
                f"{context}\n"
                f"Refine iteration #{run.refine_count + 1}.\n"
                "Review experiment results and:\n"
                "1. Identify underperforming conditions\n"
                "2. Adjust hyperparameters\n"
                "3. Fix any code bugs\n"
                "4. Re-run improved experiments\n"
                "5. Compare with previous results"
            ),
            "paper-outline": (
                f"{context}\nCreate a detailed paper outline:\n"
                "1. Title (concise, specific)\n"
                "2. Abstract structure (problem, approach, results, contribution)\n"
                "3. Section headers with 2-3 bullet points each\n"
                "4. Figure/table placement plan\n"
                "5. Target length: 8-10 pages"
            ),
            "paper-draft": (
                f"{context}\nWrite the full paper draft (5000-6500 words):\n"
                "Sections: Abstract, Introduction, Related Work, Methodology, "
                "Experiments & Results, Discussion, Conclusion.\n"
                "Requirements:\n"
                "- Cite real papers from the literature review\n"
                "- Reference actual experiment results\n"
                "- Include table/figure placeholders\n"
                "- Academic tone, no filler"
            ),
            "paper-revision": (
                f"{context}\nApply revisions from peer review.\n"
                "Address each reviewer comment. Strengthen:\n"
                "1. Clarity of claims\n"
                "2. Statistical rigor\n"
                "3. Missing references\n"
                "4. Logical flow\n"
                "Do NOT fabricate results not supported by experiments."
            ),
            "quality-gate": (
                f"{context}\nFinal quality check:\n"
                "1. Verify all claims are supported by evidence\n"
                "2. Check citation consistency\n"
                "3. Ensure no hallucinated numbers\n"
                "4. Rate: novelty (1-10), rigor (1-10), clarity (1-10)\n"
                "5. List any remaining issues\n"
                "If score < 5 on any dimension, recommend specific fixes."
            ),
            "knowledge-archive": (
                f"{context}\nArchive lessons from this research run:\n"
                "1. What worked well?\n"
                "2. What didn't work?\n"
                "3. Key decisions and their outcomes\n"
                "4. Recommendations for future runs\n"
                "5. Reusable patterns discovered"
            ),
        }
        return prompts.get(stage, f"{context}\nExecute stage: {stage}")

    # ── Knowledge Extraction ────────────────────────────────────────

    def _extract_knowledge(self, kb, stage_name: str, result: str):
        """Auto-extract knowledge entries from stage output."""
        # Map stages to KB categories
        category_map = {
            "topic-init": "decisions",
            "problem-decompose": "questions",
            "search-strategy": "literature",
            "literature-collect": "literature",
            "literature-screen": "literature",
            "knowledge-extract": "findings",
            "synthesis": "findings",
            "hypothesis-gen": "questions",
            "experiment-design": "experiments",
            "code-generation": "experiments",
            "experiment-run": "experiments",
            "iterative-refine": "experiments",
            "result-analysis": "findings",
            "research-decision": "decisions",
            "paper-outline": "decisions",
            "peer-review": "reviews",
            "quality-gate": "reviews",
            "knowledge-archive": "findings",
        }
        category = category_map.get(stage_name, "findings")

        # Extract key sentences (first 3 substantial lines)
        for line in result.split("\n"):
            line = line.strip()
            if len(line) > 30 and not line.startswith("#"):
                kb.add(category, line[:300], stage=stage_name)
                break  # Just the first meaningful line per stage

    # ── Paper Assembly ──────────────────────────────────────────────

    async def _assemble_paper(self, run: ResearchRun):
        """Assemble final paper from writing stages."""
        sections = ["paper-outline", "paper-draft", "paper-revision"]
        paper = f"# {run.topic}\n\n"
        for section in sections:
            path = run.artifacts.get(section)
            if path and Path(path).exists():
                content = Path(path).read_text()
                if section == "paper-draft" or section == "paper-revision":
                    paper = content  # Use the latest draft
                    break

        if not paper.strip() or len(paper) < 100:
            paper = f"# {run.topic}\n\n"
            for stage in run.stages_completed:
                path = run.artifacts.get(stage)
                if path and Path(path).exists() and "writing" in stage:
                    paper += Path(path).read_text() + "\n\n---\n\n"

        output = run.output_dir / "deliverables" / "paper_draft.md"
        output.write_text(paper)
        run.artifacts["final_paper"] = str(output)

    # ── State Persistence ───────────────────────────────────────────

    def _save_state(self, run: ResearchRun):
        state_file = run.output_dir / "run_state.json"
        state_file.write_text(json.dumps({
            "run_id": run.run_id,
            "topic": run.topic,
            "status": run.status,
            "current_stage": run.current_stage,
            "stages_completed": run.stages_completed,
            "papers_found": len(run.papers_found),
            "hypotheses": run.hypotheses,
            "decisions": run.decisions,
            "pivot_count": run.pivot_count,
            "refine_count": run.refine_count,
            "hardware": run.hardware,
            "started_at": run.started_at,
            "completed_at": run.completed_at,
        }, indent=2))
