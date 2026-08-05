"""
tests/test_inference_gateway.py

Tests for the UnifiedInferenceGateway, routing, caching, structured output,
cost tracking, and rate limiting.

Network isolation
-----------------
Tests that exercise individual providers mock the underlying HTTP client
(``httpx.post`` for Ollama, SDK clients for cloud providers) so the suite
runs without a live Ollama instance or cloud API keys.  Integration tests
against real endpoints belong in ``tests/integration/``.
"""
import unittest
from unittest.mock import patch, MagicMock

from pydantic import BaseModel

from src.infrastructure.inference.provider import (
    LLMResponse,
    OllamaProvider,
    OpenAIProvider,
    AnthropicProvider,
    GeminiProvider,
)
from src.infrastructure.inference.cache import PromptCache
from src.infrastructure.inference.cost_tracker import InferenceCostTracker
from src.infrastructure.inference.rate_limiter import ProviderRateLimiter
from src.infrastructure.inference.fallback import FailoverEngine
from src.infrastructure.inference.router import InferenceRouter
from src.infrastructure.inference.structured_output import StructuredOutputParser
from src.infrastructure.inference.streaming import InferenceStreamer
from src.infrastructure.inference.gateway import UnifiedInferenceGateway


class SampleStructuredOutput(BaseModel):
    status: str = "SUCCESS"
    reasoning: str = "Parsed cleanly."
    score: float = 98.0


# ---------------------------------------------------------------------------
# Shared mock response factory
# ---------------------------------------------------------------------------

def _mock_ollama_response(text: str = "mocked response") -> dict:
    return {
        "response": text,
        "prompt_eval_count": 10,
        "eval_count": 5,
        "done": True,
    }


class TestInferenceRouter(unittest.TestCase):

    def test_provider_selection_and_routing(self):
        prov, model = InferenceRouter.route("retrieval")
        self.assertEqual(prov, "gemini")

    def test_repair_routing(self):
        prov_repair, model_repair = InferenceRouter.route("repair")
        self.assertEqual(prov_repair, "anthropic")

    def test_default_routing(self):
        prov, model = InferenceRouter.route("unknown_domain")
        self.assertEqual(prov, "openai")


class TestPromptCache(unittest.TestCase):

    def test_cache_miss_then_hit(self):
        cache = PromptCache()
        prompt = "Explain quantum computing in 2 sentences."
        model = "gpt-4o"
        self.assertIsNone(cache.get(prompt, model))

        resp = LLMResponse(text="Quantum computers use qubits.", model=model, provider="openai")
        cache.set(prompt, model, resp)

        cached = cache.get(prompt, model)
        self.assertIsNotNone(cached)
        self.assertEqual(cached.text, resp.text)

    def test_different_prompts_dont_collide(self):
        cache = PromptCache()
        resp = LLMResponse(text="Answer A", model="gpt-4o", provider="openai")
        cache.set("prompt A", "gpt-4o", resp)
        self.assertIsNone(cache.get("prompt B", "gpt-4o"))


class TestGatewayCaching(unittest.TestCase):
    """Gateway caching without network calls — FailoverEngine is mocked."""

    def setUp(self):
        UnifiedInferenceGateway._instance = None

    def tearDown(self):
        UnifiedInferenceGateway._instance = None

    def test_generation_and_cache_hits(self):
        gateway = UnifiedInferenceGateway()
        # Replace FailoverEngine with a mock that returns a deterministic response
        mock_response = LLMResponse(
            text="Quantum computers use qubits.",
            prompt_tokens=10, completion_tokens=5,
            model="qwen2.5-coder:7b", provider="ollama",
            cost_usd=0.0, latency_ms=50.0,
        )
        gateway.failover_engine = MagicMock()
        gateway.failover_engine.execute_with_failover.return_value = mock_response

        prompt = "Explain quantum computing in 2 sentences."

        resp1 = gateway.generate(prompt=prompt, task_domain="planning", use_cache=True)
        self.assertFalse(resp1.cache_hit)

        resp2 = gateway.generate(prompt=prompt, task_domain="planning", use_cache=True)
        self.assertTrue(resp2.cache_hit)
        self.assertEqual(resp1.text, resp2.text)
        # Failover should only be called once (cache hit on second request)
        gateway.failover_engine.execute_with_failover.assert_called_once()


class TestOllamaProvider(unittest.TestCase):
    """OllamaProvider with mocked HTTP."""

    @patch("src.infrastructure.inference.provider.httpx")
    def test_generate_success(self, mock_httpx):
        mock_post = MagicMock()
        mock_post.raise_for_status = MagicMock()
        mock_post.json.return_value = _mock_ollama_response("Hello from Ollama!")
        mock_httpx.post.return_value = mock_post

        provider = OllamaProvider()
        resp = provider.generate("Hello", model="qwen2.5-coder:7b")
        self.assertEqual(resp.text, "Hello from Ollama!")
        self.assertEqual(resp.provider, "ollama")

    @patch("src.infrastructure.inference.provider.httpx")
    def test_health_check_success(self, mock_httpx):
        mock_get = MagicMock()
        mock_get.status_code = 200
        mock_httpx.get.return_value = mock_get
        provider = OllamaProvider()
        self.assertTrue(provider.health())

    @patch("src.infrastructure.inference.provider.httpx")
    def test_health_check_failure(self, mock_httpx):
        mock_httpx.get.side_effect = Exception("Connection refused")
        provider = OllamaProvider()
        self.assertFalse(provider.health())


