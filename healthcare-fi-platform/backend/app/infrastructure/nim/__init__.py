"""
NVIDIA NIM Infrastructure.
Provides embedding and LLM capabilities via NVIDIA's NIM API.
"""
from app.infrastructure.nim.embedding_provider import NIMEmbeddingProvider
from app.infrastructure.nim.llm_client import NIMLLMClient, get_llm_client

__all__ = ["NIMEmbeddingProvider", "NIMLLMClient", "get_llm_client"]
