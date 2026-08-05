import re
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from src.infrastructure.storage.memory.graph_db import CodeGraph, GraphNode
from src.infrastructure.storage.memory.vector_store import VectorMemoryStore, VectorDocument


class ContextSnippet(BaseModel):
    id: str
    text: str
    source_type: str  # "vector" or "graph"
    rrf_score: float = 0.0
    rank: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ContextPayload(BaseModel):
    intent: str
    entities: List[str]
    repo_id: str
    ranked_snippets: List[ContextSnippet]
    assembled_prompt_context: str


class ContextEngine:
    """
    Production-grade 9-Stage Code Context Engine utilizing Reciprocal Rank Fusion (RRF),
    symbol resolution, and token window packing.
    """

    def __init__(self, graph: CodeGraph = None, vector_store: VectorMemoryStore = None, rrf_k: int = 60):
        self.graph = graph or CodeGraph()
        self.vector_store = vector_store or VectorMemoryStore()
        self.rrf_k = rrf_k

    def detect_intent(self, prompt: str) -> str:
        prompt_lower = prompt.lower()
        if any(w in prompt_lower for w in ["fix", "bug", "error", "traceback", "exception", "broken"]):
            return "bugfix"
        elif any(w in prompt_lower for w in ["refactor", "clean", "optim", "rewrite", "extract"]):
            return "refactor"
        elif any(w in prompt_lower for w in ["add", "create", "build", "implement", "feature"]):
            return "feature"
        return "qa"

    def extract_entities(self, prompt: str) -> List[str]:
        # Extract potential function names, class names, file paths
        candidates = re.findall(r'\b[A-Za-z_][A-Za-z0-9_]*\.(?:py|js|go|rs)\b|\b[A-Za-z_][A-Za-z0-9_]{2,}\b', prompt)
        stopwords = {"the", "and", "for", "with", "this", "that", "from", "import", "code", "file", "func", "class"}
        return [c for c in candidates if c.lower() not in stopwords]

    def query(self, prompt: str, repo_id: str = "default", top_k: int = 5, max_token_chars: int = 4000) -> ContextPayload:
        # Stage 1: Intent Detection
        intent = self.detect_intent(prompt)

        # Stage 2: Entity Extraction
        entities = self.extract_entities(prompt)

        # Stage 3-5: Symbol Resolution & Graph Traversal
        graph_nodes: List[GraphNode] = []
        for entity in entities:
            callers = self.graph.find_callers(entity, repo_id=repo_id)
            graph_nodes.extend(callers)

        # Stage 6: Vector Search
        vector_docs = self.vector_store.search(prompt, top_k=top_k * 2, repo_id=repo_id)

        # Stage 7: Reciprocal Rank Fusion (RRF)
        # RRF_Score(d) = 1 / (k + rank_vector(d)) + 1 / (k + rank_graph(d))
        rrf_scores: Dict[str, float] = {}
        snippet_map: Dict[str, ContextSnippet] = {}

        for rank, doc in enumerate(vector_docs, start=1):
            doc_id = doc.id
            score = 1.0 / (self.rrf_k + rank)
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + score
            snippet_map[doc_id] = ContextSnippet(
                id=doc_id,
                text=doc.text,
                source_type="vector",
                metadata=doc.metadata
            )

        for rank, gnode in enumerate(graph_nodes, start=1):
            gid = f"graph::{gnode.id}"
            score = 1.0 / (self.rrf_k + rank)
            rrf_scores[gid] = rrf_scores.get(gid, 0.0) + score
            snippet_map[gid] = ContextSnippet(
                id=gid,
                text=f"Symbol Node [{gnode.label}]: {gnode.name} (ID: {gnode.id})",
                source_type="graph",
                metadata={"label": gnode.label, "name": gnode.name}
            )

        # Sort combined RRF list
        ranked_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
        final_snippets: List[ContextSnippet] = []

        for final_rank, snip_id in enumerate(ranked_ids[:top_k], start=1):
            snip = snippet_map[snip_id]
            snip.rrf_score = rrf_scores[snip_id]
            snip.rank = final_rank
            final_snippets.append(snip)

        # Stage 8: Context Window Optimization (Token budget packing)
        assembled_blocks = []
        current_len = 0

        for snip in final_snippets:
            block = f"--- [Snippet #{snip.rank} | Source: {snip.source_type} | RRF Score: {snip.rrf_score:.4f}] ---\n{snip.text}\n"
            if current_len + len(block) > max_token_chars:
                break
            assembled_blocks.append(block)
            current_len += len(block)

        assembled_prompt_context = "\n".join(assembled_blocks)

        # Stage 9: Payload Assembly
        return ContextPayload(
            intent=intent,
            entities=entities,
            repo_id=repo_id,
            ranked_snippets=final_snippets,
            assembled_prompt_context=assembled_prompt_context
        )
