# 🔍 Agentic Bug Hunter (HBH)

**Hybrid Bug Hunter** is an enterprise-grade software reasoning platform that combines deterministic static analysis, program graph construction, multi-agent LLM reasoning, evidence-backed confidence scoring, and automated patch planning to detect, validate, localize, and remediate defects in C++ codebases — with full explainability at every step.

Built across three major engineering phases, the system scales from single-file analysis to multi-million-line enterprise monorepositories.

---

## 🏗️ Architecture Overview

```
Repository
      │
      ▼
Parsing Layer  ──── AST / UIR / CFG / DFG / IPA
      │
      ▼
Repository Understanding  ──── Knowledge Graph, Symbol Table, Dependency Graph
      │
      ▼
Rule Engine  ──── Deterministic, pluggable, language-agnostic
      │
      ▼
Multi-Agent Semantic Reasoning  ──── Validator, Fixer, ReportGenerator
      │
      ▼
Evidence Graph  ──── Typed nodes + directed edges per finding
      │
      ▼
5-Stage Validation Pipeline  ──── Evidence → Semantic → Architecture → Consistency → Confidence
      │
      ▼
Suppression Pipeline  ──── 5 composable false-positive filters
      │
      ▼
Root Cause Analysis  ──── DFG backward slice + IPA causal chains
      │
      ▼
Patch Planning  ──── Ranked repair strategies with rollback descriptions
      │
      ▼
Regression Impact Analysis  ──── Forward IPA traversal, risk scoring
      │
      ▼
Enterprise Reports  ──── JSON · SARIF 2.1.0 · Markdown · HTML
```

---

## 🚀 Key Features

### Phase 1 — Foundation
- **VS Code-Grade Editor**: Monaco Editor with syntax highlighting and real-time diagnostics
- **Hybrid Verification**: Fast static rules + async LLM semantic validation
- **MCP Integration**: Core analysis exposed as Model Context Protocol tools for IDE AI agents
- **Docker Deployment**: Production `Dockerfile` + `docker-compose.yml` for zero-config local deployment

### Phase 2A — Static Analysis Platform
- **Pluggable Rule Engine**: Rules inherit `BaseRule`, register via `RuleRegistry`, execute over a typed `CodeRepresentation` IR
- **Language-Agnostic Parsers**: `ParserRegistry` maps file extensions to parser implementations
- **MCP Tool Registry**: `MCPCoordinator` wraps tool execution in `asyncio.wait_for` timeout pools with structured error handling
- **Normalized Finding Schema**: All findings emit `NormalizedFinding` (Pydantic) with rule_id, severity, confidence, evidence, and remediation

### Phase 3A — Intelligent Analysis Infrastructure  
- **Unified Intermediate Representation (UIR)**: Language-agnostic statement nodes (Assignment, Branch, Call, Return, FunctionDecl)
- **Symbol Table & Scope Resolution**: `ScopedContext` with parent-child namespace walking
- **Type Inference Engine**: Literal constant typing + prefix-based return type inference
- **Control Flow Graph (CFG)**: Basic block construction with branch-edge mapping
- **Data Flow Graph (DFG)**: Variable propagation chains via assignment traversal
- **Interprocedural Call Tracer (IPA)**: Caller → callee call-graph with multi-function scope tracking

### Phase 3B.1 — Multi-Agent Runtime
- **DAG Execution Scheduler**: `ExecutionGraph` with topological sort, cycle detection, and concurrent node execution via `asyncio.gather`
- **Agent Message Bus**: `AgentMessageBus` with typed `MessageEnvelope` contracts, correlation IDs, and async handler routing
- **State Manager**: Checkpoint persistence to `backend/storage/checkpoints/` for replay and disaster recovery

