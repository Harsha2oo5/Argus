# ARGUS — Enterprise AI Software Engineering Platform

ARGUS is an enterprise-grade software reasoning platform that combines deterministic static analysis, program graph construction, multi-agent LLM reasoning, evidence-backed confidence scoring, autonomous patch generation, and patch validation to detect, localize, remediate, and verify defects in C++ codebases — with full explainability and auditability at every step.

---

## Architecture Overview

```
Repository
      |
      v
Parsing Layer            AST / UIR / CFG / DFG / IPA
      |
      v
Repository Understanding  Knowledge Graph, Symbol Table, Dependency Graph
      |
      v
Rule Engine               Deterministic, pluggable, language-agnostic
      |
      v
Multi-Agent Reasoning     Validator, Fixer, ReportGenerator agents
      |
      v
Evidence Graph            Typed nodes and directed edges per finding
      |
      v
5-Stage Validation        Evidence -> Semantic -> Architecture -> Consistency -> Confidence
      |
      v
Suppression Pipeline      5 composable false-positive filters
      |
      v
Root Cause Analysis       DFG backward slice + IPA causal chains
      |
      v
Patch Generation          Ranked repair candidates with LLM reasoning (Phase 3D.1)
      |
      v
Patch Validation          Isolated workspace verification, compilation, regression (Phase 3D.2)
      |
      v
Engineering Reports       JSON / SARIF 2.1.0 / Markdown / HTML
```

---

## Key Capabilities

### Phase 1 — Foundation
- Monaco Editor-based UI with syntax highlighting and real-time diagnostics
- Hybrid verification combining fast static rules with async LLM semantic validation
- Core analysis exposed as Model Context Protocol (MCP) tools for IDE AI agents
- Production Dockerfile and docker-compose for zero-config local deployment

### Phase 2 — Static Analysis Platform
- Pluggable rule engine: rules inherit `BaseRule`, register via `RuleRegistry`, execute over a typed `CodeRepresentation` IR
- Language-agnostic parser registry mapping file extensions to parser implementations
- `MCPCoordinator` wrapping tool execution in `asyncio.wait_for` timeout pools with structured error handling
- Normalized finding schema: all findings emit `NormalizedFinding` (Pydantic) with rule_id, severity, confidence, evidence, and remediation

### Phase 3A — Intelligent Analysis Infrastructure
- Unified Intermediate Representation (UIR): language-agnostic statement nodes (Assignment, Branch, Call, Return, FunctionDecl)
- Symbol table and scope resolution: `ScopedContext` with parent-child namespace walking
- Type inference engine: literal constant typing and prefix-based return type inference
- Control Flow Graph (CFG): basic block construction with branch-edge mapping
- Data Flow Graph (DFG): variable propagation chains via assignment traversal
- Interprocedural Call Tracer (IPA): caller-to-callee call graph with multi-function scope tracking

### Phase 3B.1 — Multi-Agent Runtime
- DAG Execution Scheduler: `ExecutionGraph` with topological sort, cycle detection, and concurrent node execution via `asyncio.gather`
- Agent Message Bus: `AgentMessageBus` with typed `MessageEnvelope` contracts, correlation IDs, and async handler routing
- State Manager: checkpoint persistence for replay and disaster recovery

### Phase 3B.2 — Enterprise Knowledge Systems
- Working Memory: LRU-evicting in-process cache for active analysis context
- Semantic Memory: long-term vector-similarity knowledge store for confirmed bug patterns and false-positive suppression
- Repository Knowledge Graph: `RepositoryKnowledgeGraph` with symbol registry and call-graph edge traversal
- Model Router: complexity-aware LLM model selection across classification, validation, and repair task types

### Phase 3C.1 — Code Intelligence Engine
- Full statement-level IR with typed AST primitives
- Circular-shadow-bug prevention via parent-scope walking
- CFG, DFG, and IPA program graph construction suite, all verified against regression suite

