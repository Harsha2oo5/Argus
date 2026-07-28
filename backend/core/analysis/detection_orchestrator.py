"""
Detection Orchestrator  (§109)
================================
End-to-end pipeline entry point combining all Phase 3C.2 subsystems.
This façade is the single interface callers use for full analysis; it
coordinates AnalysisEngine, RootCauseAnalyzer, BugLocalizer, CrossFileReasoner,
PatchPlanningEngine, RemediationReasoner, RegressionAnalyzer, and ReportGenerator.

Usage
-----
    from backend.core.analysis.detection_orchestrator import DetectionOrchestrator, OrchestratorResult

    orch   = DetectionOrchestrator()
    result = orch.run(code="...", extension="cpp")
    # result.enriched_findings  — List[EnrichedFinding]
    # result.json_report        — bytes
    # result.sarif_report       — bytes
    # result.markdown_report    — bytes

Execution order
---------------
    parse + rule engine          (AnalysisEngine)
         ↓
    evidence + confidence        (inside AnalysisEngine)
         ↓
    validation + suppression     (inside AnalysisEngine)
         ↓
    localization                 (BugLocalizer per finding)
         ↓
    cross-file tracing           (CrossFileReasoner per file)
         ↓
    root cause analysis          (RootCauseAnalyzer per finding)
         ↓
    patch planning               (PatchPlanningEngine per finding)
         ↓
    remediation reasoning        (RemediationReasoner per plan)
         ↓
    regression impact            (RegressionAnalyzer per remediation plan)
         ↓
    report generation            (ReportGenerator — JSON, SARIF, Markdown)
"""
import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from backend.core.analysis.engine import AnalysisEngine, EnrichedFinding
from backend.core.analysis.schemas import NormalizedFinding, AnalysisReport
from backend.core.analysis.repo_graph import RepositoryKnowledgeGraph
from backend.core.analysis.localizer import BugLocalizer, CodeSpan
from backend.core.analysis.cross_file import CrossFileReasoner
from backend.core.analysis.root_cause import RootCauseAnalyzer, RootCauseChain
from backend.core.analysis.patch import PatchPlanningEngine, PatchPlan
from backend.core.analysis.remediation import RemediationReasoner, RemediationPlan
from backend.core.analysis.regression import RegressionAnalyzer, RegressionImpactReport
from backend.core.analysis.report import ReportGenerator, ReportFormat, EnrichedReport
from backend.core.ai.memory.semantic import SemanticMemory

logger = logging.getLogger("backend.analysis.detection_orchestrator")


# ---------------------------------------------------------------------------
# Per-finding full analysis record
# ---------------------------------------------------------------------------

@dataclass
class FindingAnalysis:
    """All Phase 3C.2 artefacts for a single finding."""
    enriched:    EnrichedFinding
    spans:       List[CodeSpan]
    root_cause:  RootCauseChain
    patch_plan:  PatchPlan
    remediation: RemediationPlan
    regression:  RegressionImpactReport


# ---------------------------------------------------------------------------
# Orchestrator result
# ---------------------------------------------------------------------------

@dataclass
class OrchestratorResult:
    """Complete output of DetectionOrchestrator.run()."""
    enriched_findings:  List[EnrichedFinding]
    finding_analyses:   List[FindingAnalysis]
    json_report:        bytes
    sarif_report:       bytes
    markdown_report:    bytes
    html_report:        bytes
    duration_seconds:   float
    suppressed_count:   int = 0


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

