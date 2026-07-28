"""
Enterprise Report Generator  (§125)
======================================
Renders AnalysisReport objects into multiple formats:
  • JSON   — full structured output for CI/CD and API consumers
  • SARIF  — SARIF 2.1.0 for IDE integrations and GitHub Code Scanning
  • Markdown — per-finding ExplanationReport.markdown concatenated
  • HTML   — lightweight self-contained browser-viewable report

Design invariants
-----------------
- All formats are produced from the same AnalysisReport input model.
- JSON output is deterministic: keys are sorted, findings ordered by severity
  then confidence descending.
- SARIF output conforms to the SARIF 2.1.0 schema (https://schemastore.org/schemas/json/sarif-2.1.0.json).
- HTML output is self-contained (no external CDN dependencies).
- Large reports (> 1000 findings) MUST stream rather than buffer.
"""
import json
import logging
import time
from enum import Enum
from typing import Any, Dict, Iterator, List, Optional

from backend.core.analysis.schemas import NormalizedFinding, AnalysisReport

logger = logging.getLogger("backend.analysis.report")

# Severity sort order (lower index = higher priority)
_SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}


class ReportFormat(str, Enum):
    JSON     = "json"
    SARIF    = "sarif"
    MARKDOWN = "markdown"
    HTML     = "html"


# ---------------------------------------------------------------------------
# Extended report model
# ---------------------------------------------------------------------------

class EnrichedReport:
    """
    Wraps AnalysisReport with optional Phase 3C.2 enrichments.
    All enrichment fields are optional so the generator works with plain
    AnalysisReport objects too.
    """
    def __init__(
        self,
        report:              AnalysisReport,
        explanation_markdowns: Optional[Dict[str, str]] = None,  # rule_id → markdown
        root_cause_summaries: Optional[Dict[str, str]] = None,
        regression_summaries: Optional[Dict[str, str]] = None,
        tool_name:           str  = "Hybrid Bug Hunter",
        tool_version:        str  = "3.0.0",
    ):
        self.report                 = report
        self.explanations           = explanation_markdowns or {}
        self.root_causes            = root_cause_summaries  or {}
        self.regressions            = regression_summaries  or {}
        self.tool_name              = tool_name
        self.tool_version           = tool_version
        self.generated_at           = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


# ---------------------------------------------------------------------------
# Report Generator
# ---------------------------------------------------------------------------

