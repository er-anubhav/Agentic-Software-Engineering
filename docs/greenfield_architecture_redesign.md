# Repository Architecture Redesign
**Reviewer**: L8 Principal Engineer / Distinguished Systems Architect  
**Scope**: All 30 packages, 155 source files, 15 RFCs  
**Standard**: Maintainable for 10 years by a team that did not write it  

---

## Repository Score

| Dimension | Score | Notes |
|---|---|---|
| Structural clarity | 28/100 | 30 top-level packages, no visible layering |
| Ownership clarity | 30/100 | 1 confirmed cycle, 18 disconnected islands |
| Dependency hygiene | 35/100 | `agents ↔ orchestrator` cycle is a blocker |
| Separation of concerns | 25/100 | AI logic, infra, tooling, runtime all mixed at root level |
| Discoverability | 20/100 | No way to know where to add a new feature |
| Testability | 45/100 | Tests exist; they test in-memory scaffolding |
| Operational readiness | 10/100 | No deployment artifacts, no real infra |
| Production code quality | 25/100 | Core inference and auth are stubs |
| **OVERALL** | **27/100** | Not approved for continued feature investment |

---

## Phase 1 — Ownership Map

Classification of every current package. Legend:
- **PROD**: Ships to production. Critical path.
- **INFRA**: Infrastructure adapter. Not business logic.
- **TOOL**: Developer tooling, test utilities, benchmarks.
- **SCAFFOLD**: RFC implementation artifact. No production route.
- **DEAD**: Never imported by any production path, zero execution value.

| Package | Files | Primary Responsibility | Classification | Action |
|---|---|---|---|---|
| `agents/` | 16 | LLM-driven task execution units | PROD | KEEP → MOVE |
| `api/` | 1 | FastAPI HTTP entry point | PROD | KEEP → MOVE |
| `auth/` | 1 | Authentication (JWT, OIDC, API keys) | PROD | KEEP → STUB until real |
| `autonomy/` | 8 | Long-horizon goal lifecycle management | SCAFFOLD | MERGE into orchestration layer |
| `benchmarks/` | 1 | Hardcoded metric `print()` statements | DEAD | DELETE |
| `codebase_intelligence/` | 5 | Polyglot AST parsing, symbol indexing | PROD | KEEP → MOVE |
| `config/` | 1 | Ollama LLM instantiation | PROD | MERGE into `core/` |
| `core/` | 2 | Settings, DI container | PROD | KEEP → MOVE |
| `evaluation/` | 6 | Benchmark dataset, metrics, eval runner | TOOL | KEEP → MOVE |
| `fault_injection/` | 1 | Chaos test runner | TOOL | MOVE to `tests/` |
| `github_engine/` | 8 | GitHub App, webhooks, PR, workspace | PROD | KEEP → MOVE |
| `inference/` | 9 | Multi-provider LLM gateway | PROD | KEEP → REWRITE stubs |
| `infra/` | 4 | Redis, S3, secrets, DR (all in-memory stubs) | INFRA | KEEP → REWRITE all stubs |
| `learning/` | 8 | Self-improvement, experience store, prompt evo | SCAFFOLD | KEEP structure → disconnect from main path |
| `mcp_runtime/` | 6 | MCP tool registry, capabilities, permissions | SCAFFOLD | MERGE into tool layer |
| `memory/` | 4 | Vector store, graph DB, context engine | PROD | KEEP → MOVE |
| `models/` | 1 | `EngineeringState` God Object dataclass | PROD | REFACTOR → split into typed domain models |
| `observability/` | 5 | Tracer, metrics, profiler, exporter | PROD | KEEP → MOVE |
| `orchestrator/` | 4 | DAG compiler, workflow, execution engine | PROD | KEEP → SPLIT |
| `persistence/` | 1 | PostgreSQL store (in-memory stub) | INFRA | MOVE → REWRITE |
| `reasoning/` | 8 | Structured outputs, prompt lib, self-critique | SCAFFOLD | MERGE into AI layer |
| `runtime/` | 5 | Job queue (local JSON), scheduler, event bus | PROD | KEEP → REWRITE queue |
| `sandboxes/` | 3 | Docker + local code execution sandboxes | PROD | KEEP → MOVE |
| `schemas/` | 0 | Empty | DEAD | DELETE |
| `security/` | 1 | RBAC roles and permissions | PROD | MERGE with `auth/` |
| `stress/` | 1 | Load testing | TOOL | MOVE to `tests/` |
| `swarm/` | 9 | Multi-agent swarm (all pre-voted stubs) | SCAFFOLD | SCAFFOLD → MOVE, rewrite later |
| `tenant/` | 1 | Multi-tenant isolation (namespace string only) | PROD | MERGE with `auth/security/` |
| `tools/` | 1 | JSON parser utility | PROD | MERGE into `shared/` |
| `verification/` | 9 | Formal verification (mostly string-checks) | SCAFFOLD | KEEP structure → REWRITE internals |

---

## Phase 2 — Architectural Smells

### P0 — Immediate Blockers

**P0-01: `agents ↔ orchestrator` circular import**  
`agents/` imports from `orchestrator/` (for `WorkflowState`, `AgentRegistry`).  
`orchestrator/` imports from `agents/` (to register every agent).  
This makes the entire layer boundary meaningless. You cannot test either in isolation.  

**P0-02: 18 packages are isolated islands with no production import path**  
`inference/`, `reasoning/`, `swarm/`, `verification/`, `auth/`, `learning/`, `mcp_runtime/`, `infra/`, `persistence/`, `memory/`, `codebase_intelligence/`, `sandboxes/`, `security/`, `tenant/`, `config/`, `observability/`, `tools/`, `models/` — none of these are imported by the main execution path through `orchestrator/workflow.py`.  
Some are imported by `agents/`, which is correct. Most are imported only by `tests/`.

