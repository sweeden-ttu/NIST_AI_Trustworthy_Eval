"""LM Studio client for rd-agent-mcp."""

import json
import os
from typing import Optional, Any

import httpx
from langchain_core.language_models import BaseChatModel
from langchain_core.outputs import ChatResult, ChatGeneration
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, SystemMessage

from rd_agent_mcp.constants import DEFAULT_LM_STUDIO_BASE_URL


class LMStudioClient:
    """Client for LM Studio local inference server."""

    def __init__(
        self,
        model: str = "ibm/granite-4-h-tiny",
        base_url: str | None = None,
        api_key: str = "lm-studio",
        timeout: float = 300.0,
    ):
        self.model = model
        resolved_base = base_url or os.getenv("LM_STUDIO_BASE_URL") or DEFAULT_LM_STUDIO_BASE_URL
        self.base_url = resolved_base.rstrip("/")
        self.api_key = api_key
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

    async def chat(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = -1,
        **kwargs,
    ) -> str:
        """Send a chat completion request."""
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens > 0:
            payload["max_tokens"] = max_tokens

        response = await self.client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

    async def embeddings(self, texts: str | list[str]) -> list[float] | list[list[float]]:
        """Generate embeddings for text(s)."""
        url = f"{self.base_url}/embeddings"
        if isinstance(texts, str):
            texts = [texts]
        payload = {
            "model": "text-embedding-nomic-embed-text-v1.5",
            "input": texts,
        }
        response = await self.client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        return [item["embedding"] for item in data["data"]]

    async def list_models(self) -> list[dict]:
        """List available models."""
        url = f"{self.base_url}/models"
        response = await self.client.get(url)
        response.raise_for_status()
        return response.json().get("data", [])

    async def is_available(self) -> bool:
        """Check if LM Studio is available."""
        try:
            await self.list_models()
            return True
        except Exception:
            return False


class LangChainLMStudio(BaseChatModel):
    """LangChain integration for LM Studio."""

    model: str = "ibm/granite-4-h-tiny"
    base_url: str | None = None
    temperature: float = 0.7
    max_tokens: int = -1

    @property
    def _llm_type(self) -> str:
        return "lm-studio"

    def _convert_message(self, message: BaseMessage) -> dict:
        if isinstance(message, HumanMessage):
            return {"role": "user", "content": message.content}
        elif isinstance(message, AIMessage):
            return {"role": "assistant", "content": message.content}
        elif isinstance(message, SystemMessage):
            return {"role": "system", "content": message.content}
        else:
            return {"role": "user", "content": str(message.content)}

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: Optional[list[str]] = None,
        **kwargs,
    ) -> ChatResult:
        import asyncio

        return asyncio.run(self._agenerate(messages, stop, **kwargs))

    async def _agenerate(
        self,
        messages: list[BaseMessage],
        stop: Optional[list[str]] = None,
        **kwargs,
    ) -> ChatResult:
        client = LMStudioClient(model=self.model, base_url=self.base_url)
        try:
            converted = [self._convert_message(m) for m in messages]
            content = await client.chat(
                converted,
                temperature=kwargs.get("temperature", self.temperature),
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
            )
            return ChatResult(generations=[ChatGeneration(message=AIMessage(content=content))])
        finally:
            await client.close()
