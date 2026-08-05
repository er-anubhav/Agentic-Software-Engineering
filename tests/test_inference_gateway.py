import unittest
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field

from inference.provider import (
    LLMResponse,
    OpenAIProvider,
    AnthropicProvider,
    GeminiProvider,
    OllamaProvider
)
from inference.cache import PromptCache
from inference.cost_tracker import InferenceCostTracker
from inference.rate_limiter import ProviderRateLimiter
from inference.fallback import FailoverEngine
from inference.router import InferenceRouter
from inference.structured_output import StructuredOutputParser
from inference.streaming import InferenceStreamer
from inference.gateway import UnifiedInferenceGateway


class SampleStructuredOutput(BaseModel):
    status: str = "SUCCESS"
    reasoning: str = "Parsed cleanly."
    score: float = 98.0


class TestInferenceGateway(unittest.TestCase):

    def setUp(self):
        self.gateway = UnifiedInferenceGateway.get_instance()
        self.cache = PromptCache()
        self.cost_tracker = InferenceCostTracker()
        self.rate_limiter = ProviderRateLimiter()

    def test_provider_selection_and_routing(self):
        prov, model = InferenceRouter.route("retrieval")
        self.assertEqual(prov, "gemini")

        prov_repair, model_repair = InferenceRouter.route("repair")
        self.assertEqual(prov_repair, "anthropic")

    def test_generation_and_cache_hits(self):
        prompt = "Explain quantum computing in 2 sentences."
        resp1 = self.gateway.generate(prompt=prompt, task_domain="planning", use_cache=True)
        self.assertFalse(resp1.cache_hit)

        resp2 = self.gateway.generate(prompt=prompt, task_domain="planning", use_cache=True)
        self.assertTrue(resp2.cache_hit)
        self.assertEqual(resp1.text, resp2.text)

    def test_automatic_failover(self):
        providers = {
            "openai": OpenAIProvider(),
            "anthropic": AnthropicProvider()
        }
        failover = FailoverEngine(providers)

        resp = failover.execute_with_failover(prompt="Test prompt", preferred_provider="openai")
        self.assertEqual(resp.provider, "openai")

    def test_structured_output_parsing(self):
        json_text = '{"status": "SUCCESS", "reasoning": "Structured response", "score": 99.5}'
        parsed = StructuredOutputParser.parse_or_fallback(json_text, SampleStructuredOutput)
        self.assertEqual(parsed.status, "SUCCESS")
        self.assertEqual(parsed.score, 99.5)

        # Fallback handling for malformed output
        fallback_parsed = StructuredOutputParser.parse_or_fallback("invalid json text", SampleStructuredOutput)
        self.assertEqual(fallback_parsed.status, "SUCCESS")

    def test_streaming_completion(self):
        prov = OpenAIProvider()
        chunks = list(InferenceStreamer.stream_completion(prov, "Stream prompt"))
        self.assertGreater(len(chunks), 0)

    def test_embeddings_gateway(self):
        embeds = self.gateway.embed(["vector text 1", "vector text 2"], provider_name="openai")
        self.assertEqual(len(embeds), 2)
        self.assertEqual(len(embeds[0]), 4)

    def test_cost_accounting(self):
        resp = LLMResponse(text="Test", prompt_tokens=100, completion_tokens=50, cost_usd=0.002, latency_ms=100.0)
        metrics = self.cost_tracker.record_request(resp, trace_id="tr_123")
        self.assertEqual(metrics.trace_id, "tr_123")

        summary = self.cost_tracker.get_summary()
        self.assertEqual(summary["total_requests"], 1)
        self.assertAlmostEqual(summary["total_cost_usd"], 0.002)

    def test_rate_limiting(self):
        limiter = ProviderRateLimiter()
        # Should allow initial request
        self.assertTrue(limiter.check_and_increment("openai"))


if __name__ == "__main__":
    unittest.main()
