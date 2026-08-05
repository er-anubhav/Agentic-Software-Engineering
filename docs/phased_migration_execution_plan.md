# Non-Breaking Phased Migration Execution Plan: V1 → V2 Enterprise Platform

**Document Status**: Operational CTO Execution Plan  
**Migration Strategy**: Strangler Fig Pattern (Zero Breaking Changes, 100% Backward Compatibility)  
**Objective**: Evolve the codebase step-by-step while keeping `python app.py` working at every single phase.  

---

## Migration Overview & Compatibility Matrix

```
       Phase 1: Hygiene & Pydantic Base (App Remains Functional)
                                │
                                ▼
       Phase 2: Docker Sandbox & Pytest Engine (App Remains Functional)
                                │
                                ▼
       Phase 3: Dynamic DAG & Temporal Engine (App Remains Functional)
                                │
                                ▼
       Phase 4: SCIP Code Graph & Qdrant Memory (App Remains Functional)
                                │
                                ▼
       Phase 5: Self-Healing & Next.js Control Panel (Flagship Complete)
```

---

## Detailed Migration Phase Specifications

---

### Phase 1: Hygiene, Bug Fixes, and Pydantic Structured Output Base

#### Objective
Fix existing baseline bugs in V1, standardize agent inheritance, and upgrade LLM JSON parsing to use Pydantic structured output while ensuring `python app.py` executes cleanly without errors.