### Phase 3C.2 — Intelligent Bug Detection and Root Cause Reasoning
- Evidence Graph: every finding materialized as a directed typed graph (12 node types, 9 edge types), fully JSON-serializable
- Confidence Engine: reproducible weighted formula — `0.45 x static + 0.25 x semantic + 0.20 x consensus + 0.10 x history - penalties`
- Explainability Engine: three output formats (Markdown, one-paragraph summary, JSON forensic dict) answering 7 mandatory explainability questions
- Suppression Pipeline: 5 composable filters in cheapest-first order with full audit log and extensible `BaseSuppressionFilter`
- Multi-Hop Reasoner: BFS/DFS graph traversal with confidence accumulation, cycle detection, and depth cap
- Bug Localizer: three-stage fallback (statement -> function/class -> file); ranked `CodeSpan` output
- Cross-File Reasoner: unified file-dependency and call-graph traversal with reverse-dependency lookup
- Root Cause Analyzer: backward DFG slice and IPA caller traversal producing ranked `RootCauseChain` with eliminated hypotheses preserved
- Patch Planner: 3 ranked `RepairStrategy` objects; score = `correctness x 0.5 + maintainability x 0.3 - risk x 0.2`
- Remediation Reasoner: strategy evaluation against SemanticMemory and architecture rules; `NO_VIABLE_STRATEGY` guard
- Regression Analyzer: forward IPA traversal; per-component `regression_risk = reach x centrality x (1 - coverage)`; API, security, and performance flags
- Validation Pipeline: 5-stage gate — Stage 1 hard-rejects, Stages 2-4 degrade severity to LOW, Stage 5 delegates to suppression
- Report Generator: JSON, SARIF 2.1.0, Markdown, dark-theme self-contained HTML; streaming support for >1K findings
- Detection Orchestrator: single `run()` facade combining all 11 subsystems; returns four pre-rendered report formats

### Phase 3D.1 — Autonomous Patch Generation
- End-to-end `PatchGenerationEngine` producing `StructuredPatch` artifacts from confirmed findings
- Context Selector: token-bounded repository context assembly from CFG, DFG, evidence, and call graph
- Edit Planner: pre-generation scope analysis producing structured `EditPlan` with per-file `EditAction` objects
- Prompt Builder: versioned system and user prompt assembly with repair category guidance injection
- Patch Output Parser: robust JSON candidate extraction with malformed-output recovery
- Unified Diff Generator: git-compatible diff generation per candidate
- Patch Explainer: rule-based fallback explanation synthesizer requiring no additional LLM calls
- Syntax Preserver: style detection and candidate-level style violation reporting
- Patch Builder: confidence-based candidate filtering, ranking, and `StructuredPatch` assembly
- Patch History Store: thread-safe, in-memory generation event log with serialization support
- 20 supported repair categories across memory, control flow, API usage, lifetime, concurrency, and type safety
- LLM Fallback Router: sequential model fallback across configured models on provider failure (added in 3D.1 reliability pass)
- 104 unit tests, 0 failures

### Phase 3D.2 — Autonomous Patch Validation
- `ValidationEngine`: top-level orchestrator running the full validation pipeline across all candidates and returning a `ValidationReport`
- `WorkspaceManager`: context-managed isolated directory creation using `tempfile`; supports `temp_dir`, `git_worktree`, and `none` modes; original repository is never modified
- `PatchApplier`: unified diff parser with hunk offset tolerance (±30 lines) and block-replace fallback for partial-match diffs
- `SyntaxValidator`: pre-compilation structural check for balanced braces, parentheses, brackets, and preprocessor directive syntax
- Compiler abstraction: `BaseCompiler` ABC with `GCCCompiler`, `ClangCompiler`, and `MSVCCompiler` async subprocess runners capturing stdout, stderr, warnings, errors, and timing
- `CompilerRegistry`: string-based compiler resolver with extensible registration
- Build system abstraction: `CMakeBuildSystem`, `MakeBuildSystem`, `NinjaBuildSystem`, `BazelBuildSystem`, `NoneBuildSystem`, and `BuildSystemRegistry`
- `StaticValidator`: re-runs `AnalysisEngine` on the patched file and compares findings to confirm bug removal and detect newly introduced violations
- `TestDiscovery`: scans for CTest configurations, shell/Python test scripts, and test binaries (GoogleTest, Catch2)
- `RegressionRunner`: async subprocess test runner with output parsers for CTest, GoogleTest, Catch2, and binary exit codes
- `QualityMetrics`: weighted scoring across bug removal (0.4), regression pass (0.3), simplicity (0.1), minus penalties for new bugs and warning increases
- `DiagnosticsCollector`: step-by-step accumulator for errors, warnings, timing records, affected files, and remediation actions
- `RollbackManager`: in-memory file backup and restore guaranteeing no partial state on failure
- `CandidateRanker`: multi-key sort and winner selection with configurable minimum acceptance score
- `ValidationReportGenerator`: JSON, Markdown, and SARIF 2.1.0 output formatters
- 19 unit tests added, 132 total tests, 0 failures

---

## Repository Structure