### Phase 3B.2 — Enterprise Knowledge Systems
- **Working Memory**: LRU-evicting in-process cache for active analysis context
- **Semantic Memory**: Long-term vector-similarity knowledge store for confirmed bug patterns and false-positive suppression
- **Repository Knowledge Graph**: `RepositoryKnowledgeGraph` with symbol registry and call-graph edge traversal
- **Model Router**: Complexity-aware LLM model selection (`llama3-8b-8192` for simple, `llama-3.1-70b-versatile` for multi-file)

### Phase 3C.1 — Code Intelligence Engine
- **UIR Parser Nodes**: Full statement-level IR with typed AST primitives
- **Scoped Symbol Resolution**: Circular-shadow-bug prevention via parent-scope walking
- **CFG + DFG + IPA**: Program graph construction suite (all 3 engines verified against regression suite)

### Phase 3C.2 — Intelligent Bug Detection & Root Cause Reasoning *(latest)*
- **Evidence Graph** (`evidence.py`): Every finding materialized as a directed typed graph (12 node types, 9 edge types) — fully JSON-serializable
- **Confidence Engine** (`confidence.py`): Reproducible weighted formula: `0.45×static + 0.25×semantic + 0.20×consensus + 0.10×history − penalties`
- **Explainability Engine** (`explain.py`): 3 output formats — full Markdown, one-paragraph summary, JSON forensic dict — answers all 7 mandatory explainability questions
- **Suppression Pipeline** (`suppression.py`): 5 composable filters in cheapest-first order; full audit log; extensible via `BaseSuppressionFilter`
- **Multi-Hop Reasoner** (`multi_hop.py`): BFS/DFS graph traversal with confidence accumulation, cycle detection, and depth cap
- **Bug Localizer** (`localizer.py`): 3-stage: statement → function/class → file fallback; ranked `CodeSpan` output
- **Cross-File Reasoner** (`cross_file.py`): Unified file-dependency + call-graph traversal; reverse-dependency lookup
- **Root Cause Analyzer** (`root_cause.py`): Backward DFG slice + IPA caller traversal → ranked `RootCauseChain` with eliminated hypotheses preserved
- **Patch Planner** (`patch.py`): 3 ranked `RepairStrategy` objects; score = `correctness×0.5 + maintainability×0.3 − risk×0.2`
- **Remediation Reasoner** (`remediation.py`): Strategy evaluation against SemanticMemory + architecture rules; `NO_VIABLE_STRATEGY` guard
- **Regression Analyzer** (`regression.py`): Forward IPA traversal; per-component `regression_risk = reach×centrality×(1−coverage)`; API/security/performance flags
- **Validation Pipeline** (`validation_pipeline.py`): 5-stage gate — Stage 1 hard-rejects, Stages 2–4 degrade severity to LOW, Stage 5 delegates to suppression
- **Report Generator** (`report.py`): JSON, SARIF 2.1.0, Markdown, dark-theme self-contained HTML; streaming support for >1K findings
- **Detection Orchestrator** (`detection_orchestrator.py`): Single `run()` façade combining all 11 subsystems; returns 4 pre-rendered report formats

---

## 📁 Repository Structure

