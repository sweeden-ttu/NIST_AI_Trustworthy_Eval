"""Embedding utilities using LM Studio."""

import os
from typing import Optional

import httpx
from langchain_core.embeddings import Embeddings

from rd_agent_mcp.constants import DEFAULT_LM_STUDIO_BASE_URL


def _resolve_lm_base_url(base_url: str | None) -> str:
    return (base_url or os.getenv("LM_STUDIO_BASE_URL") or DEFAULT_LM_STUDIO_BASE_URL).rstrip("/")


class LMStudioEmbeddings(Embeddings):
    """Embeddings using LM Studio."""

    def __init__(
        self,
        model: str = "text-embedding-nomic-embed-text-v1.5",
        base_url: str | None = None,
        timeout: float = 60.0,
    ):
        self.model = model
        self.base_url = _resolve_lm_base_url(base_url)
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _embed_async(self, texts: list[str]) -> list[list[float]]:
        """Embed texts asynchronously."""
        url = f"{self.base_url}/embeddings"
        payload = {
            "model": self.model,
            "input": texts,
        }
        response = await self.client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        return [item["embedding"] for item in data["data"]]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple documents synchronously."""
        import asyncio

        return asyncio.run(self._embed_async(texts))

    def embed_query(self, text: str) -> list[float]:
        """Embed a single query."""
        return self.embed_documents([text])[0]

    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple documents asynchronously."""
        return await self._embed_async(texts)

    async def aembed_query(self, text: str) -> list[float]:
        """Embed a single query asynchronously."""
        results = await self._embed_async([text])
        return results[0]


class SyncLMStudioEmbeddings(Embeddings):
    """Synchronous embeddings wrapper for LM Studio using requests."""

    def __init__(
        self,
        model: str = "text-embedding-nomic-embed-text-v1.5",
        base_url: str | None = None,
    ):
        self.model = model
        self.base_url = _resolve_lm_base_url(base_url)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple documents."""
        import requests

        url = f"{self.base_url}/embeddings"
        payload = {
            "model": self.model,
            "input": texts,
        }
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        return [item["embedding"] for item in data["data"]]

    def embed_query(self, text: str) -> list[float]:
        """Embed a single query."""
        return self.embed_documents([text])[0]
