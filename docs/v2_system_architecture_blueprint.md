# Enterprise System Architecture Blueprint: Version 2 Platform

**Document Status**: Final Architecture Specification  
**Author**: Principal Software Architect & AI Systems Researcher  
**Target Capability**: 100+ Parallel Agent Micro-workers, 10M+ LOC Enterprise Polyglot Codebases, Concurrent Multi-Tenant Repositories  

---

## 1. Executive Strategy & Architectural Postulates

Version 1 served as an initial single-threaded Proof-of-Concept (PoC). Version 2 is designed from first principles to fulfill the mandate of building a research-grade, enterprise-scale **Agentic Software Engineering Platform**.

### Fundamental Architectural Postulates
1. **Zero Shared Mutable State**: Agents do not mutate local memory state directly. State transitions are event-driven, immutable, and persisted via an event backbone (NATS JetStream).
2. **DAG Orchestration Over Linear Chains**: Monolithic linear step pipelines are replaced by a dynamic Directed Acyclic Graph (DAG) task engine with runtime re-planning and parallel branch execution.
3. **Strict Container Sandbox Isolation**: All untrusted LLM code execution, static checks, unit testing, and compilation occur within isolated, ephemeral micro-sandboxes (Docker/E2B/Firecracker microVMs).
4. **Hybrid Polyglot Memory**: Code analysis combines structural code graphs (Neo4j for call graphs and dependencies), semantic vector indices (Qdrant), and structured working context (Redis).
5. **Empirical Execution Feedback Loops**: Reflection and bug-fixing are driven strictly by actual runtime execution feedback (stack tracebacks, linter output, build logs) rather than prompt iteration.

---

## 2. Deep Deconstruction of V1 Limitations

Every subsystem in V1 was empirically analyzed against enterprise production standards:

```
+------------------+----------------------------------+--------------------------------------+
| V1 Subsystem     | V1 Implementation (Source Code)  | Enterprise V2 Architectural Solution |
+------------------+----------------------------------+--------------------------------------+
| Orchestration    | Hardcoded 7-step list in         | Distributed Task DAG Orchestrator    |
|                  | ExecutionPlannerAgent.py         | (Temporal / Custom DAG Engine)       |
+------------------+----------------------------------+--------------------------------------+
| State Management | In-memory EngineeringState       | Distributed Event Store (NATS)       |
|                  | Python dataclass                 | + Immutable CQRS Blackboard          |
+------------------+----------------------------------+--------------------------------------+
| Repo Intelligence| Local os.walk + ast.walk         | Multi-language Tree-sitter + SCIP    |
|                  | Python scanner                   | + Neo4j Code Knowledge Graph         |
+------------------+----------------------------------+--------------------------------------+
| Code Execution   | Overwrites host disk files in    | Isolated Ephemeral Container Pool    |
|                  | generated_project/               | (Docker / E2B MicroVM Sandboxes)     |
+------------------+----------------------------------+--------------------------------------+
| Memory           | Raw prompt string concatenation; | Hybrid Memory Engine (Qdrant Vector  |
|                  | zero long-term storage           | + Neo4j Graph + Redis State)         |
+------------------+----------------------------------+--------------------------------------+
| Repair & Retry   | Re-runs validator agent without  | Empirical Failure Diagnosis Agent    |
|                  | re-invoking generator agents     | + Automated Repair Task Sub-DAG      |
+------------------+----------------------------------+--------------------------------------+
| Output Parsing   | String replace of ```json fences | Schema-validated Pydantic / Outlines |
|                  | in tools/json_parser.py          | structured JSON enforcement          |
+------------------+----------------------------------+--------------------------------------+
| Observability    | CLI print() statements           | OpenTelemetry Traces + Prometheus    |
|                  |                                  | + SWE-bench Evaluation Suite         |
+------------------+----------------------------------+--------------------------------------+
```

---

## 3. High-Level ASCII System Architecture

```
+---------------------------------------------------------------------------------------------------+
|                                    INGRESS & GATEWAY LAYER                                        |
|  - GitHub Webhook Ingress (Issues, PRs, Comments)                                                 |
|  - REST / GraphQL Enterprise API Gateway                                                          |
|  - Developer CLI & IDE LSP/MCP Plugin                                                             |
+-------------------------------------------------+-------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
|                                     EVENT BACKBONE (NATS)                                         |
|  - CloudEvents Message Bus  |  Persistent Message Stream  |  Distributed Pub/Sub              |
+--------+----------------------------------------+----------------------------------------+--------+
         |                                        |                                        |
         v                                        v                                        v
