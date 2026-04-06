"""LM Studio model registry."""

from typing import TypedDict


class ModelInfo(TypedDict):
    """Information about a model."""

    id: str
    object: str
    owned_by: str


class ModelRegistry:
    """Registry for available models."""

    DEFAULT_CHAT_MODEL = "ibm/granite-4-h-tiny"
    DEFAULT_EMBEDDING_MODEL = "text-embedding-nomic-embed-text-v1.5"

    CHAT_MODELS = {
        "ibm/granite-4-h-tiny": "IBM Granite 4B (Tiny)",
        "qwen2.5-7b-instruct": "Qwen 2.5 7B Instruct",
        "llama-3.2-1b-instruct": "Llama 3.2 1B Instruct",
        "llama-3.2-3b-instruct": "Llama 3.2 3B Instruct",
    }

    EMBEDDING_MODELS = {
        "text-embedding-nomic-embed-text-v1.5": "Nomic Embed Text v1.5",
        "text-embedding-qwen3-embedding-4b": "Qwen3 Embedding 4B",
        "text-embedding-granite-embedding-125m-english": "Granite Embedding 125M",
    }

    CLOUD_MODELS = {
        "openai/gpt-4o": "OpenAI GPT-4o",
        "openai/gpt-4o-mini": "OpenAI GPT-4o Mini",
        "anthropic/claude-3-5-sonnet": "Anthropic Claude 3.5 Sonnet",
        "anthropic/claude-3-5-haiku": "Anthropic Claude 3.5 Haiku",
        "google/gemini-2.0-flash": "Google Gemini 2.0 Flash",
    }

    @classmethod
    def get_chat_models(cls) -> dict[str, str]:
        """Get all available chat models."""
        return cls.CHAT_MODELS.copy()

    @classmethod
    def get_embedding_models(cls) -> dict[str, str]:
        """Get all available embedding models."""
        return cls.EMBEDDING_MODELS.copy()

    @classmethod
    def get_cloud_models(cls) -> dict[str, str]:
        """Get all available cloud models."""
        return cls.CLOUD_MODELS.copy()

    @classmethod
    def is_cloud_model(cls, model: str) -> bool:
        """Check if a model is a cloud model."""
        return any(model.startswith(prefix) for prefix in ["openai/", "anthropic/", "google/"])
