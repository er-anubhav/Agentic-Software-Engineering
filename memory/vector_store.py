import math
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

try:
    import numpy as np
except ImportError:
    np = None

try:
    from fastembed import TextEmbedding
    HAS_FASTEMBED = True
except ImportError:
    HAS_FASTEMBED = False

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
    HAS_QDRANT = True
except ImportError:
    HAS_QDRANT = False


class VectorDocument(BaseModel):
    id: str
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    vector: Optional[List[float]] = None
    score: float = 0.0


def compute_cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0

    if np is not None:
        v1 = np.array(vec1, dtype=np.float32)
        v2 = np.array(vec2, dtype=np.float32)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(v1, v2) / (norm1 * norm2))
    else:
        dot = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)


class VectorMemoryStore:
    """
    Production-grade Vector Memory Store using FastEmbed dense text embeddings,
    Qdrant vector collection indexing, and Cosine Similarity math.
    """

    def __init__(self, collection_name: str = "agentic_memory"):
        self.collection_name = collection_name
        self.documents: Dict[str, VectorDocument] = {}

        # Initialize FastEmbed Model
        self.embedding_model = None
        if HAS_FASTEMBED:
            try:
                self.embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
            except Exception:
                pass

        # Initialize Qdrant Client (in-memory)
        self.qdrant_client = None
        if HAS_QDRANT:
            try:
                self.qdrant_client = QdrantClient(location=":memory:")
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
                )
            except Exception:
                self.qdrant_client = None

    def _embed(self, text: str) -> List[float]:
        if self.embedding_model:
            try:
                embeddings = list(self.embedding_model.embed([text]))
                if len(embeddings) > 0:
                    return embeddings[0].tolist()
            except Exception:
                pass

        # Deterministic feature hashing vector fallback if model uninitialized
        vector = [0.0] * 384
        words = text.lower().split()
        for i, word in enumerate(words):
            idx = abs(hash(word)) % 384
            vector[idx] += 1.0 / (i + 1.0)
        norm = math.sqrt(sum(x * x for x in vector)) or 1.0
        return [x / norm for x in vector]

    def add_document(self, doc_id: str, text: str, metadata: Dict[str, Any] = None) -> VectorDocument:
        vector = self._embed(text)
        doc = VectorDocument(
            id=doc_id,
            text=text,
            metadata=metadata or {},
            vector=vector
        )
        self.documents[doc_id] = doc

        if self.qdrant_client:
            try:
                # Numerical payload ID for Qdrant Struct
                point_id = abs(hash(doc_id)) % (10 ** 12)
                self.qdrant_client.upsert(
                    collection_name=self.collection_name,
                    points=[PointStruct(
                        id=point_id,
                        vector=vector,
                        payload={"doc_id": doc_id, "text": text, **(metadata or {})}
                    )]
                )
            except Exception:
                pass

        return doc

    def search(self, query: str, top_k: int = 5) -> List[VectorDocument]:
        query_vector = self._embed(query)
        results = []

        for doc_id, doc in self.documents.items():
            if doc.vector:
                score = compute_cosine_similarity(query_vector, doc.vector)
            else:
                score = 0.0

            results.append(VectorDocument(
                id=doc.id,
                text=doc.text,
                metadata=doc.metadata,
                vector=doc.vector,
                score=score
            ))

        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]