```
agentic-bug-hunter/
├── backend/
│   ├── core/
│   │   ├── analysis/                     # Phase 3A–3C analysis engines
│   │   │   ├── parsers/                  # Language frontend + UIR
│   │   │   │   ├── base.py               # CodeRepresentation IR contract
│   │   │   │   ├── registry.py           # ParserRegistry
│   │   │   │   ├── cpp_parser.py         # C++ tokenizer and IR builder
│   │   │   │   └── uir.py                # Unified Intermediate Representation nodes
│   │   │   ├── rules/                    # Pluggable rule engine
│   │   │   │   ├── base.py               # BaseRule abstract class
│   │   │   │   ├── registry.py           # RuleRegistry
│   │   │   │   └── rdi_rules.py          # RDI API check rules (5 rules)
│   │   │   ├── schemas.py                # NormalizedFinding + AnalysisReport (Pydantic)
│   │   │   ├── engine.py                 # AnalysisEngine — full Phase 3C.2 pipeline
│   │   │   ├── detection_orchestrator.py # DetectionOrchestrator — end-to-end façade
│   │   │   ├── graph.py                  # DAG ExecutionGraph scheduler
│   │   │   ├── state.py                  # StateManager — checkpoint persistence
│   │   │   ├── repo_graph.py             # RepositoryKnowledgeGraph
│   │   │   ├── symbols.py                # ScopedContext + ScopedSymbol
│   │   │   ├── types.py                  # TypeInferencer
│   │   │   ├── cfg.py                    # CFGGenerator — basic blocks + branch edges
│   │   │   ├── dfg.py                    # DFGConstructor — variable propagation chains
│   │   │   ├── ipa.py                    # IPATracer — interprocedural call graph
│   │   │   ├── evidence.py               # EvidenceGraph + EvidenceGraphBuilder
│   │   │   ├── confidence.py             # ConfidenceEngine — weighted reproducible scoring
│   │   │   ├── explain.py                # ExplainabilityEngine — Markdown/summary/forensic
│   │   │   ├── suppression.py            # SuppressionPipeline — 5 composable filters
│   │   │   ├── multi_hop.py              # MultiHopReasoner — BFS/DFS graph traversal
│   │   │   ├── localizer.py              # BugLocalizer — statement/function/file spans
│   │   │   ├── cross_file.py             # CrossFileReasoner — cross-module dependency tracing
│   │   │   ├── root_cause.py             # RootCauseAnalyzer — causal chain inference
│   │   │   ├── patch.py                  # PatchPlanningEngine — ranked repair strategies
│   │   │   ├── remediation.py            # RemediationReasoner — strategy evaluation
│   │   │   ├── regression.py             # RegressionAnalyzer — forward impact analysis
│   │   │   ├── validation_pipeline.py    # ValidationPipeline — 5-stage finding gate
│   │   │   └── report.py                 # ReportGenerator — JSON/SARIF/Markdown/HTML
│   │   ├── ai/                           # LLM reasoning layer
│   │   │   ├── agents/                   # Agent implementations
│   │   │   │   ├── base.py               # BaseAgent contract
│   │   │   │   ├── validator.py          # ValidatorAgent — semantic false-positive check
│   │   │   │   ├── fixer.py              # FixerAgent — correction generation
│   │   │   │   └── report_generator.py   # ReportGeneratorAgent — audit compilation
│   │   │   ├── memory/
│   │   │   │   ├── working.py            # WorkingMemory — LRU in-process cache
│   │   │   │   └── semantic.py           # SemanticMemory — vector similarity store
│   │   │   ├── providers/                # LLM provider adapters (Groq, etc.)
│   │   │   ├── bus.py                    # AgentMessageBus + MessageEnvelope
│   │   │   └── router.py                 # ModelRoutingEngine — complexity-aware model selection
│   │   ├── mcp/                          # Model Context Protocol layer
│   │   │   ├── registry.py               # MCPToolRegistry — tool metadata + timeouts
│   │   │   ├── coordinator.py            # MCPCoordinator — async execution + error handling
│   │   │   └── tools.py                  # MCP tool implementations
│   │   ├── config.py                     # Pydantic settings loader
│   │   └── orchestrator.py               # Legacy pipeline orchestrator (LLM agent coordination)
│   ├── api/
│   │   └── router.py                     # FastAPI HTTP routes
│   ├── tests/
│   │   └── test_static_engine.py         # Regression test suite (5 tests, 0 dependencies)
│   ├── main.py                           # FastAPI application entry point
│   ├── mcp_server.py                     # FastMCP server CLI entry point
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                             # Next.js UI
│   ├── src/
│   │   ├── app/                          # App routing + global stylesheet
│   │   ├── components/                   # Monaco Editor, Header, Results Panel
│   │   └── lib/                          # API fetch client
│   ├── package.json
│   └── Dockerfile
├── docs/
│   ├── architecture.md
│   ├── setup.md
│   ├── deployment.md
│   ├── troubleshooting.md
│   └── contributing.md
├── PHASE_1_SUMMARY.md
├── PHASE_3A_SUMMARY.md
├── PHASE_3B_1_SUMMARY.md
├── PHASE_3B_2_SUMMARY.md
├── PHASE_3C_1_SUMMARY.md
├── PHASE_3C_2_SUMMARY.md
├── PHASE_3C_2_SPEC.md                    # Full architecture spec (§109–§132)
└── docker-compose.yml
```

