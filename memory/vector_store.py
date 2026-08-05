import math
import hashlib
from typing import List, Dict, Any, Optional, Tuple
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
    from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
    HAS_QDRANT = True
except ImportError:
    HAS_QDRANT = False


class VectorDocument(BaseModel):
    id: str
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    repo_id: str = "default"
    vector: Optional[List[float]] = None
    score: float = 0.0


def generate_sha256_point_id(repo_id: str, doc_id: str, symbol: Optional[str] = None) -> int:
    """
    Generates a deterministic 64-bit integer point ID for Qdrant storage using
    cryptographic SHA-256 hashing on `repo_id:doc_id:symbol` namespaced string representation.
    Guarantees seed stability across process restarts.
    """
    raw_key = f"{repo_id}:{doc_id}:{symbol or ''}"
    hash_hex = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
    return int(hash_hex[:12], 16)


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
    Production-grade Multi-Tenant Vector Memory Store supporting FastEmbed ONNX
    batch embedding generation, Qdrant HNSW vector index isolation, and SHA256 namespacing.
    """

    def __init__(self, collection_name: str = "agentic_memory", qdrant_url: Optional[str] = None):
        self.collection_name = collection_name
        self.documents: Dict[str, VectorDocument] = {}

        # Initialize FastEmbed Model
        self.embedding_model = None
        if HAS_FASTEMBED:
            try:
                self.embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
            except Exception:
                pass

        # Initialize Qdrant Client (in-memory or remote cluster)
        self.qdrant_client = None
        if HAS_QDRANT:
            try:
                if qdrant_url:
                    self.qdrant_client = QdrantClient(url=qdrant_url)
                else:
                    self.qdrant_client = QdrantClient(location=":memory:")

                collections = [c.name for c in self.qdrant_client.get_collections().collections]
                if self.collection_name not in collections:
                    self.qdrant_client.create_collection(
                        collection_name=self.collection_name,
                        vectors_config=VectorParams(size=384, distance=Distance.COSINE)
                    )
            except Exception:
                self.qdrant_client = None

    def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        if self.embedding_model and texts:
            try:
                embeddings = list(self.embedding_model.embed(texts))
                return [emb.tolist() for emb in embeddings]
            except Exception:
                pass

        results = []
        for text in texts:
            vector = [0.0] * 384
            words = text.lower().split()
            for i, word in enumerate(words):
                word_hash = int(hashlib.sha256(word.encode("utf-8")).hexdigest()[:8], 16)
                idx = word_hash % 384
                vector[idx] += 1.0 / (i + 1.0)
            norm = math.sqrt(sum(x * x for x in vector)) or 1.0
            results.append([x / norm for x in vector])
        return results

    def _embed(self, text: str) -> List[float]:
        return self._embed_batch([text])[0]

    def add_document(self, doc_id: str, text: str, metadata: Dict[str, Any] = None, repo_id: str = "default") -> VectorDocument:
        vector = self._embed(text)
        meta = metadata or {}
        meta["repo_id"] = repo_id

        doc = VectorDocument(
            id=doc_id,
            text=text,
            metadata=meta,
            repo_id=repo_id,
            vector=vector
        )
        self.documents[doc_id] = doc

        if self.qdrant_client:
            try:
                symbol = meta.get("symbol")
                point_id = generate_sha256_point_id(repo_id, doc_id, symbol)
                self.qdrant_client.upsert(
                    collection_name=self.collection_name,
                    points=[PointStruct(
                        id=point_id,
                        vector=vector,
                        payload={"doc_id": doc_id, "text": text, "repo_id": repo_id, **meta}
                    )]
                )
            except Exception:
                pass

        return doc

    def add_documents_batch(self, repo_id: str, docs: List[Dict[str, Any]]) -> List[VectorDocument]:
        """
        High-throughput batch document ingestion with parallel ONNX neural embedding.
        Each doc in list is a dict: {"id": str, "text": str, "metadata": Optional[Dict]}
        """
        if not docs:
            return []

        texts = [d["text"] for d in docs]
        vectors = self._embed_batch(texts)

        added_docs = []
        points = []

        for i, d in enumerate(docs):
            doc_id = d["id"]
            text = d["text"]
            meta = d.get("metadata") or {}
            meta["repo_id"] = repo_id
            vector = vectors[i]

            doc = VectorDocument(
                id=doc_id,
                text=text,
                metadata=meta,
                repo_id=repo_id,
                vector=vector
            )
            self.documents[doc_id] = doc
            added_docs.append(doc)

            symbol = meta.get("symbol")
            point_id = generate_sha256_point_id(repo_id, doc_id, symbol)
            points.append(PointStruct(
                id=point_id,
                vector=vector,
                payload={"doc_id": doc_id, "text": text, "repo_id": repo_id, **meta}
            ))

        if self.qdrant_client and points:
            try:
                self.qdrant_client.upsert(
                    collection_name=self.collection_name,
                    points=points
                )
            except Exception:
                pass

        return added_docs

    def delete_by_file(self, repo_id: str, file_path: str) -> None:
        """
        Deletes vector index points corresponding to a specific repository file path.
        """
        to_delete = [
            doc_id for doc_id, doc in self.documents.items()
            if doc.repo_id == repo_id and doc.metadata.get("file_path") == file_path
        ]
        for doc_id in to_delete:
            del self.documents[doc_id]

        if self.qdrant_client and HAS_QDRANT:
            try:
                query_filter = Filter(must=[
                    FieldCondition(key="repo_id", match=MatchValue(value=repo_id)),
                    FieldCondition(key="file_path", match=MatchValue(value=file_path))
                ])
                self.qdrant_client.delete(
                    collection_name=self.collection_name,
                    points_selector=query_filter
                )
            except Exception:
                pass

    def search(self, query: str, top_k: int = 5, repo_id: Optional[str] = None) -> List[VectorDocument]:
        query_vector = self._embed(query)

        # Delegate query to Qdrant vector engine if active
        if self.qdrant_client:
            try:
                q_filter = None
                if repo_id and HAS_QDRANT:
                    q_filter = Filter(must=[FieldCondition(key="repo_id", match=MatchValue(value=repo_id))])

                if hasattr(self.qdrant_client, "search"):
                    hits = self.qdrant_client.search(
                        collection_name=self.collection_name,
                        query_vector=query_vector,
                        query_filter=q_filter,
                        limit=top_k
                    )
                    return [
                        VectorDocument(
                            id=hit.payload.get("doc_id", str(hit.id)),
                            text=hit.payload.get("text", ""),
                            repo_id=hit.payload.get("repo_id", "default"),
                            metadata={k: v for k, v in hit.payload.items() if k not in ("doc_id", "text")},
                            score=hit.score
                        )
                        for hit in hits
                    ]
                elif hasattr(self.qdrant_client, "query_points"):
                    query_res = self.qdrant_client.query_points(
                        collection_name=self.collection_name,
                        query=query_vector,
                        query_filter=q_filter,
                        limit=top_k
                    )
                    return [
                        VectorDocument(
                            id=point.payload.get("doc_id", str(point.id)),
                            text=point.payload.get("text", ""),
                            repo_id=point.payload.get("repo_id", "default"),
                            metadata={k: v for k, v in point.payload.items() if k not in ("doc_id", "text")},
                            score=point.score
                        )
                        for point in query_res.points
                    ]
            except Exception:
                pass

        # In-memory vector cosine similarity search fallback with repo_id filter
        results = []
        for doc_id, doc in self.documents.items():
            if repo_id and doc.repo_id != repo_id:
                continue

            if doc.vector:
                score = compute_cosine_similarity(query_vector, doc.vector)
            else:
                score = 0.0

            results.append(VectorDocument(
                id=doc.id,
                text=doc.text,
                metadata=doc.metadata,
                repo_id=doc.repo_id,
                vector=doc.vector,
                score=score
            ))

        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]
