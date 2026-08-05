# Agentic Software Engineering System

A production-oriented **Multi-Agent Software Engineering Platform** that transforms high-level software requirements into reviewable engineering deliverables through autonomous workflow orchestration, validation, and human-in-the-loop approval.

---

## Assignment Coverage

| Capability | Status |
|------------|--------|
| Requirement Understanding | ✅ |
| Task Decomposition | ✅ |
| Brownfield Codebase Analysis | ✅ |
| Multi-Agent Workflow Orchestration | ✅ |
| Engineering Output Generation | ✅ |
| Validation & Risk Control | ✅ |
| Human-in-the-Loop Approval | ✅ |
| Automated Test Generation | ✅ |
| Engineering Summary | ✅ |

---

# Overview

This project demonstrates an **Agentic Software Engineering System** capable of automating the Software Development Life Cycle (SDLC) from software requirements to production-ready engineering deliverables.

Unlike a traditional chatbot, the solution decomposes software engineering work into specialized autonomous agents that collaboratively execute the complete engineering lifecycle.

The platform supports:

- Greenfield development
- Brownfield enhancements
- Architecture generation
- Engineering planning
- Production code generation
- API generation
- Database schema generation
- Validation
- Human approval
- Test generation
- Engineering documentation

---

# Architecture

The following diagram illustrates the overall multi-agent architecture.

![Architecture](docs/architecture.png)

---

# Engineering Workflow

The engineering workflow demonstrates how requirements are transformed into production-ready engineering outputs.

![Workflow](docs/workflow.png)

---

# Sample Execution

Example execution of the complete engineering workflow.

![Execution](docs/terminal-output.png)

---

# Key Features

- Multi-Agent Engineering Workflow
- Requirement Understanding
- Functional & Non-Functional Requirement Extraction
- Ambiguity Detection
- Risk Identification
- Task Decomposition
- Brownfield Repository Analysis
- Architecture Generation
- High-Level Design Generation
- Database Schema Generation
- REST API Generation
- Production Code Generation
- Validation & Engineering Guardrails
- Human Approval Workflow
- Automated Test Generation
- Engineering Summary Generation

---

# System Architecture

```
User Requirement
        │
        ▼
 RequirementAgent
        │
        ▼
 PlannerAgent
        │
        ▼
CodebaseAnalysisAgent
        │
        ▼
 ArchitectureAgent
        │
        ▼
   DesignAgent
        │
        ▼
ExecutionPlannerAgent
        │
        ▼
 ExecutionEngine
        │
 ┌──────┼───────────────┐
 ▼      ▼               ▼
Database API       Validation
Agent    Agent         Agent
              │
              ▼
      HumanApprovalAgent
              │
      Approved?
      Yes │   No
          ▼
CodeGenerationAgent
          │
          ▼
TestGenerationAgent
          │
          ▼
SummaryAgent
```

---

# Project Structure

```
agentic-software-engineering/

├── agents/
│   ├── requirement_agent.py
│   ├── planner_agent.py
│   ├── codebase_analysis_agent.py
│   ├── architecture_agent.py
│   ├── design_agent.py
│   ├── execution_planner_agent.py
│   ├── execution_engine.py
│   ├── database_agent.py
│   ├── api_agent.py
│   ├── validation_agent.py
│   ├── human_approval_agent.py
│   ├── code_generation_agent.py
│   ├── test_generation_agent.py
│   └── summary_agent.py
│
├── orchestrator/
│   └── workflow.py
│
├── models/
│   └── state.py
│
├── docs/
│   ├── architecture.png
│   ├── workflow.png
│   ├── terminal-output.png
│   └── architecture.mmd
│
├── generated_project/
│
├── requirements.txt
├── README.md
└── app.py
```

---

# Agent Responsibilities

## RequirementAgent

Responsible for understanding business requirements.

Produces:

- Functional Requirements
- Non-Functional Requirements
- Assumptions
- Ambiguities
- Risks

---

## PlannerAgent

Transforms requirements into structured engineering tasks.

Produces:

- Engineering Tasks
- Execution Order

---

## CodebaseAnalysisAgent

Supports Greenfield and Brownfield engineering.

Analyzes:

- Repository structure
- Python modules
- Dependencies
- Services
- Classes
- Functions
- APIs
- Database models

---

## ArchitectureAgent

Generates:

- System Architecture
- Components
- Data Flow
- Communication Model

---

## DesignAgent

Produces:

- Module Design
- API Design
- Database Design

---

## ExecutionPlannerAgent

Creates the engineering execution plan.

---

## ExecutionEngine

