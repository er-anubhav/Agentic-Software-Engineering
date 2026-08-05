from typing import Dict, Any, List
from memory.graph_db import CodeGraph
from memory.vector_store import VectorMemoryStore, VectorDocument


class HybridMemoryEngine:
    """
    Fuses structural code knowledge graphs and semantic vector store search results.
    """

    def __init__(self, graph: CodeGraph = None, vector_store: VectorMemoryStore = None):
        self.graph = graph or CodeGraph()
        self.vector_store = vector_store or VectorMemoryStore()

    def query(self, prompt: str, top_k: int = 5) -> Dict[str, Any]:
        vector_results = self.vector_store.search(prompt, top_k=top_k)
        graph_summary = self.graph.get_summary()

        return {
            "graph_summary": graph_summary,
            "relevant_snippets": [
                {"id": doc.id, "text": doc.text, "score": doc.score}
                for doc in vector_results
            ]
        }