**P0-03: `config/` and `core/` are two separate packages with identical responsibility**  
`config/llm.py` creates the LLM. `core/config.py` holds `Settings`. `core/container.py` is the DI container that calls `config/llm.py`. Three locations for application bootstrap.

### P1 — High Impact, High Frequency

**P1-01: `EngineeringState` is a mutable God Object dataclass**  
It accumulates every field from every RFC. Every agent reads and writes the same bag. No contract enforced between producer and consumer agents. No type boundary at stage transitions.

**P1-02: `orchestrator/` owns both workflow coordination AND agent registry AND execution engine**  
These are three distinct responsibilities with three distinct change rates. `DAGCompiler` changes when task scheduling logic changes. `ExecutionEngine` changes when retry/abort logic changes. `AgentRegistry` changes when agents are added. All three share a package boundary.

**P1-03: `autonomy/` owns both goal state machine AND replanning logic AND policy evaluation**  
`GoalLifecycleManager`, `DynamicReplanner`, `ExecutionPolicyEngine`, `ObservationEngine`, `ProgressEngine` — five distinct subsystems inside one package with no sub-organization. `autonomy/` has more responsibility than `orchestrator/`.

**P1-04: `github_engine/` contains its own orchestrator**  
`github_engine/orchestrator.py` imports from `orchestrator/workflow.py` and wraps the entire pipeline. A `github_engine` module should be an integration adapter, not an orchestration owner. It violates the ports-and-adapters pattern.

**P1-05: Implementation history leaks into package names**  
`mcp_runtime/` is named after RFC-007. `swarm/` is named after RFC-014. `reasoning/` is named after RFC-010. These are not stable architecture boundaries. They are project history.

**P1-06: `learning/` imports nothing from production code**  
`SelfImprovementEngine` is a complete island. It has 8 files and imports only its own submodules. It has no connection to the execution lifecycle. There is no hook in `Workflow`, `ExecutionEngine`, or any agent that calls into `learning/` after a task completes.

**P1-07: Dual runtime paths**  
`orchestrator/execution_engine.py` (sequential, synchronous) and `runtime/scheduler.py` (parallel, async DAG execution) both claim to execute agents. They do not share an interface. `Workflow` uses `ExecutionEngine`. Nothing uses `DistributedScheduler` in production.

**P1-08: `swarm/` and `orchestrator/` both claim to own agent execution coordination**  
`FederatedSwarmEngine.execute_swarm_goal()` and `orchestrator/execution_engine.py` `ExecutionEngine.execute()` do the same job. Completely separate implementations with no shared interface.

### P2 — Medium Impact

**P2-01: Two LLM routing systems** — `inference/router.py::InferenceRouter` and `reasoning/token_budget.py::ModelRouter`. Identical responsibility, different packages, different interfaces.

**P2-02: Two retry systems** — `reasoning/retry_policy.py::ReasoningRetryPolicy` and `orchestrator/execution_engine.py::MAX_RETRIES = 1`.

**P2-03: Two governance/approval systems** — `swarm/governance.py::SwarmGovernanceEngine` and `agents/human_approval_agent.py::HumanApprovalAgent`. Both control whether execution proceeds.

**P2-04: Two cost tracking systems** — `inference/cost_tracker.py::InferenceCostTracker` and `reasoning/token_budget.py::TokenBudgetManager`.

**P2-05: `observability/` uses `print()` internally and is never connected to a real export target** — `tracer.py` stores spans in memory. `metrics.py` stores metrics in a list. Neither exports to Prometheus, OTLP, or any real sink.

**P2-06: `infra/` mixes infrastructure categories** — `redis_client.py` (runtime), `object_storage.py` (storage), `secrets_manager.py` (security), `disaster_recovery.py` (operations). Four completely different concerns in one package.

**P2-07: `sandboxes/` is imported by both `agents/` and `evaluation/`** — correct in principle, but creates a cross-cutting dependency that will generate a cycle the moment `evaluation/` needs to call an agent.

**P2-08: `persistence/postgres_store.py` is never imported by any other package** — confirmed island. Complete dead code in production terms.

### P3 — Low Impact, Cleanup

**P3-01**: `benchmarks/benchmark_suite.py` is 20 `print()` calls with hardcoded numbers. Not a benchmark. Not a module. A debug script left at top level.

**P3-02**: `schemas/` is an empty package with only `__init__.py`.

**P3-03**: `fault_injection/chaos_runner.py` belongs in `tests/`, not at the root source level.

**P3-04**: `stress/load_tester.py` belongs in `tests/`, not at the root source level.

**P3-05**: `generated_project/` is output that was accidentally committed to source.

**P3-06**: `Span.planner_version = "RFC-001"` — RFC names hardcoded into production telemetry. Implementation history in production artifacts.

---

## Phase 3 — New Repository Layout

Design principle: **Stable layers, directional dependencies, discoverable by role.**

```
agentic-se/
├── src/
│   ├── platform/          # Cross-cutting platform concerns (auth, tenant, config, RBAC)
│   ├── ai/                # All LLM, reasoning, and memory concerns
│   ├── agents/            # Specialized domain agents (LLM-driven workers)
│   ├── orchestration/     # Workflow DAG, execution, scheduling, autonomy
│   ├── knowledge/         # Codebase understanding and retrieval
│   ├── execution/         # Sandbox execution, verification, evaluation
│   ├── integrations/      # External system adapters (GitHub, MCP, cloud)
│   └── observability/     # Tracing, metrics, structured logging
├── infra/                 # Infrastructure clients (real implementations of adapters)
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── tools/                 # Dev tools: load tester, chaos runner, benchmark runner
├── scripts/               # One-shot scripts: migrations, seeders, benchmarks
└── docs/
    ├── architecture/
    ├── adr/               # Architecture Decision Records
    └── runbooks/
```

### Why each top-level directory exists

**`src/`**: All production Python source lives here. One import root. Prevents accidental top-level imports.