Coordinates the execution of all engineering agents.

Capabilities:

- Multi-step orchestration
- Dependency management
- Validation checkpoints
- Retry support
- Human approval
- Shared engineering state

---

## DatabaseAgent

Generates:

- SQL Schema
- SQLAlchemy Models

---

## APIAgent

Generates:

- OpenAPI Specification
- REST API Routes

---

## ValidationAgent

Performs engineering validation.

Checks include:

- Generated artifacts
- Requirement coverage
- Architecture consistency
- Database schema
- REST API completeness
- Production readiness
- Risk identification

---

## HumanApprovalAgent

Implements controlled autonomy.

Requires explicit human approval before production code generation.

---

## CodeGenerationAgent

Generates production-ready application code.

---

## TestGenerationAgent

Generates:

- Unit Tests
- Integration Test Scaffolding

---

## SummaryAgent

Produces:

- Implementation Plan
- Validation Summary
- Generated Artifacts
- Risks
- Assumptions
- Limitations

---

# Engineering Workflow

1. Requirement Understanding
2. Requirement Analysis
3. Task Decomposition
4. Brownfield Analysis
5. Architecture Design
6. Solution Design
7. Execution Planning
8. Database Generation
9. API Generation
10. Validation
11. Human Approval
12. Code Generation
13. Test Generation
14. Engineering Summary

---

# Controlled Autonomy

The platform follows a **Human-in-the-Loop (HITL)** execution model.

```
Validation

↓

Human Approval

↓

Approved?

├── Yes → Continue Execution

└── No → Abort Execution
```

This ensures production code is generated only after successful validation and explicit human approval.

---

# Validation Strategy

The Validation Agent verifies:

- Generated artifacts
- Architecture consistency
- Requirement traceability
- Database schema
- REST API completeness
- Project structure
- Production readiness
- Brownfield analysis
- Engineering risks

---

# Generated Deliverables

## Production Code

- main.py
- routes.py
- service.py
- repository.py
- models.py
- config.py

---

## API Contracts

- OpenAPI Specification

---

## Database

- SQL Schema
- SQLAlchemy Models

---

## Tests

- Unit Tests
- Integration Test Scaffolding

---

## Documentation

- Engineering Summary
- README

---

# Example Scenarios

## Greenfield

```
Build a scalable URL Shortener service with APIs, persistence, and analytics.
```

Generated:

- Requirements
- Architecture
- Database
- APIs
- Production Code
- Tests
- Validation Report
- Engineering Summary

---

## Brownfield

```
Add rate limiting to the existing URL Shortener APIs.
```

Demonstrates:

- Repository Analysis
- Impact Analysis
- Module Identification
- Validation

---

## Ambiguous Requirement

```
Improve the performance of the URL Shortener service.
```

The Requirement Agent identifies ambiguities before engineering execution.

Examples:

- Which APIs?
- Database latency?
- Throughput?
- Response time?
- Cache strategy?

---

# Technology Stack

- Python 3.11
- Ollama
- LangChain
- FastAPI
- SQLAlchemy
- Pydantic
- PyYAML

---

# Setup Instructions

## Clone Repository

```bash
git clone https://github.com/dprabhakar047/agentic-software-engineering.git

cd agentic-software-engineering
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Start Ollama

```bash
ollama serve
```

---

## Download Model

```bash
ollama pull llama3
```

---

## Run

```bash
python app.py
```

---

# Mandatory Assignment Use Case

```
Build a scalable URL Shortener service with APIs, persistence, and analytics.
```

The system demonstrates:

- Requirement Analysis
- Planning
- Architecture Design
- Database Generation
- API Generation
- Validation
- Human Approval
- Production Code Generation
- Test Generation
- Engineering Summary

---

# Future Enhancements

- Parallel Agent Execution
- Agent Memory
- Retrieval-Augmented Generation (RAG)
- CI/CD Integration
- GitHub Integration
- Security Scanning
- Performance Profiling
- Multi-language Code Generation
- Architecture Visualization
- Deployment Automation

---

# Known Limitations

- Prototype implementation intended for interview demonstration
- Parallel workflow execution is not yet implemented
- Advanced impact analysis can be further enhanced
- CI/CD integration is outside the current scope

---

# Author

**Prabhakar Daggula**

Senior Engineering Leader | Platform Engineering | Site Reliability Engineering | DevOps | Cloud Engineering | AI-Powered Engineering

This project was developed as part of a Software Engineering Architecture interview assignment to demonstrate autonomous multi-agent orchestration across the Software Development Life Cycle (SDLC).