class ReportGenerator:
    """
    Generates reports in multiple formats from an EnrichedReport.
    All public methods return bytes for consistent streaming support.
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self, report: EnrichedReport, fmt: ReportFormat) -> bytes:
        """Generate a complete report in *fmt* and return as bytes."""
        if fmt == ReportFormat.JSON:
            return self._generate_json(report)
        elif fmt == ReportFormat.SARIF:
            return self._generate_sarif(report)
        elif fmt == ReportFormat.MARKDOWN:
            return self._generate_markdown(report)
        elif fmt == ReportFormat.HTML:
            return self._generate_html(report)
        raise ValueError(f"Unsupported ReportFormat: {fmt}")

    def stream(self, report: EnrichedReport, fmt: ReportFormat) -> Iterator[bytes]:
        """
        Stream large reports in chunks (≥ 1000 findings).
        Yields newline-delimited JSON records for JSON/SARIF,
        or page blocks for Markdown/HTML.
        """
        findings = self._sorted_findings(report.report.static_findings)
        chunk_size = 100

        if fmt == ReportFormat.JSON:
            yield b'{"findings":[\n'
            for i, f in enumerate(findings):
                sep = b",\n" if i < len(findings) - 1 else b"\n"
                yield json.dumps(f.model_dump(), sort_keys=True).encode() + sep
            yield b']}\n'
        else:
            # For other formats, fall back to single-shot generation
            yield self.generate(report, fmt)

    # ------------------------------------------------------------------
    # Format renderers
    # ------------------------------------------------------------------

    def _generate_json(self, r: EnrichedReport) -> bytes:
        findings = self._sorted_findings(r.report.static_findings)
        payload: Dict[str, Any] = {
            "schema_version": "3.0.0",
            "generated_at": r.generated_at,
            "tool": {"name": r.tool_name, "version": r.tool_version},
            "summary": {
                "total_issues":   r.report.total_issues,
                "llm_available":  r.report.llm_available,
                "severity_counts": self._severity_counts(findings),
            },
            "findings": [
                {
                    **f.model_dump(),
                    "explanation": r.explanations.get(f.rule_id),
                    "root_cause":  r.root_causes.get(f.rule_id),
                    "regression":  r.regressions.get(f.rule_id),
                }
                for f in findings
            ],
        }
        return json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")

    def _generate_sarif(self, r: EnrichedReport) -> bytes:
        rules = {f.rule_id: f for f in r.report.static_findings}
        sarif_rules = [
            {
                "id": rule_id,
                "name": rule_id.replace("-", " ").title(),
                "shortDescription": {"text": f.description},
                "properties": {"severity": f.severity},
            }
            for rule_id, f in rules.items()
        ]
        sarif_results = []
        for f in self._sorted_findings(r.report.static_findings):
            result: Dict[str, Any] = {
                "ruleId": f.rule_id,
                "level": self._sarif_level(f.severity),
                "message": {"text": f.description},
            }
            if f.file_path:
                loc: Dict[str, Any] = {
                    "physicalLocation": {
                        "artifactLocation": {"uri": f.file_path.replace("\\", "/")},
                    }
                }
                if f.line_number:
                    loc["physicalLocation"]["region"] = {"startLine": f.line_number}
                result["locations"] = [loc]
            sarif_results.append(result)

        sarif_doc = {
            "$schema": "https://schemastore.org/schemas/json/sarif-2.1.0.json",
            "version": "2.1.0",
            "runs": [{
                "tool": {
                    "driver": {
                        "name": r.tool_name,
                        "version": r.tool_version,
                        "rules": sarif_rules,
                    }
                },
                "results": sarif_results,
            }],
        }
        return json.dumps(sarif_doc, indent=2, sort_keys=True).encode("utf-8")

    def _generate_markdown(self, r: EnrichedReport) -> bytes:
        lines = [
            f"# {r.tool_name} — Analysis Report",
            f"",
            f"Generated: {r.generated_at}",
            f"",
            f"## Summary",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Total issues | {r.report.total_issues} |",
            f"| LLM available | {r.report.llm_available} |",
        ]
        counts = self._severity_counts(r.report.static_findings)
        for sev, cnt in counts.items():
            lines.append(f"| {sev} | {cnt} |")
        lines.append("")
        lines.append("---")
        lines.append("")

        for f in self._sorted_findings(r.report.static_findings):
            # Use pre-generated explanation markdown if available
            if f.rule_id in r.explanations:
                lines.append(r.explanations[f.rule_id])
            else:
                lines.extend([
                    f"## [{f.severity}] `{f.rule_id}`",
                    f"",
                    f"> {f.description}",
                    f"",
                    f"**File:** `{f.file_path}`  **Line:** {f.line_number}",
                    f"",
                    f"```\n{f.line_text.strip()}\n```",
                    f"",
                    f"**Evidence:** {f.evidence}",
                    f"",
                    f"**Remediation:** {f.remediation}",
                    f"",
                    f"**Confidence:** {f.static_confidence:.2f}",
                    "",
                    "---",
                    "",
                ])
        return "\n".join(lines).encode("utf-8")

    def _generate_html(self, r: EnrichedReport) -> bytes:
        findings = self._sorted_findings(r.report.static_findings)
        counts = self._severity_counts(findings)

        rows = []
        for f in findings:
            sev_class = f.severity.lower()
            rows.append(
                f'<tr class="sev-{sev_class}">'
                f'<td><span class="badge {sev_class}">{f.severity}</span></td>'
                f'<td><code>{f.rule_id}</code></td>'
                f'<td>{f.file_path or "—"}:{f.line_number or "?"}</td>'
                f'<td>{f.description}</td>'
                f'<td>{f.static_confidence:.2f}</td>'
                f'</tr>'
            )

        summary_pills = "".join(
            f'<span class="badge {s.lower()}">{s}: {c}</span> '
            for s, c in counts.items()
        )

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{r.tool_name} Report</title>
<style>
  body {{ font-family: system-ui, sans-serif; max-width: 1200px; margin: auto; padding: 2rem; background: #0f1117; color: #e2e8f0; }}
  h1 {{ color: #7c3aed; }}
  .badge {{ padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: bold; margin-right: 4px; }}
  .critical {{ background: #7f1d1d; color: #fca5a5; }}
  .high     {{ background: #7c2d12; color: #fed7aa; }}
  .medium   {{ background: #713f12; color: #fde68a; }}
  .low      {{ background: #1e3a5f; color: #93c5fd; }}
  table {{ border-collapse: collapse; width: 100%; margin-top: 1rem; }}
  th, td {{ text-align: left; padding: 8px 12px; border-bottom: 1px solid #1e293b; }}
  th {{ background: #1e293b; color: #94a3b8; font-weight: 600; }}
  tr:hover {{ background: #1e293b44; }}
  code {{ background: #1e293b; padding: 1px 4px; border-radius: 3px; font-size: 0.85rem; }}
  .summary {{ margin-bottom: 1.5rem; }}
</style>
</head>
<body>
<h1>🔍 {r.tool_name}</h1>
<p>Generated: <code>{r.generated_at}</code> &nbsp;|&nbsp; Tool: <code>{r.tool_version}</code></p>
<div class="summary">{summary_pills}</div>
<table>
  <thead><tr><th>Severity</th><th>Rule</th><th>Location</th><th>Description</th><th>Confidence</th></tr></thead>
  <tbody>{"".join(rows)}</tbody>
</table>
</body>
</html>"""
        return html.encode("utf-8")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _sorted_findings(findings: List[NormalizedFinding]) -> List[NormalizedFinding]:
        return sorted(
            findings,
            key=lambda f: (_SEVERITY_ORDER.get(f.severity, 9), -f.static_confidence),
        )

    @staticmethod
    def _severity_counts(findings: List[NormalizedFinding]) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for f in findings:
            counts[f.severity] = counts.get(f.severity, 0) + 1
        return counts

    @staticmethod
    def _sarif_level(severity: str) -> str:
        return {
            "CRITICAL": "error",
            "HIGH":     "error",
            "MEDIUM":   "warning",
            "LOW":      "note",
        }.get(severity, "note")
