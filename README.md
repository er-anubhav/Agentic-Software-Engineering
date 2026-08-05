# 🤖 Agentic Software Engineering Platform

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Architecture Governance](https://img.shields.io/badge/Architecture-AST%20Enforced-emerald.svg)](scripts/verify_layer_dependencies.py)
[![Test Pass Rate](https://img.shields.io/badge/Tests-144%2F144%20Passed-success.svg)](tests)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An enterprise-grade, autonomous **Agentic Software Engineering Platform** designed for high-throughput repository intelligence, surgical git-diff code repair, dynamic task DAG orchestration, and formal AST verification. Built on Tactical Domain-Driven Design (DDD), Hexagonal Architecture (Ports & Adapters), and Executable Architecture Governance.

---

## 🏛️ System Architecture

The platform strictly enforces a 6-layer Domain-Driven Design (DDD) & Hexagonal Architecture:

```
┌────────────────────────────────────────────────────────────────────────┐
│ Layer 5: Interfaces & Platform API (FastAPI, WebSockets, CLI)          │
├────────────────────────────────────────────────────────────────────────┤
│ Layer 4: Application Orchestration, Swarm, Agents & Event Bus          │
├────────────────────────────────────────────────────────────────────────┤
│ Layer 3: Infrastructure Adapters (Inference Gateway, Storage, Sandboxes)│
├────────────────────────────────────────────────────────────────────────┤
│ Layer 2: Domain Layer (Entities, Aggregates, Value Objects, Events)   │
├────────────────────────────────────────────────────────────────────────┤
│ Layer 1: Application Bootstrapper (Service Graph Assembly)             │
├────────────────────────────────────────────────────────────────────────┤
│ Layer 0: Core Configuration & Type-Safe Dependency Injection Container │
└────────────────────────────────────────────────────────────────────────┘
```

---

## ✨ Key Features

- 🧠 **Intelligent Task DAG Orchestrator**: Generates, validates, and compiles cycle-free task execution graphs with topological parallel execution phases.
- 🔧 **Surgical Git-Diff Repair Engine**: Executes precise line-by-line patch generation and AST validation for fault repair without code erosion.
- ⚡ **Unified Inference Gateway**: Multi-provider LLM gateway supporting OpenAI, Anthropic, Gemini, and Ollama with automatic failover, health checks, and SHA-256 prompt caching.
- 💾 **Hexagonal SQLite WAL Persistence**: ACID-compliant relational persistence with WAL journal mode, connection health-checking, and transaction management.
- 📊 **High-Scale Performance Benchmark Suite**: Built-in benchmark harness with automated CI performance regression tracking against saved baselines.
- 🛡️ **Executable Architecture Governance**: AST-parsed layer dependency linter integrated directly into pytest (`tests/test_architecture.py`) to prevent architectural drift.

---

## 🚀 Quickstart Guide

### 1. Prerequisites & Installation

Ensure you have Python 3.12+ installed:

```bash
# Clone the repository
git clone https://github.com/er-anubhav/agentic-software-engineering.git
cd agentic-software-engineering

# Set up virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

Copy the example environment configuration:

```bash
cp .env.example .env
```

Update your `.env` file with your API keys:

```env
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
GEMINI_API_KEY=your_gemini_api_key
OLLAMA_BASE_URL=http://localhost:11434
SQLITE_DB_PATH=platform.db
```

---

## 🧪 Testing & Architecture Governance

Run the complete test suite across all 26 test files:

```bash
# Run pytest test suite (144 / 144 tests)
.venv/bin/python3 -m pytest tests/ -v

# Run AST-based layer dependency linter
python3 scripts/verify_layer_dependencies.py

# Run high-scale performance benchmark suite with CI regression gate
.venv/bin/python3 scripts/benchmark_suite.py
```

---

## 📊 Performance Metrics & Benchmark Output

| Benchmark Workload | Scale / Complexity | Latency / Throughput |
| :--- | :--- | :--- |
| **Polyglot Codebase Indexing** | 1,000 Classes / 2,000 Method Symbols | **54.66 ms** |
| **Task DAG Compilation** | 200 Interconnected Nodes (20 runs) | **568.56 ms** |
| **Surgical Hunk Repair Patch** | 100 Iterations | **0.86 ms** |
| **Prompt Cache Hit Ratio** | 100 Repeated Requests | **100.0%** |
| **Memory Footprint (RSS)** | Idle Execution | **25.0 MB** |

---

## 📜 Project Structure

```
agentic-se/
├── src/
│   ├── core/                    # Config & Type-Safe DI Container Locator
│   ├── bootstrap/               # Application Bootstrapper & Service Graph Assembly
│   ├── domain/                  # Tactical DDD Entities, Value Objects, Aggregates, Ports, Events
│   │   ├── entities/            # Core Domain Entities (Requirement, JobRecord)
│   │   ├── value_objects/       # Value Objects (ConfidenceScore, QualityScore)
│   │   ├── aggregates/          # Aggregate Roots (TaskDAG, DAGNode)
│   │   ├── services/            # Repository Ports (JobCommandRepositoryPort, JobQueryRepositoryPort)
│   │   └── events/              # Domain Event Bus & Domain Events
│   ├── infrastructure/          # Inference Gateway, Persistence Adapters, Sandboxes, Tracing
│   │   ├── inference/           # Unified Inference Gateway & Provider Adapters
│   │   ├── storage/             # SQLiteAdapter (WAL mode), Memory, Parsers
│   │   └── observability/       # Structured Logging & OpenTelemetry Tracing
│   ├── application/             # Domain Agents, Orchestrators, Learning & Tools
│   └── interfaces/              # FastAPI App, Controllers, WebSockets, CLI
├── scripts/
│   ├── verify_layer_dependencies.py  # AST-based layer dependency linter
│   └── benchmark_suite.py            # High-scale performance benchmark suite
├── tests/                       # 26 Unit, Integration, and Architecture Test Suites
└── docs/                        # ADRs, Contributing & Architecture Guides
```

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