```
argus/
├── backend/
│   ├── core/
│   │   ├── analysis/                     # Phases 3A-3C analysis engines
│   │   │   ├── parsers/                  # Language frontend and UIR
│   │   │   │   ├── base.py               # CodeRepresentation IR contract
│   │   │   │   ├── registry.py           # ParserRegistry
│   │   │   │   ├── cpp_parser.py         # C++ tokenizer and IR builder
│   │   │   │   └── uir.py                # Unified Intermediate Representation nodes
│   │   │   ├── rules/                    # Pluggable rule engine
│   │   │   │   ├── base.py               # BaseRule abstract class
│   │   │   │   ├── registry.py           # RuleRegistry
│   │   │   │   └── rdi_rules.py          # RDI API check rules
│   │   │   ├── schemas.py                # NormalizedFinding + AnalysisReport (Pydantic)
│   │   │   ├── engine.py                 # AnalysisEngine — full Phase 3C.2 pipeline
│   │   │   ├── detection_orchestrator.py # DetectionOrchestrator — end-to-end facade
│   │   │   ├── graph.py                  # DAG ExecutionGraph scheduler
│   │   │   ├── state.py                  # StateManager — checkpoint persistence
│   │   │   ├── repo_graph.py             # RepositoryKnowledgeGraph
│   │   │   ├── symbols.py                # ScopedContext + ScopedSymbol
│   │   │   ├── types.py                  # TypeInferencer
│   │   │   ├── cfg.py                    # CFGGenerator — basic blocks and branch edges
│   │   │   ├── dfg.py                    # DFGConstructor — variable propagation chains
│   │   │   ├── ipa.py                    # IPATracer — interprocedural call graph
│   │   │   ├── evidence.py               # EvidenceGraph + EvidenceGraphBuilder
│   │   │   ├── confidence.py             # ConfidenceEngine — weighted reproducible scoring
│   │   │   ├── explain.py                # ExplainabilityEngine
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
│   │   │   ├── agents/
│   │   │   │   ├── base.py               # BaseAgent contract
│   │   │   │   ├── validator.py          # ValidatorAgent — semantic false-positive check
│   │   │   │   ├── fixer.py              # FixerAgent — correction generation
│   │   │   │   └── report_generator.py   # ReportGeneratorAgent — audit compilation
│   │   │   ├── memory/
│   │   │   │   ├── working.py            # WorkingMemory — LRU in-process cache
│   │   │   │   └── semantic.py           # SemanticMemory — vector similarity store
│   │   │   ├── providers/
│   │   │   │   ├── base.py               # BaseLLMProvider abstract interface
│   │   │   │   ├── groq.py               # GroqProvider with sequential model fallback
│   │   │   │   └── factory.py            # LLMProviderFactory
│   │   │   ├── bus.py                    # AgentMessageBus + MessageEnvelope
│   │   │   └── router.py                 # ModelRoutingEngine — task-aware model routing
│   │   ├── patch_generation/             # Phase 3D.1 — Autonomous Patch Generation
│   │   │   ├── patch_generator.py        # PatchGenerationEngine — main entry point
│   │   │   ├── patch_models.py           # All generation Pydantic models
│   │   │   ├── patch_builder.py          # StructuredPatch assembly
│   │   │   ├── patch_parser.py           # LLM output parser with recovery
│   │   │   ├── patch_explainer.py        # Rule-based explanation synthesizer
│   │   │   ├── patch_history.py          # PatchHistoryStore
│   │   │   ├── context_selector.py       # Token-bounded context assembly
│   │   │   ├── edit_planner.py           # EditPlan + EditAction construction
│   │   │   ├── prompt_builder.py         # Versioned system and user prompt builder
│   │   │   ├── diff_generator.py         # Unified diff generation
│   │   │   ├── syntax_preserver.py       # Style detection and violation reporting
│   │   │   ├── repair_strategies.py      # RepairGuidanceRegistry (20 categories)
│   │   │   ├── candidate_ranker.py       # Confidence-based candidate ranking
│   │   │   ├── exceptions.py             # Generation exception hierarchy
│   │   │   └── __init__.py               # Package exports
│   │   ├── patch_validation/             # Phase 3D.2 — Autonomous Patch Validation
│   │   │   ├── validation_engine.py      # ValidationEngine — top-level public API
│   │   │   ├── validator.py              # CandidateValidator — single-candidate pipeline
│   │   │   ├── workspace_manager.py      # Isolated workspace creation and cleanup
│   │   │   ├── patch_applier.py          # Unified diff and block-replace applier
│   │   │   ├── syntax_validator.py       # Pre-compilation structural syntax check
│   │   │   ├── compiler.py               # GCC, Clang, MSVC async runners
│   │   │   ├── compiler_registry.py      # Compiler resolver registry
│   │   │   ├── build_system.py           # CMake/Make/Ninja/Bazel/Direct + registry
│   │   │   ├── static_validator.py       # Before/after static analysis comparison
│   │   │   ├── test_discovery.py         # CTest, script, and binary test discovery
│   │   │   ├── regression_runner.py      # Async test runner with output parsers
│   │   │   ├── quality_metrics.py        # Weighted validation score computation
│   │   │   ├── candidate_ranker.py       # Multi-key candidate sort and winner selection
│   │   │   ├── diagnostics.py            # DiagnosticsCollector builder
│   │   │   ├── rollback.py               # File backup and atomic restore
│   │   │   ├── validation_report.py      # JSON, Markdown, and SARIF report formatters
│   │   │   ├── validation_models.py      # All validation Pydantic models
│   │   │   ├── configuration.py          # PatchValidationConfig
│   │   │   ├── exceptions.py             # Validation exception hierarchy
│   │   │   └── __init__.py               # Package exports
│   │   ├── mcp/                          # Model Context Protocol layer
│   │   │   ├── registry.py               # MCPToolRegistry
│   │   │   ├── coordinator.py            # MCPCoordinator
│   │   │   └── tools.py                  # MCP tool implementations
│   │   ├── config.py                     # Settings loader
│   │   └── orchestrator.py              # Legacy pipeline orchestrator
│   ├── api/
│   │   └── router.py                     # FastAPI HTTP routes
│   ├── tests/
│   │   ├── test_static_engine.py         # Static engine regression suite
│   │   ├── test_patch_generation.py      # Phase 3D.1 unit tests (104 tests)
│   │   ├── test_patch_validation.py      # Phase 3D.2 unit tests (19 tests)
│   │   └── test_groq_provider.py         # LLM fallback unit tests (4 tests)
│   ├── main.py                           # FastAPI application entry point
│   ├── mcp_server.py                     # FastMCP server CLI entry point
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                             # Next.js UI
│   ├── src/
│   │   ├── app/
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
├── PHASE_3D_1_SUMMARY.md
├── PHASE_3D_2_SUMMARY.md
└── docker-compose.yml
```

