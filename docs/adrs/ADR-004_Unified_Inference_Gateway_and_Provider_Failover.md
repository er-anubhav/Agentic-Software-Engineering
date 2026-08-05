# ADR-004: Unified Inference Gateway & Automatic Provider Failover

## Status
Accepted

## Context
Multiple LLM integrations (OpenAI, Anthropic, Gemini, OpenRouter, Ollama, vLLM, Azure OpenAI) led to duplicated HTTP error handling, token accounting, and fallback logic across agents.

## Decision
Centralize all LLM interactions in `UnifiedInferenceGateway` (`src/inference/gateway.py`) with:
- `BaseSDKProvider` adapter framework.
- SHA-256 prompt response caching (`PromptCache`).
- Token bucket provider rate limiting (`ProviderRateLimiter`).
- Failover cascade to local Ollama fallback.
- Cost, latency, and token accounting.

## Consequences
- Single entry point for all LLM calls.
- Automated resilient fallback during cloud API outages.