class DetectionOrchestrator:
    """
    Full Phase 3C.2 detection pipeline façade.

    Parameters
    ----------
    semantic_memory     : Shared SemanticMemory (propagated to all subsystems).
    repo_graph          : Pre-populated RepositoryKnowledgeGraph, or None for a
                          fresh empty graph (sufficient for single-file analysis).
    min_confidence      : Minimum confidence threshold (default 0.30).
    max_traversal_depth : CrossFile / MultiHop traversal depth cap (default 5).
    """

    def __init__(
        self,
        semantic_memory:      Optional[SemanticMemory]           = None,
        repo_graph:           Optional[RepositoryKnowledgeGraph] = None,
        min_confidence:       float = 0.30,
        max_traversal_depth:  int   = 5,
    ):
        mem = semantic_memory or SemanticMemory()
        self._graph      = repo_graph or RepositoryKnowledgeGraph()
        self._engine     = AnalysisEngine(semantic_memory=mem, min_confidence=min_confidence)
        self._localizer  = BugLocalizer()
        self._cross_file = CrossFileReasoner(max_depth=max_traversal_depth)
        self._root_cause = RootCauseAnalyzer()
        self._patcher    = PatchPlanningEngine()
        self._remediator = RemediationReasoner(semantic_memory=mem)
        self._regression = RegressionAnalyzer()
        self._reporter   = ReportGenerator()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(
        self,
        code:      str,
        extension: str = "cpp",
        file_path: Optional[str] = None,
    ) -> OrchestratorResult:
        """
        Execute the full Phase 3C.2 pipeline and return an OrchestratorResult.

        Parameters
        ----------
        code      : Source code string to analyse.
        extension : File extension used for parser and rule resolution.
        file_path : Optional file path used for cross-file reasoning seed.
        """
        t0 = time.perf_counter()
        logger.info("DetectionOrchestrator.run() started (extension=%s).", extension)

        # ── 1. Static + Phase 3C.2 core pipeline ──────────────────────
        enriched_findings = self._engine.analyze(code, extension)
        suppressed_count  = len(self._engine._suppression_p.audit_log)

        # ── 2. Per-finding deep analysis ───────────────────────────────
        analyses: List[FindingAnalysis] = []

        for ef in enriched_findings:
            fa = self._analyse_finding(ef)
            analyses.append(fa)

        # ── 3. Build plain NormalizedFinding list for AnalysisReport ──
        plain_findings = [ef.finding for ef in enriched_findings]
        analysis_report = AnalysisReport(
            static_findings=plain_findings,
            total_issues=len(plain_findings),
            llm_available=False,   # synchronous path; LLM agents run separately
        )

        # ── 4. Build explanation markdown map ─────────────────────────
        explanation_md: Dict[str, str] = {}
        for ef in enriched_findings:
            if ef.explanation:
                explanation_md[ef.finding.rule_id] = ef.explanation.markdown

        # ── 5. Generate reports ────────────────────────────────────────
        enriched_report = EnrichedReport(
            report=analysis_report,
            explanation_markdowns=explanation_md,
            root_cause_summaries={
                fa.enriched.finding.rule_id: (
                    fa.root_cause.primary.hypothesis
                    if fa.root_cause.primary else "N/A"
                )
                for fa in analyses
            },
            regression_summaries={
                fa.enriched.finding.rule_id: (
                    f"api={fa.regression.api_compat_verdict}, "
                    f"affected={len(fa.regression.affected_components)}"
                )
                for fa in analyses
            },
        )

        json_bytes     = self._reporter.generate(enriched_report, ReportFormat.JSON)
        sarif_bytes    = self._reporter.generate(enriched_report, ReportFormat.SARIF)
        markdown_bytes = self._reporter.generate(enriched_report, ReportFormat.MARKDOWN)
        html_bytes     = self._reporter.generate(enriched_report, ReportFormat.HTML)

        duration = time.perf_counter() - t0
        logger.info(
            "DetectionOrchestrator complete: %d findings, %d suppressed, %.3fs.",
            len(enriched_findings), suppressed_count, duration,
        )

        return OrchestratorResult(
            enriched_findings=enriched_findings,
            finding_analyses=analyses,
            json_report=json_bytes,
            sarif_report=sarif_bytes,
            markdown_report=markdown_bytes,
            html_report=html_bytes,
            duration_seconds=round(duration, 4),
            suppressed_count=suppressed_count,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _analyse_finding(self, ef: EnrichedFinding) -> FindingAnalysis:
        """Run per-finding deep analysis: localize → root cause → patch → remediate → regression."""
        f = ef.finding

        # Localization
        spans = self._localizer.locate(f, self._graph)

        # Root cause
        rc = self._root_cause.analyze(f, self._graph)

        # Patch plan
        pp = self._patcher.plan(f, rc, self._graph, spans)

        # Remediation
        rp = self._remediator.evaluate(pp)

        # Regression
        reg = self._regression.analyze(rp, self._graph)

        logger.debug(
            "FindingAnalysis for '%s': spans=%d rc_primary='%s' patch_strategies=%d reg_affected=%d",
            f.rule_id, len(spans),
            rc.primary.hypothesis[:60] if rc.primary else "none",
            len(pp.strategies),
            len(reg.affected_components),
        )
        return FindingAnalysis(
            enriched=ef, spans=spans, root_cause=rc,
            patch_plan=pp, remediation=rp, regression=reg,
        )