---

## Quick Start

### Prerequisites
- Python 3.12+
- Node.js 20+
- A [Groq API key](https://console.groq.com) (free tier is sufficient)

### Backend

```bash
cd backend
python -m venv venv

# Windows
.\\venv\\Scripts\\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
export GROQ_API_KEY="your_api_key_here"   # Windows: $env:GROQ_API_KEY="..."
python main.py
```

API available at `http://localhost:8000`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

UI available at `http://localhost:3000`

### Docker (full stack)

```bash
export GROQ_API_KEY="your_api_key_here"
docker compose up --build
```

---

## Running Tests

```bash
cd backend
python -m unittest discover -s tests
```

Expected output:

```
Ran 132 tests in ~1.1s

OK
```

Test breakdown:

| Suite | Tests |
|---|---|
| `test_static_engine.py` | 5 |
| `test_patch_generation.py` | 104 |
| `test_patch_validation.py` | 19 |
| `test_groq_provider.py` | 4 |
| **Total** | **132** |

---

## Usage

### End-to-end analysis (Phase 3C.2 API)

```python
from backend.core.analysis.detection_orchestrator import DetectionOrchestrator

orch   = DetectionOrchestrator()
result = orch.run(code="void IRAM_ATTR my_isr() { delay(100); }", extension="cpp")

for ef in result.enriched_findings:
    print(ef.finding.rule_id, ef.finding.severity)
    print(ef.confidence_result.final_score)
    print(ef.explanation.summary)

for fa in result.finding_analyses:
    print("Root cause:", fa.root_cause.primary.hypothesis)
    print("Best fix:  ", fa.patch_plan.best.description)

with open("report.sarif", "wb") as f:
    f.write(result.sarif_report)
```

### Patch generation (Phase 3D.1 API)

```python
from backend.core.ai.providers.factory import LLMProviderFactory
from backend.core.patch_generation import PatchGenerationEngine, PatchGenerationConfig

provider = LLMProviderFactory.get_provider("groq")
engine   = PatchGenerationEngine(provider, PatchGenerationConfig())

patch = await engine.generate(
    finding    = finding,      # NormalizedFinding
    code       = source_code,
    root_cause = root_cause,   # RootCauseChain
    evidence   = evidence,     # EvidenceGraph
    bug_id     = "BUG-001",
)
# patch.file_patches[0].candidates  -> List[PatchCandidate]
```

### Patch validation (Phase 3D.2 API)

```python
from backend.core.patch_validation import ValidationEngine, PatchValidationConfig

config = PatchValidationConfig(
    compiler_type   = "gcc",
    build_system    = "cmake",
    regression_enabled       = True,
    static_analysis_enabled  = True,
    min_acceptance_score     = 0.7,
)
engine = ValidationEngine(config)

report = await engine.validate_patch(
    patch              = patch,           # StructuredPatch from 3D.1
    original_code_path = "/path/to/repo",
)

if report.accepted:
    print("Winner:", report.winner_candidate_id)
    print("Score: ", report.metrics[report.winner_candidate_id].score)
else:
    print("No candidate passed validation thresholds.")
    for error in report.diagnostics.errors:
        print(" -", error)
```

### Validation report formats

```python
from backend.core.patch_validation import ValidationReportGenerator

markdown = ValidationReportGenerator.to_markdown(report)
json_str = ValidationReportGenerator.to_json(report)
sarif    = ValidationReportGenerator.to_sarif(report)
```

### Backward-compatible static analysis API

```python
from backend.core.analysis.engine import AnalysisEngine

findings = AnalysisEngine().analyze_plain(code)   # List[NormalizedFinding]
```

---

## REST API

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/analyze` | Full analysis — body: `{"code": "..."}` |
| `GET` | `/rules` | List all active rules with metadata |
| `GET` | `/health` | Server availability check |
| `GET` | `/ollama/status` | LLM provider connectivity check |

---

## Extending the Platform

### Add a detection rule

```python
from backend.core.analysis.rules.base import BaseRule
from backend.core.analysis.rules.registry import RuleRegistry

@RuleRegistry.register
class MyRule(BaseRule):
    rule_id    = "my_custom_rule"
    language   = "cpp"
    severity   = "HIGH"
    confidence = 0.85

    def execute(self, representation): ...
```

### Add a language parser

```python
from backend.core.analysis.parsers.base import BaseParser
from backend.core.analysis.parsers.registry import ParserRegistry

class PythonParser(BaseParser):
    def parse(self, code: str) -> CodeRepresentation: ...

ParserRegistry.register("py", PythonParser)
```

### Add a suppression filter

```python
from backend.core.analysis.suppression import BaseSuppressionFilter, SuppressionPipeline

class TeamFilter(BaseSuppressionFilter):
    name = "TeamFilter"
    def apply(self, findings): ...

pipeline = SuppressionPipeline.default()
pipeline.register_filter(TeamFilter())
```

### Add a compiler backend

```python
from backend.core.patch_validation.compiler import BaseCompiler
from backend.core.patch_validation.compiler_registry import CompilerRegistry
from backend.core.patch_validation.validation_models import CompilationResult

class IntelCompiler(BaseCompiler):
    async def compile(self, workspace_path, source_files, build_command=None, timeout=30) -> CompilationResult:
        ...

CompilerRegistry._compilers["intel"] = IntelCompiler
```

---

## Performance Targets

| Operation | Target |
|---|---|
| Single-file static analysis | < 100 ms |
| Full 3C.2 pipeline per file | < 5 s |
| Root cause analysis | < 200 ms |
| Regression impact analysis | < 500 ms |
| Report generation (1K findings) | < 1 s |
| Patch generation per finding | < 15 s |
| Patch validation per candidate | < 60 s (compilation + tests) |

---

## Phase Completion Status

| Phase | Status | Description |
|---|---|---|
| Phase 1 | Complete | Foundation — editor, hybrid analysis, MCP, Docker |
| Phase 2A | Complete | Static analysis platform — rule engine, IR, parsers, MCP |
| Phase 3A | Complete | Intelligence layer — UIR, symbols, types, CFG, DFG, IPA |
| Phase 3B.1 | Complete | Multi-agent runtime — DAG scheduler, message bus, state |
| Phase 3B.2 | Complete | Knowledge systems — semantic memory, repo graph, model router |
| Phase 3C.1 | Complete | Code intelligence engine — all program graph builders |
| Phase 3C.2 | Complete | Bug detection and reasoning — 15 modules, evidence/confidence/root cause |
| Phase 3D.1 | Complete | Autonomous patch generation — 14 modules, 104 tests |
| Phase 3D.2 | Complete | Autonomous patch validation — 20 modules, 132 total tests |

---

## License

MIT License — see `LICENSE` for details.
