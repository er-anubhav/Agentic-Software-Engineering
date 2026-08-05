from typing import Dict, Any, List, Optional
from memory.graph_db import CodeGraph
from memory.vector_store import VectorMemoryStore, VectorDocument
from memory.context_engine import ContextEngine, ContextPayload


class HybridMemoryEngine:
    """
    Production-grade Multi-Tenant Hybrid Memory Engine fusing structural Neo4j CodeGraph nodes,
    FastEmbed dense vector embeddings, Qdrant HNSW vector search, and 9-stage ContextEngine RRF re-ranking.
    """

    def __init__(self, graph: CodeGraph = None, vector_store: VectorMemoryStore = None):
        self.graph = graph or CodeGraph()
        self.vector_store = vector_store or VectorMemoryStore()
        self.context_engine = ContextEngine(graph=self.graph, vector_store=self.vector_store)

    def add_code_document(self, doc_id: str, text: str, metadata: Dict[str, Any] = None, repo_id: str = "default") -> VectorDocument:
        return self.vector_store.add_document(doc_id, text, metadata=metadata, repo_id=repo_id)

    def query(self, prompt: str, repo_id: str = "default", top_k: int = 5) -> Dict[str, Any]:
        payload: ContextPayload = self.context_engine.query(prompt=prompt, repo_id=repo_id, top_k=top_k)
        graph_summary = self.graph.get_summary()

        return {
            "intent": payload.intent,
            "entities": payload.entities,
            "repo_id": payload.repo_id,
            "graph_summary": graph_summary,
            "context_prompt_text": payload.assembled_prompt_context,
            "ranked_snippets": [
                {
                    "id": snip.id,
                    "text": snip.text,
                    "source": snip.source_type,
                    "rrf_score": snip.rrf_score,
                    "rank": snip.rank
                }
                for snip in payload.ranked_snippets
            ]
        }