+------------------------+      +----------------------------------+      +-------------------------+
|  REPO INTELLIGENCE     |      |      DAG TASK ORCHESTRATOR       |      | HYBRID MEMORY ENGINE    |
|  - Tree-sitter AST     |      |  - Dynamic Task DAG Compiler     |      | - Neo4j Code Graph      |
|  - SCIP/LSP Indexer    |<---->|  - Graph Execution State Machine |<---->| - Qdrant Vector Store   |
|  - Git Diff Engine     |      |  - Task Scheduler & Dispatcher   |      | - Redis Working Context |
+------------------------+      +-----------------+----------------+      +-------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
|                                  AGENT WORKER MESH (KUBERNETES)                                   |
|  - Requirement Analysis Agent  |  Architecture Agent    |  Security Audit Agent                    |
|  - Database Engineering Agent  |  API Design Agent      |  Code Generation Agent                   |
|  - Refactoring & Lint Agent    |  Test Generator Agent  |  Diagnosis & Repair Agent                |
+-------------------------------------------------+-------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
|                                AUTONOMOUS ISOLATED SANDBOX POOL                                   |
|  - Ephemeral Docker / E2B Container Pool                                                          |
|  - Sub-100ms Pre-warmed Container Allocation                                                      |
|  - gRPC Sandbox Runner (Executes Build, Pytest, Static Analysis, Benchmarks)                      |
|  - Real-time Log & Traceback Telemetry Streamer                                                   |
+---------------------------------------------------------------------------------------------------+
```

---

## 4. Subsystem Detailed Specifications

### 4.1 Subsystem 1: Repository Intelligence Service (RIS)
- **Architecture**: Asynchronous ingestion worker pipeline.
- **Components**:
  1. **Tree-sitter Parser Engine**: Extracts AST nodes for Python, TypeScript, Go, Java, and C++.
  2. **SCIP Indexer**: Generates precise cross-file definition and reference symbols.
  3. **Code Knowledge Graph Builder**: Projects AST and SCIP data into a Neo4j graph database.

#### Knowledge Graph Schema:
- **Nodes**: `(:File)`, `(:Package)`, `(:Class)`, `(:Function)`, `(:Interface)`, `(:DatabaseTable)`
- **Relationships**: 
  - `(:File)-[:CONTAINS]->(:Class)`
  - `(:Class)-[:IMPLEMENTS]->(:Interface)`
  - `(:Function)-[:CALLS]->(:Function)`
  - `(:Function)-[:MUTATES_TABLE]->(:DatabaseTable)`

### 4.2 Subsystem 2: Dynamic Task DAG Compiler & Orchestrator (DOS)
- **Architecture**: Graph-based state machine driven by Temporal / Custom DAG orchestrator.
- **Workflow**:
  1. Takes a high-level requirement or GitHub issue.
  2. Compiles an initial **Task Graph DAG** where nodes represent Agent execution steps and directed edges represent data/contract dependencies.
  3. Supports **Dynamic Node Branching**: If an agent discovers unexpected database dependencies during execution, it dynamically injects new prerequisite task nodes into the active DAG.

```
                  ┌──────────────────────────────┐
                  │ Requirement Decomposition    │
                  └──────────────┬───────────────┘
                                 │
                   ┌─────────────┴─────────────┐
                   ▼                           ▼
      ┌──────────────────────────┐┌──────────────────────────┐
      │ DB Schema Migration DAG  ││ OpenAPI Specification    │
      └────────────┬─────────────┘└────────────┬─────────────┘
                   │                           │
                   └─────────────┬─────────────┘
                                 ▼
                    ┌──────────────────────────┐
                    │ Architecture Contract    │
                    └────────────┬─────────────┘
                                 │
          ┌──────────────────────┼──────────────────────┐
          ▼                      ▼                      ▼
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│ Service Module A │   │ Service Module B │   │ Service Module C │
└─────────┬────────┘   └─────────┬────────┘   └─────────┬────────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 ▼
                    ┌──────────────────────────┐
                    │ Sandbox Build & Pytest   │
                    └────────────┬─────────────┘
                                 │
                   ┌─────────────┴─────────────┐
                   ▼                           ▼
             (Status: PASS)              (Status: FAIL)
                   │                           │
                   ▼                           ▼
        ┌──────────────────┐        ┌──────────────────────┐
        │  Git Pull Request│        │ Self-Healing Repair  │
        │   Synthesis      │        │      Sub-DAG         │
        └──────────────────┘        └──────────────────────┘