**`src/platform/`**: Owns the surface every other package touches but should not implement: auth, tenant isolation, RBAC, application config, DI container, secrets access. Changes here require security review. Changes rarely. No business logic.

**`src/ai/`**: Owns the LLM boundary. Inference gateway, provider adapters, structured output, routing, caching, token budget, prompt library, reasoning patterns. Everything that touches a model lives here. Nothing in `src/ai/` should know what a "GitHub issue" is.

**`src/agents/`**: Domain-specific workers. Each agent has a single `execute(context) -> result` contract. Agents import from `src/ai/` to make LLM calls. They import from `src/knowledge/` to retrieve context. They do not import from `src/orchestration/`.

**`src/orchestration/`**: Owns workflow coordination. DAG compiler, execution engine, scheduler, job queue, event bus, autonomy loop, replanning. Does not know what any specific agent does — it knows agent roles and dispatches by role name.

**`src/knowledge/`**: Owns codebase understanding. Polyglot parsing, symbol indexing, vector store, graph database, context engine, hybrid retrieval. Nothing here executes code or talks to GitHub.

**`src/execution/`**: Owns the "run and verify" surface. Docker/local sandboxes, verification engine, evaluation harness, deployment gate. Separated from `src/orchestration/` because execution policy can change independently of scheduling policy.

**`src/integrations/`**: Ports-and-adapters. Each subdirectory is an adapter to one external system. `github/`, `mcp/`, `swarm/`. These translate external events into internal domain types. They do not own business logic.

**`src/observability/`**: Owns telemetry. Tracer, metrics, exporter. Imported by every other layer. Exports to nothing by default — real sinks are configured in `infra/`.

**`infra/`**: Real infrastructure implementations. `redis.py`, `postgres.py`, `object_storage.py`, `secrets.py`. These are the actual adapters that touch external services. Separated from `src/` so tests can swap them with in-memory implementations without modifying source.

**`tests/`**: All tests. Flat `tests/` is an anti-pattern for a codebase this size. Structured into `unit/`, `integration/`, `e2e/` to allow different CI gates.

**`tools/`**: Load tester, chaos runner. Developer tooling. Never imported by `src/`.

**`scripts/`**: One-shot executables. Benchmark suite, database migrations, seeding. Never imported by `src/`.

---

## Phase 4 — Migration Table

Complete mapping for all 30 current packages.