---

## 🛠️ Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- A [Groq API key](https://console.groq.com) (free tier works)

### Backend (FastAPI)
```bash
cd backend
python -m venv venv
# Windows:
.\\venv\\Scripts\\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
export GROQ_API_KEY="your_api_key_here"   # Windows: $env:GROQ_API_KEY="..."
python main.py
```
API available at **http://localhost:8000**

### Frontend (Next.js)
```bash
cd frontend
npm install
npm run dev
```
UI available at **http://localhost:3000**

### Docker (full stack)
```bash
export GROQ_API_KEY="your_api_key_here"
docker compose up --build
```

---

## 🧪 Running Tests

```bash
# From project root — zero extra dependencies required
python -m unittest backend/tests/test_static_engine.py -v
```

Expected output:
```
test_blocking_delay_in_isr ... ok
test_incomplete_chaining   ... ok
test_null_pointer          ... ok
test_unknown_methods       ... ok
test_unmatched_rdi_blocks  ... ok

Ran 5 tests in 0.003s  OK
```

---

## ⚡ Usage — Phase 3C.2 Pipeline

### Full end-to-end analysis (new API)
```python
from backend.core.analysis.detection_orchestrator import DetectionOrchestrator

orch   = DetectionOrchestrator()
result = orch.run(code="void IRAM_ATTR my_isr() { delay(100); }", extension="cpp")

# Enriched findings with evidence + confidence + explanations
for ef in result.enriched_findings:
    print(ef.finding.rule_id, ef.finding.severity)
    print(ef.confidence_result.final_score)
    print(ef.explanation.summary)

# Per-finding deep analysis
for fa in result.finding_analyses:
    print("Root cause:", fa.root_cause.primary.hypothesis)
    print("Best fix:  ", fa.patch_plan.best.description)
    print("API risk:  ", fa.regression.api_compat_verdict)

# Pre-rendered reports
with open("report.sarif", "wb") as f:
    f.write(result.sarif_report)   # SARIF 2.1.0 for GitHub Code Scanning
with open("report.html", "wb") as f:
    f.write(result.html_report)    # Self-contained dark-theme HTML
```

### Backward-compatible API (existing integrations)
```python
from backend.core.analysis.engine import AnalysisEngine

engine   = AnalysisEngine()
findings = engine.analyze_plain(code)   # returns List[NormalizedFinding]
```

### Using individual subsystems
```python
from backend.core.analysis.evidence import EvidenceGraphBuilder
from backend.core.analysis.confidence import ConfidenceEngine, ConfidenceInputs
from backend.core.analysis.root_cause import RootCauseAnalyzer
from backend.core.analysis.suppression import SuppressionPipeline

# Build evidence graph for a finding
graph = EvidenceGraphBuilder().build(finding)

# Compute reproducible confidence score
cr = ConfidenceEngine().compute(ConfidenceInputs(
    static_score=0.9,
    semantic_score=0.8,
    consensus_score=0.75,
    history_score=0.6,
))
print(cr.final_score)  # → 0.825

# Run false-positive suppression
pipeline = SuppressionPipeline.default(min_confidence=0.30)
result   = pipeline.run(findings)
# result.passed     → surfaced findings
# pipeline.audit_log → every suppressed finding with reason
```

