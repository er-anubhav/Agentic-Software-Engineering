# ADR-002: Thread-Safe Dependency Injection & Application Bootstrap

## Status
Accepted

## Context
Direct service construction inside singleton classes created hidden dependencies and coupled infrastructure to service resolution logic.

## Decision
We separate service registration from service construction:
1. `Container` (`src/core/container.py`): Pure thread-safe service locator with double-checked locking (`threading.Lock()`).
2. `bootstrap_system()` (`src/platform/bootstrap.py`): Reads configuration, constructs providers and storage engines, and registers them into the `Container` at application startup.

## Consequences
- Service construction is explicit and isolated to the bootstrap sequence.
- High test isolation: tests can mock services via `container.register()` or `container.reset_instance()`.