```

### 4.3 Subsystem 3: Ephemeral Sandbox Isolation Engine (ASES)
- **Environment**: Isolated Linux containers running inside an unprivileged sandbox pool (Docker / E2B microVMs).
- **Control Interface**: gRPC daemon running inside the sandbox listening for commands:
  - `ExecuteBuild()`: Compiles binary or installs requirements.
  - `ExecuteTests()`: Runs test suites (`pytest`, `jest`, `go test`).
  - `CaptureTraceback()`: Extracts structured stack tracebacks and diagnostic failure codes on crash.

### 4.4 Subsystem 4: Self-Healing & Reflection Loop (SHRL)
- **Failure Trigger**: Any failed test or syntax error in the sandbox emits an `ExecutionFailedEvent`.
- **Diagnosis & Repair Contract**:
  1. **Diagnosis Agent** receives:
     - Target source file diff.
     - Raw stderr execution log.
     - Stack traceback frame lines.
     - Context from Code Knowledge Graph for referenced functions.
  2. Diagnosis Agent identifies exact root cause (e.g. `TypeError: expected str, got NoneType at service.py:L42`).
  3. Spawns a targeted **Repair Task** with minimal diff patch constraints.
  4. Applies patch in sandbox and re-verifies.

---

## 5. Architectural Decision Records (ADRs)

### ADR-001: Dynamic DAG Orchestration vs. Hardcoded Pipelines
- **Status**: Approved.
- **Context**: V1 used a rigid 7-step linear sequence. Complex real-world software tasks require parallel execution, branching, and dynamic re-planning based on feedback.
- **Decision**: Adopt a dynamic Task DAG compiler where nodes represent specialized Agent contracts and edges enforce artifact dependencies.

### ADR-002: SCIP Code Knowledge Graph vs. Vector-Only Retrieval
- **Status**: Approved.
- **Context**: Vector embedding search alone misses exact code references (e.g., "Find all callers of method `calculate_tax` across 50 microservices").
- **Decision**: Combine Tree-sitter + SCIP symbol indexing in Neo4j for structural queries, supplemented by Qdrant for semantic search.

### ADR-003: Isolated Micro-Sandboxes vs. Host OS Execution
- **Status**: Approved.
- **Context**: Executing LLM-generated code directly on host OS is a critical security vulnerability and pollutes local environments.
- **Decision**: All execution must occur within ephemeral, network-isolated container sandboxes streaming telemetry over gRPC.

---

## 6. Verification & Evaluation Strategy

1. **Benchmark Evaluation**: Automated evaluation against **SWE-bench Lite / Full** benchmarks to measure real-world repository bug resolution rates.
2. **Quality Gates**:
   - 100% automated test pass rate in isolated sandbox.
   - Zero static analysis linter errors (flake8, ruff, mypy, tsc).
   - Zero security policy violations (Bandit, Trivy vulnerability scans).

---

## 7. Deliverable Summary

This blueprint completes the **Version 2 System Architecture Specification** for an enterprise-grade, autonomous, multi-agent software engineering platform.
