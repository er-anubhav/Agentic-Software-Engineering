# 🏗️ Architecture & Developer Contribution Guide

Welcome to the **Agentic Software Engineering Platform** codebase! This document provides a comprehensive high-level guide to understanding the architecture, layer boundaries, dependency rules, and developer workflows.

---

## 🏛️ 1. The 8-Layer Architecture

The codebase enforces a strict 8-layer architecture hierarchy. Higher layers may import lower layers, but **lower layers NEVER import higher layers**.

```
Layer 7: Platform API, Auth, Security, Tenant, GitHub, Evaluation, Observability
   ↓
Layer 6: Workflow Orchestration, Autonomy, Swarm Platform
   ↓
Layer 5: Domain Agents, MCP Tools, Continuous Learning, Formal Verification
   ↓
Layer 4: Sandboxes (Docker, Local), Distributed Scheduler & Workers
   ↓
Layer 3: Unified Inference Gateway, Provider Adapters, Reasoning Engine
   ↓
Layer 2: Storage & Persistence (SQLiteStore, VectorMemoryStore, GraphDB)
   ↓
Layer 1: Domain State Models, Task DAG Models, Pydantic Schemas
   ↓
Layer 0: Core Configuration, Dependency Injection Container
```

### Layer Dependency Verification
Before submitting any code changes or Pull Requests, run the layer dependency linter:

```bash
python3 scripts/verify_layer_dependencies.py
```

Any upward layer import violation will trigger a non-zero exit code and fail CI validation.

---

## 🔌 2. Application Bootstrap & Dependency Injection

- **`src/core/container.py`**: Thread-safe service locator holding singleton services.
- **`src/platform/bootstrap.py`**: The application bootstrapper. It reads configuration settings, instantiates storage engines and LLM gateways, and registers them into the `Container`.

### Resolving a Service
```python
from src.core.container import get_container
from src.storage.persistence import RelationalStore

container = get_container()
store = container.resolve(RelationalStore)
```

---

## 💾 3. Relational Persistence & Repositories

Database persistence is decoupled using the **Repository Pattern**:
- `RelationalStore` (`src/storage/persistence/base_store.py`): Abstract persistence contract.
- `SQLiteStore` (`src/storage/persistence/sqlite_store.py`): WAL-mode embedded SQLite relational database with thread-local connection management and transaction support (`with store.transaction():`).
- `JobRepository` & `CheckpointRepository` (`src/storage/persistence/repositories.py`): High-level domain interfaces querying database tables directly.

---

## 🤖 4. Inference Gateway & Failover Cascade

All LLM calls are routed through `UnifiedInferenceGateway` (`src/inference/gateway.py`):
- **Providers**: Supports OpenAI, Anthropic, Gemini, OpenRouter, Ollama, vLLM, Azure OpenAI.
- **Caching**: Prompt responses are cached via SHA-256 prompt hashing (`PromptCache`).
- **Failover**: Cloud provider failures automatically trigger local Ollama fallback.
- **Cost & Latency Accounting**: Measures prompt/completion tokens, cost in USD, and latency in milliseconds.

---

## 🧪 5. Testing & Quality Verification

Run the automated test suite using pytest:

```bash
.venv/bin/python3 -m pytest tests/ -v
```

### Key Test Categories
- `tests/test_core.py`: Core configuration & DI container.
- `tests/test_memory.py`: Vector memory, graph database, and SQLite persistence.
- `tests/test_inference_gateway.py`: Gateway, provider failover, and streaming.
- `tests/test_sandboxes.py`: Local and Docker sandbox execution.
- `tests/test_intelligent_planner.py`: DAG compilation and phase sorting.
- `tests/test_swarm_platform.py`: Swarm consensus, bidding, and dynamic agent spawning.
- `tests/test_verification_engine.py`: Contracts, symbolic execution, and safety gates.
