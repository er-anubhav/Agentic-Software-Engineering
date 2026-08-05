from typing import Dict, Any, List
from memory.graph_db import CodeGraph
from memory.vector_store import VectorMemoryStore, VectorDocument


class HybridMemoryEngine:
    """
    Production-grade Hybrid Memory Engine fusing structural Neo4j/CodeGraph nodes,
    FastEmbed dense vector embeddings, and Qdrant Cosine Similarity search.
    """

    def __init__(self, graph: CodeGraph = None, vector_store: VectorMemoryStore = None):
        self.graph = graph or CodeGraph()
        self.vector_store = vector_store or VectorMemoryStore()

    def add_code_document(self, doc_id: str, text: str, metadata: Dict[str, Any] = None) -> VectorDocument:
        return self.vector_store.add_document(doc_id, text, metadata)

    def query(self, prompt: str, top_k: int = 5) -> Dict[str, Any]:
        vector_results = self.vector_store.search(prompt, top_k=top_k)
        graph_summary = self.graph.get_summary()

        # Structural caller lookup if a symbol is mentioned in prompt
        graph_callers = []
        words = prompt.split()
        for word in words:
            clean_word = word.strip("()'\",.;:")
            callers = self.graph.find_callers(clean_word)
            if callers:
                graph_callers.extend([
                    {"symbol": clean_word, "caller_id": caller.id, "caller_name": caller.name}
                    for caller in callers
                ])

        return {
            "graph_summary": graph_summary,
            "structural_callers": graph_callers,
            "semantic_vector_matches": [
                {
                    "id": doc.id,
                    "text": doc.text,
                    "score": doc.score,
                    "metadata": doc.metadata
                }
                for doc in vector_results
            ]
        }
