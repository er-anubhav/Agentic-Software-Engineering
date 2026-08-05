# ADR-001: 8-Layer Architecture & Automated Dependency Linter

## Status
Accepted

## Context
The autonomous software engineering platform evolved across 15 RFCs into a monolithic multi-agent system. Without clear architectural boundaries, modules suffered from circular imports, layer inversions, and high coupling.

## Decision
We enforce a strict 8-layer architecture hierarchy with a zero-upward-import rule enforced via an automated CI linter (`scripts/verify_layer_dependencies.py`).

### Layer Hierarchy
- Layer 0: Core Architecture (`src/core/`)
- Layer 1: Domain State & Data Models (`src/models/`)
- Layer 2: Persistence & Storage (`src/storage/`)
- Layer 3: Unified Inference Engine (`src/inference/`)
- Layer 4: Isolated Sandboxes & Distributed Runtime (`src/sandboxes/`)
- Layer 5: Domain Agents, Tools, Learning & Verification (`src/agents/`, `src/tools/`, `src/learning/`, `src/verification/`)
- Layer 6: Workflow Orchestration, Autonomy & Swarm (`src/orchestration/`)
- Layer 7: Platform API, Auth, Security, Tenant, GitHub, Evaluation, Observability (`src/platform/`, `src/github_engine/`, `src/evaluation/`, `src/observability/`)

## Consequences
- Upward layer imports are blocked at build time.
- Standardized package organization improves developer experience and maintainability.
