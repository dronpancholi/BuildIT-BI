"""
NVIDIA NIM Embedding Provider.
Uses NVIDIA's NIM API for text embeddings.
"""
import logging
from typing import List, Optional
import httpx

from app.core.config import settings
from app.domain.memory import EmbeddingProvider, MemoryDocument

logger = logging.getLogger(__name__)

NIM_EMBEDDING_URL = f"{settings.NVIDIA_NIM_BASE_URL}/embeddings"
DEFAULT_MODEL = "nvidia/nv-embedqa-e5-v5"
DEFAULT_DIMENSION = 1024


class NIMEmbeddingProvider(EmbeddingProvider):
    """NVIDIA NIM-based embedding provider for semantic memory."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = DEFAULT_MODEL,
        embedding_dimension: int = DEFAULT_DIMENSION,
    ):
        self.api_key = api_key or settings.NVIDIA_NIM_API_KEY
        self.model_name = model_name
        self.embedding_dimension = embedding_dimension
        self._client = httpx.AsyncClient(
            base_url=settings.NVIDIA_NIM_BASE_URL,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    async def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        if not texts:
            return []
        if not self.api_key:
            logger.warning("NIM API key not configured, returning empty embeddings")
            return [[] for _ in texts]

        try:
            response = await self._client.post(
                "/embeddings",
                json={
                    "model": self.model_name,
                    "input": texts,
                    "input_type": "query",
                    "encoding_format": "float",
                },
            )
            response.raise_for_status()
            data = response.json()
            embeddings = [item["embedding"] for item in data["data"]]
            return embeddings
        except Exception as e:
            logger.error(f"NIM embedding failed: {e}")
            return [[] for _ in texts]

    async def embed_with_metadata(
        self, documents: List[MemoryDocument]
    ) -> List[dict]:
        """Embed documents and return with metadata for vector storage."""
        texts = [doc.content for doc in documents]
        embeddings = await self.embed(texts)
        results = []
        for doc, embedding in zip(documents, embeddings):
            results.append({
                "id": doc.id or str(doc.id),
                "embedding": embedding,
                "metadata": {
                    "content": doc.content,
                    "doc_type": doc.doc_type,
                    "entity_id": doc.entity_id,
                    "tenant_id": str(doc.tenant_id),
                    "created_at": doc.created_at.isoformat(),
                },
            })
        return results

    async def embed_query(self, query: str) -> List[float]:
        """Embed a single query text."""
        results = await self.embed([query])
        return results[0] if results else []

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()