| Current Location | New Location | Reason |
|---|---|---|
| `agents/base_agent.py` | `src/agents/base.py` | Protocol/ABC for all agents |
| `agents/requirement_agent.py` | `src/agents/domain/requirement.py` | Domain agent |
| `agents/planner_agent.py` | `src/agents/domain/planner.py` | Domain agent |
| `agents/architecture_agent.py` | `src/agents/domain/architecture.py` | Domain agent |
| `agents/design_agent.py` | `src/agents/domain/design.py` | Domain agent |
| `agents/execution_planner_agent.py` | `src/agents/domain/execution_planner.py` | Domain agent |
| `agents/codebase_analysis_agent.py` | `src/agents/domain/codebase_analysis.py` | Domain agent |
| `agents/code_generation_agent.py` | `src/agents/domain/code_generation.py` | Domain agent |
| `agents/repair_agent.py` | `src/agents/domain/repair.py` | Domain agent |
| `agents/test_generation_agent.py` | `src/agents/domain/test_generation.py` | Domain agent |
| `agents/validation_agent.py` | `src/agents/domain/validation.py` | Domain agent |
| `agents/database_agent.py` | `src/agents/domain/database.py` | Domain agent |
| `agents/api_agent.py` | `src/agents/domain/api.py` | Domain agent |
| `agents/summary_agent.py` | `src/agents/domain/summary.py` | Domain agent |
| `agents/human_approval_agent.py` | `src/agents/domain/human_approval.py` | Domain agent |
| `agents/reflection_agent.py` | `src/agents/domain/reflection.py` | Domain agent |
| `api/app_api.py` | `src/platform/api.py` | Entry point belongs to platform |
| `auth/oidc.py` | `src/platform/auth/provider.py` | Auth is a platform concern |
| `security/rbac.py` | `src/platform/auth/rbac.py` | RBAC is auth-adjacent |
| `tenant/tenant_manager.py` | `src/platform/tenant.py` | Multi-tenancy is a platform concern |
| `config/llm.py` | `src/platform/config/llm.py` | Config is a platform concern |
| `core/config.py` | `src/platform/config/settings.py` | Config is a platform concern |
| `core/container.py` | `src/platform/container.py` | DI container is a platform concern |
| `tools/json_parser.py` | `src/platform/utils/json_parser.py` | Shared utility |
| `inference/gateway.py` | `src/ai/inference/gateway.py` | LLM gateway |
| `inference/provider.py` | `src/ai/inference/provider.py` | Provider adapters |
| `inference/router.py` | `src/ai/inference/router.py` | Routing |
| `inference/cache.py` | `src/ai/inference/cache.py` | Prompt caching |
| `inference/rate_limiter.py` | `src/ai/inference/rate_limiter.py` | Rate limiting |
| `inference/fallback.py` | `src/ai/inference/fallback.py` | Failover |
| `inference/streaming.py` | `src/ai/inference/streaming.py` | Streaming |
| `inference/structured_output.py` | `src/ai/inference/structured_output.py` | Output parsing |
| `inference/cost_tracker.py` | `src/ai/inference/cost_tracker.py` | Cost accounting (SINGLE source) |
| `reasoning/structured_outputs.py` | `src/ai/reasoning/schemas.py` | Pydantic output schemas |
| `reasoning/prompt_library.py` | `src/ai/reasoning/prompt_library.py` | Prompt versioning |
| `reasoning/reasoning_engine.py` | `src/ai/reasoning/engine.py` | Reasoning coordinator |
| `reasoning/self_critique.py` | `src/ai/reasoning/critique.py` | Self-critique loop |
| `reasoning/reflection_memory.py` | `src/ai/reasoning/reflection.py` | Reasoning reflection |
| `reasoning/token_budget.py` | `DELETED — merge into inference/router.py` | Duplicate of InferenceRouter |
| `reasoning/retry_policy.py` | `DELETED — use infra retry decorator` | Duplicate policy |
| `reasoning/multi_agent_debate.py` | `src/ai/reasoning/debate.py` | Multi-agent consensus |
| `memory/vector_store.py` | `src/knowledge/store/vector.py` | Vector retrieval |
| `memory/graph_db.py` | `src/knowledge/store/graph.py` | Graph retrieval |
| `memory/context_engine.py` | `src/knowledge/retrieval/context_engine.py` | Context assembly |
| `memory/hybrid_memory.py` | `DELETED — context_engine.py IS hybrid memory` | Thin indirection |
| `codebase_intelligence/polyglot_parser.py` | `src/knowledge/indexing/parser.py` | AST parsing |
| `codebase_intelligence/scip_index.py` | `src/knowledge/indexing/scip.py` | SCIP code intelligence |
| `codebase_intelligence/symbol_search.py` | `src/knowledge/indexing/symbol_search.py` | Symbol lookup |
| `codebase_intelligence/semantic_chunker.py` | `src/knowledge/indexing/chunker.py` | Semantic chunking |
| `codebase_intelligence/health_metrics.py` | `src/knowledge/indexing/health.py` | Index health |
| `orchestrator/dag_compiler.py` | `src/orchestration/dag/compiler.py` | DAG compilation |
| `orchestrator/execution_engine.py` | `src/orchestration/engine/executor.py` | Sequential execution |
| `orchestrator/agent_registry.py` | `src/orchestration/engine/registry.py` | Agent lookup |
| `orchestrator/workflow.py` | `src/orchestration/engine/workflow.py` | Workflow orchestration |
| `runtime/scheduler.py` | `src/orchestration/scheduler/dag_scheduler.py` | Parallel DAG scheduling |
| `runtime/job_queue.py` | `src/orchestration/scheduler/job_queue.py` | Job queue |
| `runtime/worker.py` | `src/orchestration/scheduler/worker.py` | Worker pool |
| `runtime/event_bus.py` | `src/orchestration/events/bus.py` | Event bus |
| `runtime/checkpoint_manager.py` | `src/orchestration/state/checkpoint.py` | Checkpoint management |
| `autonomy/long_horizon_engine.py` | `src/orchestration/autonomy/engine.py` | Long-horizon control loop |
| `autonomy/goal_manager.py` | `src/orchestration/autonomy/goal.py` | Goal lifecycle |
| `autonomy/goal_validator.py` | `src/orchestration/autonomy/validator.py` | Goal validation |
| `autonomy/replanner.py` | `src/orchestration/autonomy/replanner.py` | Dynamic replanning |
| `autonomy/observation_engine.py` | `src/orchestration/autonomy/observer.py` | State observation |
| `autonomy/progress_engine.py` | `src/orchestration/autonomy/progress.py` | Progress tracking |
| `autonomy/policy_engine.py` | `src/orchestration/autonomy/policy.py` | Execution policy |
| `autonomy/human_gate.py` | `MERGE into src/agents/domain/human_approval.py` | Duplicate of HumanApprovalAgent |
| `sandboxes/docker_sandbox.py` | `src/execution/sandbox/docker.py` | Docker execution |
| `sandboxes/local_sandbox.py` | `src/execution/sandbox/local.py` | Local execution |
| `sandboxes/base_sandbox.py` | `src/execution/sandbox/base.py` | Sandbox interface |
| `verification/verification_engine.py` | `src/execution/verification/engine.py` | Verification orchestrator |
| `verification/contracts.py` | `src/execution/verification/contracts.py` | Contract specs |
| `verification/symbolic_executor.py` | `src/execution/verification/symbolic.py` | Symbolic analysis |
| `verification/semantic_validator.py` | `src/execution/verification/semantic.py` | Semantic diff |
| `verification/impact_analysis.py` | `src/execution/verification/impact.py` | Blast radius |
| `verification/invariant_engine.py` | `src/execution/verification/invariants.py` | Invariant checking |
| `verification/risk_engine.py` | `src/execution/verification/risk.py` | Risk scoring |
| `verification/deployment_gate.py` | `src/execution/verification/gate.py` | Deployment gate |
| `verification/rollback_engine.py` | `src/execution/verification/rollback.py` | Rollback planning |
| `evaluation/evaluation_runner.py` | `src/execution/evaluation/runner.py` | Benchmark runner |
| `evaluation/benchmark_dataset.py` | `src/execution/evaluation/dataset.py` | Benchmark dataset |
| `evaluation/metrics_engine.py` | `src/execution/evaluation/metrics.py` | Metric computation |
| `evaluation/experiment_tracker.py` | `src/execution/evaluation/tracker.py` | Experiment tracking |
| `evaluation/failure_classifier.py` | `src/execution/evaluation/classifier.py` | Failure analysis |
| `evaluation/replay_engine.py` | `src/execution/evaluation/replay.py` | Test replay |
| `github_engine/app_auth.py` | `src/integrations/github/auth.py` | GitHub App auth |
| `github_engine/webhook_gateway.py` | `src/integrations/github/webhook.py` | Webhook ingestion |
| `github_engine/workspace_manager.py` | `src/integrations/github/workspace.py` | Repo workspace |
| `github_engine/git_workflow.py` | `src/integrations/github/git.py` | Git operations |
| `github_engine/pr_engine.py` | `src/integrations/github/pr.py` | PR generation |
| `github_engine/review_loop.py` | `src/integrations/github/review.py` | Review feedback |
| `github_engine/github_mcp_tools.py` | `src/integrations/github/mcp_tools.py` | GitHub MCP tools |
| `github_engine/orchestrator.py` | `DELETED — logic absorbed into github/webhook.py + platform/api.py` | GitHub adapter must not own orchestration |
| `mcp_runtime/tool_registry.py` | `src/integrations/mcp/registry.py` | MCP tool registry |
| `mcp_runtime/capability_registry.py` | `src/integrations/mcp/capabilities.py` | Capability catalog |
| `mcp_runtime/permission_engine.py` | `src/integrations/mcp/permissions.py` | Tool permission model |
| `mcp_runtime/health_monitor.py` | `src/integrations/mcp/health.py` | Tool health |
| `mcp_runtime/tool_memory.py` | `src/integrations/mcp/memory.py` | Tool call memory |
| `mcp_runtime/agent_negotiator.py` | `src/integrations/mcp/negotiator.py` | Agent-tool negotiation |
| `swarm/swarm_engine.py` | `src/integrations/swarm/engine.py` | Swarm coordinator |
| `swarm/agent_runtime.py` | `src/integrations/swarm/agent_runtime.py` | Agent lifecycle |
| `swarm/hierarchical_orchestrator.py` | `src/integrations/swarm/hierarchy.py` | Hierarchical decomp |
| `swarm/task_marketplace.py` | `src/integrations/swarm/marketplace.py` | Task bidding |
| `swarm/blackboard.py` | `src/integrations/swarm/blackboard.py` | Shared memory |
| `swarm/message_bus.py` | `src/integrations/swarm/bus.py` | Message routing |
| `swarm/consensus.py` | `src/integrations/swarm/consensus.py` | Voting engine |
| `swarm/governance.py` | `src/integrations/swarm/governance.py` | Autonomy policy |
| `swarm/swarm_optimizer.py` | `src/integrations/swarm/optimizer.py` | Team composition |
| `learning/experience_store.py` | `src/ai/learning/experience.py` | Experience persistence |
| `learning/self_improvement_engine.py` | `src/ai/learning/engine.py` | Improvement orchestrator |
| `learning/prompt_evolution.py` | `src/ai/learning/prompt_evo.py` | Prompt A/B |
| `learning/pattern_mining.py` | `src/ai/learning/patterns.py` | Pattern extraction |
| `learning/planner_optimizer.py` | `src/ai/learning/planner_opt.py` | DAG heuristic optimization |
| `learning/retrieval_optimizer.py` | `src/ai/learning/retrieval_opt.py` | Retrieval weight tuning |
| `learning/model_optimizer.py` | `src/ai/learning/model_opt.py` | Model ranking |
| `learning/knowledge_distillation.py` | `src/ai/learning/distillation.py` | Knowledge playbooks |
| `observability/tracer.py` | `src/observability/tracing.py` | Distributed tracing |
| `observability/metrics.py` | `src/observability/metrics.py` | Metrics collection |
| `observability/exporters.py` | `src/observability/exporters.py` | OTLP/Prometheus export |
| `observability/profiler.py` | `src/observability/profiler.py` | Performance profiling |
| `observability/regression_detector.py` | `src/observability/regression.py` | Metric regression |
| `infra/redis_client.py` | `infra/redis.py` | Redis adapter |
| `infra/object_storage.py` | `infra/storage.py` | Object storage adapter |
| `infra/secrets_manager.py` | `infra/secrets.py` | Secrets adapter |
| `infra/disaster_recovery.py` | `docs/runbooks/disaster_recovery.md` | Not code — a runbook |
| `persistence/postgres_store.py` | `infra/postgres.py` | PostgreSQL adapter |
| `models/state.py` | **REFACTORED** — see note below | God object eliminated |