class TestFailoverEngine(unittest.TestCase):
    """FailoverEngine with mocked providers."""

    def _make_provider(self, name: str, healthy: bool = True, response_text: str = "ok") -> MagicMock:
        p = MagicMock()
        p.name = name
        p.health.return_value = healthy
        p.generate.return_value = LLMResponse(
            text=response_text,
            prompt_tokens=10,
            completion_tokens=5,
            model="test-model",
            provider=name,
            cost_usd=0.001,
            latency_ms=50.0,
        )
        return p

    def test_preferred_provider_used_when_healthy(self):
        openai_p = self._make_provider("openai", healthy=True, response_text="openai response")
        anthropic_p = self._make_provider("anthropic", healthy=True, response_text="anthropic response")
        failover = FailoverEngine({"openai": openai_p, "anthropic": anthropic_p})
        resp = failover.execute_with_failover(prompt="Test prompt", preferred_provider="openai")
        self.assertEqual(resp.provider, "openai")
        self.assertEqual(resp.text, "openai response")

    def test_failover_to_next_when_primary_unhealthy(self):
        openai_p = self._make_provider("openai", healthy=False)
        anthropic_p = self._make_provider("anthropic", healthy=True, response_text="fallback used")
        failover = FailoverEngine({"openai": openai_p, "anthropic": anthropic_p})
        resp = failover.execute_with_failover(prompt="Test", preferred_provider="openai")
        self.assertEqual(resp.provider, "anthropic")

    def test_failover_raises_when_all_fail(self):
        openai_p = self._make_provider("openai", healthy=False)
        failover = FailoverEngine({"openai": openai_p})
        with self.assertRaises(RuntimeError):
            failover.execute_with_failover(prompt="Test", preferred_provider="openai")


class TestStructuredOutputParser(unittest.TestCase):

    def test_structured_output_parsing(self):
        json_text = '{"status": "SUCCESS", "reasoning": "Structured response", "score": 99.5}'
        parsed = StructuredOutputParser.parse_or_fallback(json_text, SampleStructuredOutput)
        self.assertEqual(parsed.status, "SUCCESS")
        self.assertEqual(parsed.score, 99.5)

    def test_fallback_on_malformed_output(self):
        fallback_parsed = StructuredOutputParser.parse_or_fallback("invalid json text", SampleStructuredOutput)
        self.assertEqual(fallback_parsed.status, "SUCCESS")


class TestInferenceStreamer(unittest.TestCase):

    @patch("src.infrastructure.inference.provider.httpx")
    def test_streaming_completion(self, mock_httpx):
        # Mock stream context manager
        mock_response = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        import json
        mock_response.iter_lines.return_value = [
            json.dumps({"response": "Hello", "done": False}),
            json.dumps({"response": " world", "done": True}),
        ]
        mock_httpx.stream.return_value = mock_response

        prov = OllamaProvider()
        chunks = list(InferenceStreamer.stream_completion(prov, "Stream prompt"))
        self.assertGreater(len(chunks), 0)


class TestCostAccounting(unittest.TestCase):

    def test_cost_accounting(self):
        cost_tracker = InferenceCostTracker()
        resp = LLMResponse(text="Test", prompt_tokens=100, completion_tokens=50, cost_usd=0.002, latency_ms=100.0)
        metrics = cost_tracker.record_request(resp, trace_id="tr_123")
        self.assertEqual(metrics.trace_id, "tr_123")

        summary = cost_tracker.get_summary()
        self.assertEqual(summary["total_requests"], 1)
        self.assertAlmostEqual(summary["total_cost_usd"], 0.002)


class TestRateLimiting(unittest.TestCase):

    def test_rate_limiting_allows_initial_request(self):
        limiter = ProviderRateLimiter()
        self.assertTrue(limiter.check_and_increment("openai"))


class TestEmbeddingsGateway(unittest.TestCase):

    def setUp(self):
        UnifiedInferenceGateway._instance = None

    def tearDown(self):
        UnifiedInferenceGateway._instance = None

    def test_embeddings_gateway(self):
        """Embeddings via OllamaProvider fallback (mocked fastembed)."""
        gateway = UnifiedInferenceGateway()
        prov_mock = MagicMock()
        prov_mock.embed.return_value = [[0.1, 0.2, 0.3, 0.4], [0.5, 0.6, 0.7, 0.8]]
        gateway.providers["openai"] = prov_mock

        embeds = gateway.embed(["vector text 1", "vector text 2"], provider_name="openai")
        self.assertEqual(len(embeds), 2)
        self.assertEqual(len(embeds[0]), 4)


if __name__ == "__main__":
    unittest.main()
