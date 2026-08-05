# ADR-005: Hierarchical Swarm Orchestration & Dynamic DAG Planning

## Status
Accepted

## Context
Linear pipeline execution failed on complex engineering tasks requiring iterative feedback, database schema changes, and concurrent sub-task execution.

## Decision
1. Use `TaskDAG` and `DAGCompiler` (`src/orchestration/dag_compiler.py`) to compile tasks into topological execution phases.
2. Implement Hierarchical Swarm Orchestration (Executive → Coordinator → Specialist → Worker) with distributed task marketplaces, weighted voting consensus, and event-driven blackboard memory.

## Consequences
- Efficient parallel execution of independent task DAG nodes.
- Fault-tolerant multi-agent consensus for critical architecture decisions.