> **`models/state.py` refactoring note**: `EngineeringState` must be split into typed, stage-scoped transfer objects. Each stage transition in the workflow produces a typed result consumed by the next stage. `RequirementResult`, `PlanResult`, `AnalysisResult`, `ImplementationResult`, `ValidationResult`. The God Object is eliminated.

---

## Phase 5 — Delete List

| Item | Reason |
|---|---|
| `benchmarks/benchmark_suite.py` | Hardcoded `print()` statements. Zero measurement value. |
| `schemas/__init__.py` | Empty package with no purpose. |
| `generated_project/` | Committed test output. Add to `.gitignore`. |
| `infra/disaster_recovery.py` | Not code. Write `docs/runbooks/disaster_recovery.md`. |
| `memory/hybrid_memory.py` | Three-line wrapper that delegates to `ContextEngine`. Remove the indirection. |
| `reasoning/token_budget.py::TokenBudgetManager` | Duplicate of `inference/cost_tracker.py`. |
| `reasoning/retry_policy.py` | Duplicate of `orchestrator/execution_engine.py::MAX_RETRIES`. Consolidate into one retry decorator in `src/platform/`. |
| `github_engine/orchestrator.py` | An integration adapter must not own orchestration. Wire `webhook.py` directly to `orchestration/engine/workflow.py` via an event. |
| `autonomy/human_gate.py` | Duplicate of `agents/human_approval_agent.py`. |
| `swarm/swarm_engine.py::execute_swarm_goal()` method body | Pre-voted consensus, hardcoded bids. The method shell can stay; the body must be rewritten before the module has any value. |

---

## Phase 6 — Import Rules

### Layer Dependency DAG (directional, no upward imports)

