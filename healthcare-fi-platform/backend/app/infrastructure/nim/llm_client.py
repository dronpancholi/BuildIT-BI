"""
NVIDIA NIM LLM Client.
Uses the OpenAI-compatible API with rate limiting (40 RPM free tier).
"""
import asyncio
import logging
import time
from collections import deque
from typing import Optional, List, Dict, Any

from openai import AsyncOpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)

# Free model — fast, good for finance, small context window is fine
DEFAULT_MODEL = "meta/llama-3.1-8b-instruct"
MAX_RPM = 40  # Free tier limit
RPM_WINDOW = 60.0  # seconds


class RateLimiter:
    """Sliding-window rate limiter for 40 RPM free tier."""

    def __init__(self, max_requests: int = MAX_RPM, window: float = RPM_WINDOW):
        self.max_requests = max_requests
        self.window = window
        self._timestamps: deque = deque()
        self._lock = asyncio.Lock()

    async def acquire(self):
        """Wait until a request slot is available."""
        async with self._lock:
            now = time.monotonic()
            # Purge expired timestamps
            while self._timestamps and self._timestamps[0] <= now - self.window:
                self._timestamps.popleft()
            if len(self._timestamps) >= self.max_requests:
                # Sleep until the oldest request expires
                sleep_time = self._timestamps[0] + self.window - now + 0.1
                if sleep_time > 0:
                    logger.warning(f"Rate limit: sleeping {sleep_time:.1f}s")
                    await asyncio.sleep(sleep_time)
            self._timestamps.append(time.monotonic())


class NIMLLMClient:
    """
    NVIDIA NIM LLM client with rate limiting.
    Uses OpenAI-compatible API format.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = DEFAULT_MODEL,
    ):
        self.api_key = api_key or settings.NVIDIA_NIM_API_KEY
        self.base_url = base_url or settings.NVIDIA_NIM_BASE_URL
        self.model = model
        self._rate_limiter = RateLimiter()
        self._client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=60.0,
            max_retries=2,
        )

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 1024,
        system: Optional[str] = None,
    ) -> str:
        """
        Send a chat completion request with rate limiting.
        Returns the assistant message content.
        """
        if not self.api_key:
            logger.warning("NIM API key not configured, returning fallback")
            return ""

        await self._rate_limiter.acquire()

        full_messages = []
        if system:
            full_messages.append({"role": "system", "content": system})
        full_messages.extend(messages)

        try:
            response = await self._client.chat.completions.create(
                model=self.model,
                messages=full_messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            content = response.choices[0].message.content or ""
            return content.strip()
        except Exception as e:
            logger.error(f"NIM LLM call failed: {e}")
            return ""

    async def complete(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> str:
        """Single-turn completion convenience method."""
        return await self.chat(
            messages=[{"role": "user", "content": prompt}],
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    async def close(self):
        """Close the underlying HTTP client."""
        await self._client.close()


# Module-level singleton (lazy init)
_llm_client: Optional[NIMLLMClient] = None


def get_llm_client() -> NIMLLMClient:
    """Get or create the singleton LLM client."""
    global _llm_client
    if _llm_client is None:
        _llm_client = NIMLLMClient()
    return _llm_client
