"""
NVIDIA NIM Infrastructure.
Provides embedding and LLM capabilities via NVIDIA's NIM API.
"""
from app.infrastructure.nim.embedding_provider import NIMEmbeddingProvider

__all__ = ["NIMEmbeddingProvider"]