```
  ┌─────────────────────────────────────┐
  │  tools/  scripts/                   │  ← developer tooling, never imported by src/
  └─────────────────────────────────────┘
                    │
  ┌─────────────────▼───────────────────┐
  │  src/platform/                      │  ← auth, config, DI, tenant, utils
  └──────┬──────────────────────────────┘
         │
  ┌──────▼──────────────────────────────┐
  │  src/observability/                 │  ← tracer, metrics. Imported by all layers.
  └──────┬──────────────────────────────┘
         │
  ┌──────▼──────────────────────────────┐
  │  infra/                             │  ← Redis, Postgres, S3, Secrets (real clients)
  └──────┬──────────────────────────────┘
         │
  ┌──────▼──────────────────────────────┐
  │  src/ai/                            │  ← inference gateway, reasoning, learning
  └──────┬──────────────────────────────┘
         │
  ┌──────▼──────────────────────────────┐
  │  src/knowledge/                     │  ← vector, graph, context engine, AST indexing
  └──────┬──────────────────────────────┘
         │
  ┌──────▼──────────────────────────────┐
  │  src/agents/                        │  ← domain agents (use ai/ and knowledge/)
  └──────┬──────────────────────────────┘
         │
  ┌──────▼──────────────────────────────┐
  │  src/execution/                     │  ← sandboxes, verification, evaluation
  └──────┬──────────────────────────────┘
         │
  ┌──────▼──────────────────────────────┐
  │  src/orchestration/                 │  ← DAG, workflow, scheduler, autonomy
  └──────┬──────────────────────────────┘
         │
  ┌──────▼──────────────────────────────┐
  │  src/integrations/                  │  ← github, mcp, swarm (adapters only)
  └──────┬──────────────────────────────┘
         │
  ┌──────▼──────────────────────────────┐
  │  src/platform/api.py                │  ← HTTP entry point, mounts integrations
  └─────────────────────────────────────┘
```

### Explicitly Forbidden Imports

```python
# FORBIDDEN: upward layer violations
src/ai/          →  src/orchestration/    # AI must not know about workflows
src/ai/          →  src/integrations/     # AI must not know about GitHub
src/knowledge/   →  src/agents/           # Knowledge must not drive agents
src/agents/      →  src/orchestration/    # Agents must not know the scheduler ← FIXES CURRENT CYCLE
src/execution/   →  src/orchestration/    # Execution must not know the scheduler
src/observability/ → src/ai/             # Telemetry must not call LLMs

# FORBIDDEN: infra leaking into business logic
src/agents/      →  infra/               # Agents get storage via platform/ DI
src/ai/          →  infra/               # AI layer uses platform/ injected deps
src/orchestration/ → infra/             # Orchestration uses platform/ injected deps

# FORBIDDEN: integration concerns in core layers
src/ai/          →  src/integrations/github/   # AI must not know about GitHub
src/knowledge/   →  src/integrations/          # Knowledge store is provider-agnostic
src/agents/      →  src/integrations/mcp/      # Agents use capabilities, not MCP directly

# PERMITTED cross-cutting imports (all layers may import these)
src/*/           →  src/observability/     # All layers may emit traces/metrics
src/*/           →  src/platform/config/   # All layers may read configuration
```

---

## Phase 7 — Final Repository Tree