#### Files Affected:
- [agents/base_agent.py](file:///home/anubhavtripathi/Documents/Projects/agentic-se/agents/base_agent.py)
- [agents/requirement_agent.py](file:///home/anubhavtripathi/Documents/Projects/agentic-se/agents/requirement_agent.py)
- [agents/architecture_agent.py](file:///home/anubhavtripathi/Documents/Projects/agentic-se/agents/architecture_agent.py)
- [orchestrator/workflow.py](file:///home/anubhavtripathi/Documents/Projects/agentic-se/orchestrator/workflow.py)

#### New Modules:
- `schemas/`: Directory for Pydantic structured response models (`RequirementSchema`, `ArchitectureSchema`, `DesignSchema`).

#### Refactored Modules:
- [agents/base_agent.py](file:///home/anubhavtripathi/Documents/Projects/agentic-se/agents/base_agent.py): Add `invoke_structured()` method utilizing Pydantic models.
- [agents/requirement_agent.py](file:///home/anubhavtripathi/Documents/Projects/agentic-se/agents/requirement_agent.py): Remove double LLM call bug on lines 34-38.
- [agents/architecture_agent.py](file:///home/anubhavtripathi/Documents/Projects/agentic-se/agents/architecture_agent.py): Inherit from `BaseAgent` and parse output into structured schema instead of raw text.
- [orchestrator/workflow.py](file:///home/anubhavtripathi/Documents/Projects/agentic-se/orchestrator/workflow.py): Replace hardcoded `C:\Projects\...` path with dynamic `os.getcwd()` detection.

#### Deleted Modules:
- None.

#### Risks:
- Ollama local model formatting variations on Pydantic JSON schemas. (Mitigation: Retain `tools/json_parser.py` regex fallback).

#### Success Criteria:
- `python app.py` completes execution in <50% of original time due to removing double LLM calls. Zero exceptions.

#### Demo After Completion:
- Run `python app.py` from CLI; verify structured console output without JSON decode errors or missing path exceptions.

---

### Phase 2: Isolated Docker Sandbox & Dynamic Pytest Engine

#### Objective
Safely isolate code execution from the host operating system by introducing an ephemeral Docker container pool, and replace static dummy test strings with dynamically generated Pytest test suites.

#### Files Affected:
- [agents/code_generation_agent.py](file:///home/anubhavtripathi/Documents/Projects/agentic-se/agents/code_generation_agent.py)
- [agents/test_generation_agent.py](file:///home/anubhavtripathi/Documents/Projects/agentic-se/agents/test_generation_agent.py)
- [agents/validation_agent.py](file:///home/anubhavtripathi/Documents/Projects/agentic-se/agents/validation_agent.py)

#### New Modules:
- `sandboxes/`: Ephemeral container manager module (`container_pool.py`, `grpc_runner.py`).

#### Refactored Modules:
- [agents/code_generation_agent.py](file:///home/anubhavtripathi/Documents/Projects/agentic-se/agents/code_generation_agent.py): Redirect file writing target from local host disk to Docker sandbox environment.
- [agents/test_generation_agent.py](file:///home/anubhavtripathi/Documents/Projects/agentic-se/agents/test_generation_agent.py): Replace hardcoded dummy strings (`assert True`) with an LLM prompt that reads OpenAPI routes and generates functional Pytest code.
- [agents/validation_agent.py](file:///home/anubhavtripathi/Documents/Projects/agentic-se/agents/validation_agent.py): Re-order execution logic to validate compiled code artifacts *after* generation inside the sandbox.

#### Deleted Modules:
- None.

#### Risks:
- Docker daemon availability on host OS. (Mitigation: Fallback to local isolated `/tmp` directory if Docker is unavailable).

#### Success Criteria:
- Generated FastAPI code compiles and passes Pytest inside a clean Docker sandbox.

#### Demo After Completion:
- Run `python app.py`. Observe console log showing: `[Sandbox] Provisioned container -> Executed pytest -> 3/3 tests PASSED`.

---

### Phase 3: Dynamic Task DAG Compiler & Temporal Orchestration Engine

#### Objective
Replace the rigid hardcoded 7-step execution list with a dynamic Directed Acyclic Graph (DAG) task engine capable of parallel step execution and runtime DAG branching.

#### Files Affected:
- [agents/execution_planner_agent.py](file:///home/anubhavtripathi/Documents/Projects/agentic-se/agents/execution_planner_agent.py)
- [orchestrator/execution_engine.py](file:///home/anubhavtripathi/Documents/Projects/agentic-se/orchestrator/execution_engine.py)
- [orchestrator/workflow.py](file:///home/anubhavtripathi/Documents/Projects/agentic-se/orchestrator/workflow.py)

#### New Modules:
- `orchestrator/dag_compiler.py`: Compiles high-level plans into dynamic Task DAG structures.
- `orchestrator/temporal_runner.py`: Async DAG state machine executor.

#### Refactored Modules:
- [agents/execution_planner_agent.py](file:///home/anubhavtripathi/Documents/Projects/agentic-se/agents/execution_planner_agent.py): Refactor from hardcoded list returner to `DAGCompiler` invoker.
- [orchestrator/execution_engine.py](file:///home/anubhavtripathi/Documents/Projects/agentic-se/orchestrator/execution_engine.py): Add topological sorting and parallel task worker support.

#### Deleted Modules:
- None (retain legacy linear runner as `--legacy` CLI flag option).

#### Risks:
- Dependency graph cycle deadlocks. (Mitigation: Run NetworkX cycle detection check prior to execution).

#### Success Criteria:
- Parallel execution of independent steps (e.g. DatabaseAgent and APIAgent execute simultaneously).

#### Demo After Completion:
- Run `python app.py`. Console displays animated task tree execution showing parallel task execution.

---

### Phase 4: Polyglot SCIP/Tree-sitter Code Knowledge Graph & Hybrid Memory

#### Objective
Replace single-threaded Python-only AST scans with polyglot Tree-sitter parsing and a Neo4j Code Knowledge Graph, supplemented by vector memory in Qdrant.

#### Files Affected:
- [agents/codebase_analysis_agent.py](file:///home/anubhavtripathi/Documents/Projects/agentic-se/agents/codebase_analysis_agent.py)

#### New Modules:
- `memory/`: Module holding Neo4j graph schemas (`graph_db.py`), Qdrant vector indexer (`vector_store.py`), and hybrid search ranker (`hybrid_memory.py`).

#### Refactored Modules:
- [agents/codebase_analysis_agent.py](file:///home/anubhavtripathi/Documents/Projects/agentic-se/agents/codebase_analysis_agent.py): Integrate Tree-sitter parser to extract multi-language call graphs into Neo4j.

#### Deleted Modules:
- None.

#### Risks:
- Database connection overhead for offline runs. (Mitigation: In-memory networkx graph fallback if Neo4j is offline).

#### Success Criteria:
- Sub-millisecond call graph queries for polyglot repositories (Python, TypeScript, Go).

#### Demo After Completion:
- Run codebase analysis on a multi-language repo. CLI outputs detailed multi-file call graph trees and cross-module import relations.

---

### Phase 5: Empirical Reflection Engine, Self-Healing Repair & Enterprise Control Panel

#### Objective
Implement automated traceback reflection, self-healing code diff repair, and expose a Next.js 14 Web Dashboard with real-time React Flow visual DAG rendering.

#### Files Affected:
- [app.py](file:///home/anubhavtripathi/Documents/Projects/agentic-se/app.py)

#### New Modules:
- `agents/reflection_agent.py`: Parses raw sandbox stack tracebacks into diagnostic error reports.
- `agents/repair_agent.py`: Generates targeted `git diff` patches to fix failed sandbox tests.
- `api/`: FastAPI REST/WebSocket API endpoints.
- `web/`: Next.js 14 web control dashboard.

#### Refactored Modules:
- [app.py](file:///home/anubhavtripathi/Documents/Projects/agentic-se/app.py): Expose CLI and web server initiation flags (`python app.py --serve`).

#### Deleted Modules:
- None.

#### Risks:
- Infinite self-healing repair loops on un-fixable bugs. (Mitigation: Enforce max 3 repair sub-DAG attempts per issue).

#### Success Criteria:
- Autonomous detection, diagnosis, and fix of injected codebase bugs without human intervention. Live visualization on Next.js UI.

#### Demo After Completion:
- Launch `python app.py --serve`. Open `http://localhost:3000`. Trigger a feature request. Watch real-time React Flow DAG execution nodes light up green, run tests in Docker, auto-repair a syntax error, and output passing code.

---

## Migration Phase Summary Matrix

| Phase | Core Objective | Key New / Refactored Modules | Backward Compatible? | Demo Verification |
| :---: | :--- | :--- | :---: | :--- |
| **Phase 1** | Hygiene & Pydantic Base | `agents/base_agent.py`, `schemas/` | YES | 2x speedup in `python app.py` |
| **Phase 2** | Sandbox & Dynamic Pytest | `sandboxes/`, `agents/test_generation_agent.py` | YES | Pytest passing inside Docker |
| **Phase 3** | Dynamic Task DAG Engine | `orchestrator/dag_compiler.py`, `temporal_runner.py` | YES | Parallel step DAG execution log |
| **Phase 4** | Code Knowledge Graph | `memory/graph_db.py`, `codebase_analysis_agent.py` | YES | SCIP call-graph query output |
| **Phase 5** | Self-Healing & Next.js UI | `agents/reflection_agent.py`, `api/`, `web/` | YES | Auto-repair bug & Live Web DAG UI |