---

## 🌐 REST API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/analyze` | Full analysis — body: `{"code": "..."}` |
| `GET`  | `/rules`   | List all active rules with metadata |
| `GET`  | `/health`  | Server availability check |
| `GET`  | `/ollama/status` | LLM provider connectivity check |

---

## 🧩 Extending the Platform

### Add a new detection rule
```python
from backend.core.analysis.rules.base import BaseRule
from backend.core.analysis.rules.registry import RuleRegistry

@RuleRegistry.register
class MyRule(BaseRule):
    rule_id  = "my_custom_rule"
    language = "cpp"
    severity = "HIGH"
    confidence = 0.85
    # ...
    def execute(self, representation): ...
```

### Add a new language frontend
```python
from backend.core.analysis.parsers.base import BaseParser
from backend.core.analysis.parsers.registry import ParserRegistry

class PythonParser(BaseParser):
    def parse(self, code: str) -> CodeRepresentation: ...

ParserRegistry.register("py", PythonParser)
```

### Add a custom suppression filter
```python
from backend.core.analysis.suppression import BaseSuppressionFilter, SuppressionPipeline

class TeamFilter(BaseSuppressionFilter):
    name = "TeamFilter"
    def apply(self, findings): ...

pipeline = SuppressionPipeline.default()
pipeline.register_filter(TeamFilter())
```

---

## 📊 Performance Targets

| Operation | Target |
|-----------|--------|
| Single-file static analysis | < 100 ms |
| Full 3C.2 pipeline per file | < 5 s (incl. agent round-trips) |
| Root cause analysis | < 200 ms |
| Regression impact analysis | < 500 ms |
| Report generation (1K findings) | < 1 s |

---

## 📋 Phase Completion Status

| Phase | Status | Summary |
|-------|--------|---------|
| Phase 1 | ✅ Complete | Foundation — editor, hybrid analysis, MCP, Docker |
| Phase 2A.1 | ✅ Complete | Functional architecture — rule engine, IR, parsers |
| Phase 2A.2 | ✅ Complete | Technical architecture — schemas, registry, MCP decoupling |
| Phase 3A | ✅ Complete | Intelligence layer — UIR, symbols, types, CFG, DFG, IPA |
| Phase 3B.1 | ✅ Complete | Multi-agent runtime — DAG scheduler, message bus, state |
| Phase 3B.2 | ✅ Complete | Knowledge systems — semantic memory, repo graph, model router |
| Phase 3C.1 | ✅ Complete | Code intelligence engine — all program graph builders verified |
| Phase 3C.2 | ✅ Complete | Bug detection & reasoning — 15 new modules, 5/5 tests pass |

---

## 🛡️ Architecture Specification

The full internal engineering specification (§109–§132) is available at [`PHASE_3C_2_SPEC.md`](./PHASE_3C_2_SPEC.md), covering:
- §109 Intelligent Bug Detection Architecture
- §110 Rule-Based Detection Engine
- §111 Semantic Bug Detection
- §112 Multi-Agent Collaborative Detection
- §113 Bug Localization Engine
- §114 Cross-File & Cross-Service Reasoning
- §115 Root Cause Analysis Engine
- §116 Evidence Graph Construction
- §117 Multi-Hop Reasoning
- §118 Confidence Framework
- §119 Explainability Engine
- §120 False Positive Reduction
- §121 Patch Planning Engine
- §122 Automated Remediation Reasoning
- §123 Regression Impact Analysis
- §124 Validation Architecture
- §125 Enterprise Reporting
- §126 Continuous Repository Learning
- §127 Performance Optimization
- §128 Security & Governance
- §129 Extensibility Framework
- §130 Production Readiness
- §131 End-to-End Reasoning Pipeline
- §132 System Requirements & Acceptance Criteria

---

## 📄 License

MIT License — see `LICENSE` for details.