```
agentic-se/
├── src/
│   ├── platform/
│   │   ├── __init__.py
│   │   ├── api.py                        # FastAPI application factory
│   │   ├── container.py                  # DI container (thread-safe, not singleton)
│   │   ├── tenant.py                     # Multi-tenant isolation and quota
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   ├── provider.py               # JWT, OIDC, OAuth, API key verification
│   │   │   ├── rbac.py                   # Role definitions and permission checks
│   │   │   └── middleware.py             # FastAPI auth middleware
│   │   ├── config/
│   │   │   ├── __init__.py
│   │   │   ├── settings.py               # Pydantic Settings (env-driven)
│   │   │   └── llm.py                    # LLM client factory
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── json_parser.py            # Robust LLM JSON parsing
│   │       └── retry.py                  # Shared retry decorator (ONE retry policy)
│   │
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── inference/
│   │   │   ├── __init__.py
│   │   │   ├── gateway.py                # UnifiedInferenceGateway (real HTTP calls)
│   │   │   ├── provider.py               # LLMProvider ABC + real provider impls
│   │   │   ├── router.py                 # Task → provider/model routing (ONE router)
│   │   │   ├── cache.py                  # SHA-256 prompt cache
│   │   │   ├── rate_limiter.py           # Token-bucket rate limiting
│   │   │   ├── fallback.py               # Failover cascade
│   │   │   ├── streaming.py              # SSE streaming
│   │   │   ├── structured_output.py      # Pydantic output parsing
│   │   │   └── cost_tracker.py           # Cost + token accounting (ONE tracker)
│   │   ├── reasoning/
│   │   │   ├── __init__.py
│   │   │   ├── engine.py                 # UnifiedReasoningEngine
│   │   │   ├── schemas.py                # Pydantic structured output types
│   │   │   ├── prompt_library.py         # Versioned prompt templates
│   │   │   ├── critique.py               # Self-critique loop
│   │   │   ├── debate.py                 # Multi-agent deliberation
│   │   │   └── reflection.py             # Reasoning trajectory memory
│   │   └── learning/
│   │       ├── __init__.py
│   │       ├── engine.py                 # SelfImprovementEngine
│   │       ├── experience.py             # Engineering experience store
│   │       ├── prompt_evo.py             # Prompt A/B tournament
│   │       ├── patterns.py               # Pattern mining
│   │       ├── planner_opt.py            # DAG heuristic optimizer
│   │       ├── retrieval_opt.py          # Retrieval weight tuner
│   │       ├── model_opt.py              # Model performance ranker
│   │       └── distillation.py           # Knowledge playbook distillation
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py                       # BaseAgent ABC: execute(ctx) -> result
│   │   ├── context.py                    # AgentContext: typed input for agents
│   │   └── domain/
│   │       ├── __init__.py
│   │       ├── requirement.py
│   │       ├── planner.py
│   │       ├── architecture.py
│   │       ├── design.py
│   │       ├── execution_planner.py
│   │       ├── codebase_analysis.py
│   │       ├── code_generation.py
│   │       ├── repair.py
│   │       ├── test_generation.py
│   │       ├── validation.py
│   │       ├── database.py
│   │       ├── api.py
│   │       ├── summary.py
│   │       ├── human_approval.py
│   │       └── reflection.py
│   │
│   ├── knowledge/
│   │   ├── __init__.py
│   │   ├── indexing/
│   │   │   ├── __init__.py
│   │   │   ├── parser.py                 # Polyglot AST parser
│   │   │   ├── scip.py                   # SCIP code intelligence index
│   │   │   ├── symbol_search.py          # Symbol resolution
│   │   │   ├── chunker.py                # Semantic chunking
│   │   │   └── health.py                 # Index health metrics
│   │   ├── store/
│   │   │   ├── __init__.py
│   │   │   ├── vector.py                 # Qdrant vector store (repo_id namespaced)
│   │   │   └── graph.py                  # Neo4j graph store (repo_id namespaced)
│   │   └── retrieval/
│   │       ├── __init__.py
│   │       └── context_engine.py         # 9-stage RRF context assembly
│   │
│   ├── execution/
│   │   ├── __init__.py
│   │   ├── sandbox/
│   │   │   ├── __init__.py
│   │   │   ├── base.py                   # Sandbox ABC
│   │   │   ├── docker.py                 # Docker isolation sandbox
│   │   │   └── local.py                  # Local fallback sandbox
│   │   ├── verification/
│   │   │   ├── __init__.py
│   │   │   ├── engine.py                 # UnifiedVerificationEngine
│   │   │   ├── contracts.py              # Pre/post conditions
│   │   │   ├── symbolic.py               # AST-based dead code and path analysis
│   │   │   ├── semantic.py               # Signature and behavior diff
│   │   │   ├── impact.py                 # Blast radius analysis
│   │   │   ├── invariants.py             # Invariant checking
│   │   │   ├── risk.py                   # Risk scoring
│   │   │   ├── gate.py                   # Deployment approval gate
│   │   │   └── rollback.py               # Rollback plan generation
│   │   └── evaluation/
│   │       ├── __init__.py
│   │       ├── runner.py                 # Benchmark runner
│   │       ├── dataset.py                # Benchmark task definitions
│   │       ├── metrics.py                # Metric computation
│   │       ├── tracker.py                # Experiment tracking
│   │       ├── classifier.py             # Failure mode classification
│   │       └── replay.py                 # Test case replay
│   │
│   ├── orchestration/
│   │   ├── __init__.py
│   │   ├── dag/
│   │   │   ├── __init__.py
│   │   │   └── compiler.py               # DAG compilation and cycle detection
│   │   ├── engine/
│   │   │   ├── __init__.py
│   │   │   ├── executor.py               # Sequential execution engine
│   │   │   ├── registry.py               # Agent role registry (no circular dep)
│   │   │   └── workflow.py               # Workflow pipeline coordinator
│   │   ├── scheduler/
│   │   │   ├── __init__.py
│   │   │   ├── dag_scheduler.py          # Parallel DAG scheduler
│   │   │   ├── job_queue.py              # Durable job queue (Redis-backed)
│   │   │   └── worker.py                 # Worker pool
│   │   ├── events/
│   │   │   ├── __init__.py
│   │   │   └── bus.py                    # Internal event bus
│   │   ├── state/
│   │   │   ├── __init__.py
│   │   │   ├── checkpoint.py             # Workflow checkpoint manager
│   │   │   └── models.py                 # Typed stage transition models (replaces EngineeringState)
│   │   └── autonomy/
│   │       ├── __init__.py
│   │       ├── engine.py                 # Long-horizon control loop
│   │       ├── goal.py                   # Goal lifecycle state machine
│   │       ├── validator.py              # Goal completion validation
│   │       ├── replanner.py              # Dynamic DAG replanning
│   │       ├── observer.py               # Repository state observation
│   │       ├── progress.py               # Progress tracking
│   │       └── policy.py                 # Execution policy (abort/continue/retry)
│   │
│   ├── integrations/
│   │   ├── __init__.py
│   │   ├── github/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py                   # GitHub App JWT auth
│   │   │   ├── webhook.py                # Webhook event → domain event translation
│   │   │   ├── workspace.py              # Repository clone and workspace management
│   │   │   ├── git.py                    # Git branch, commit operations
│   │   │   ├── pr.py                     # Pull request creation (real API calls)
│   │   │   ├── review.py                 # Review comment feedback loop
│   │   │   └── mcp_tools.py              # GitHub-specific MCP tools
│   │   ├── mcp/
│   │   │   ├── __init__.py
│   │   │   ├── registry.py               # MCP tool registry
│   │   │   ├── capabilities.py           # Agent capability catalog
│   │   │   ├── permissions.py            # Tool permission model
│   │   │   ├── health.py                 # Tool health monitoring
│   │   │   ├── memory.py                 # Tool call history
│   │   │   └── negotiator.py             # Agent-to-agent subtask negotiation
│   │   └── swarm/
│   │       ├── __init__.py
│   │       ├── engine.py                 # FederatedSwarmEngine
│   │       ├── agent_runtime.py          # Agent lifecycle manager
│   │       ├── hierarchy.py              # Executive → Coordinator → Specialist
│   │       ├── marketplace.py            # Task bidding system
│   │       ├── blackboard.py             # Shared collaborative memory
│   │       ├── bus.py                    # Typed inter-agent messages
│   │       ├── consensus.py              # Weighted voting engine
│   │       ├── governance.py             # Autonomy and safety policy
│   │       └── optimizer.py              # Team composition optimizer
│   │
│   └── observability/
│       ├── __init__.py
│       ├── tracing.py                    # OpenTelemetry span/trace management
│       ├── metrics.py                    # Prometheus-compatible metric collection
│       ├── exporters.py                  # OTLP, Prometheus exporters
│       ├── profiler.py                   # Performance profiling
│       └── regression.py                # Metric regression detection
│
├── infra/
│   ├── __init__.py
│   ├── redis.py                          # Real redis-py client adapter
│   ├── postgres.py                       # Real asyncpg/psycopg2 adapter
│   ├── storage.py                        # Real boto3/google-cloud-storage adapter
│   └── secrets.py                        # Real hvac/boto3/google-cloud-secret adapter
│
├── tests/
│   ├── unit/
│   │   ├── ai/
│   │   ├── agents/
│   │   ├── knowledge/
│   │   ├── execution/
│   │   ├── orchestration/
│   │   └── integrations/
│   ├── integration/
│   │   ├── test_workflow_pipeline.py
│   │   ├── test_github_webhook.py
│   │   ├── test_vector_graph_retrieval.py
│   │   └── test_inference_gateway.py
│   └── e2e/
│       ├── test_issue_to_pr.py
│       └── test_long_horizon_goal.py
│
├── tools/
│   ├── load_tester.py
│   ├── chaos_runner.py
│   └── dev_seed.py                       # Seed test data for local development
│
├── scripts/
│   ├── benchmark.py                      # Real benchmark runner (measured timings)
│   ├── migrate_db.py                     # Alembic migration runner
│   └── seed_experience_store.py          # Seed learning experience data
│
├── docs/
│   ├── architecture/
│   │   ├── overview.md
│   │   ├── layer_diagram.png
│   │   └── dependency_rules.md
│   ├── adr/
│   │   ├── ADR-001-layered-architecture.md
│   │   ├── ADR-002-single-inference-gateway.md
│   │   └── ADR-003-eliminate-god-object.md
│   └── runbooks/
│       ├── disaster_recovery.md
│       ├── incident_response.md
│       └── deployment.md
│
├── app.py                                # Entry point: `uvicorn app:app`
├── pyproject.toml                        # Single build config (replaces requirements.txt)
├── alembic.ini                           # Database migration config
└── .gitignore                            # Must include generated_project/
```

