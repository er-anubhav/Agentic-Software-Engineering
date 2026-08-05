from typing import List, Dict, Any
from pydantic import BaseModel, Field


class VectorDocument(BaseModel):
    id: str
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    score: float = 0.0


class VectorMemoryStore:
    """
    In-memory vector store representation with semantic keyword indexing fallback.
    """

    def __init__(self):
        self.documents: Dict[str, VectorDocument] = {}

    def add_document(self, doc_id: str, text: str, metadata: Dict[str, Any] = None) -> None:
        self.documents[doc_id] = VectorDocument(
            id=doc_id,
            text=text,
            metadata=metadata or {}
        )

    def search(self, query: str, top_k: int = 5) -> List[VectorDocument]:
        query_words = set(query.lower().split())
        scored = []
        for doc in self.documents.values():
            doc_words = set(doc.text.lower().split())
            intersection = query_words.intersection(doc_words)
            score = len(intersection) / (len(query_words) + 1e-5)
            scored.append(VectorDocument(
                id=doc.id,
                text=doc.text,
                metadata=doc.metadata,
                score=score
            ))
        scored.sort(key=lambda x: x.score, reverse=True)
        return scored[:top_k]