---

## 90-Day Convergence Roadmap

### Month 1 — Structural Integrity (Weeks 1–4)

**Week 1**: Break the `agents ↔ orchestrator` cycle.
- Extract `AgentRegistry` from `orchestrator/` into its own module.
- Remove all imports of `orchestrator/` from `agents/`. Agents receive state as typed input, not the orchestrator.
- Verify: `python -c "from agents.base_agent import BaseAgent"` must not trigger any orchestrator import.

**Week 2**: Wire `UnifiedInferenceGateway` to real provider SDKs.
- Install `openai`, `anthropic`, `google-generativeai`.
- Replace all 7 `f"[ProviderName Response]..."` stubs with real API calls.
- Delete `reasoning/token_budget.py`. Merge routing into `inference/router.py`.
- Target: `inference/` passes integration tests against real endpoints with test API keys.

**Week 3**: Fix authentication.
- Install `python-jose[cryptography]` for JWT.
- Implement real JWT signature verification in `auth/oidc.py`.
- `authenticate_jwt()` must reject an invalid token. If it can't, it's not auth.
- Target: `test_enterprise_platform.py::test_jwt_authentication` must fail with an invalid token.

**Week 4**: Create the new directory structure.
- Create `src/` with new layer layout.
- Move packages according to migration table above (mechanical move only, no logic changes).
- Update all import paths.
- Verify: 132 tests still pass.

### Month 2 — Reconnect the Islands (Weeks 5–8)

**Week 5**: Connect `ContextEngine` to agent prompt construction.
- `CodeGenerationAgent` and `RepairAgent` must call `ContextEngine.query()` before building their LLM prompt.
- No agent should build a prompt from `EngineeringState` fields alone.

**Week 6**: Replace `EngineeringState` God Object.
- Define `RequirementResult`, `PlanResult`, `AnalysisResult`, `ImplementationResult`, `ValidationResult`.
- Each agent produces one typed result consumed by the next stage.
- `EngineeringState` becomes a thin session context holding only ID, repository_path, and trace_id.

**Week 7**: Replace `DurableJobQueue` local JSON with Redis.
- Use `infra/redis.py` (real `redis-py`) as the backing store.
- Use `rq` or `celery` for the worker model. Or: raw Redis list with `BRPOP`.
- Target: Two simultaneous workflow requests do not corrupt queue state.

**Week 8**: Connect `learning/` to the workflow lifecycle.
- After `ValidationAgent` completes, emit an experience to `ExperienceStore`.
- After `RepairAgent` completes (success or failure), record the repair trajectory.
- Verify: `ExperienceStore` has records after a real workflow run.

### Month 3 — Verification and Benchmarking (Weeks 9–12)

**Week 9**: Rewrite `SymbolicExecutor` using `ast`.
- Use `ast.parse()` + `ast.walk()` to detect unreachable code, dead branches, and impossible conditions.
- Target: detects `if sys.version_info < (2, 0):` as dead code on Python 3.

**Week 10**: Rewrite `SemanticValidator` using `ast`.
- Full function signature comparison: parameter names, types, return annotation, added/removed params.
- Detect method removal, class removal, module-level renames.
- Target: correctly identifies a breaking change when a function signature changes.

**Week 11**: Connect `UnifiedVerificationEngine` into `RepairAgent`.
- After generating a patch, `RepairAgent` must call `verify_patch()`.
- If `gate_passed == False`, the repair attempt fails and triggers retry.

**Week 12**: Write real benchmarks.
- `scripts/benchmark.py`: measure wall-clock time from webhook to PR object on a real task.
- Measure: context retrieval latency, LLM call latency, verification latency.
- Output: structured JSON to `benchmark_results/YYYYMMDD.json`. Not `print()`.

---

*This is a 10-year architecture. Every directory name should be obvious to an engineer who has never seen this codebase. Every import should be obvious from the layer it belongs to. Every deletion should have happened before the second RFC was merged.*
