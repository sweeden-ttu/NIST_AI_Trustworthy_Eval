"""Configuration management for rd-agent-mcp."""

import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from rd_agent_mcp.constants import DEFAULT_LM_STUDIO_BASE_URL


class CloudProviderConfig(BaseModel):
    """Cloud provider configuration."""

    openai: str = "gpt-4o"
    anthropic: str = "claude-3-5-sonnet"
    google: str = "gemini-2.0-flash"


class LangSmithConfig(BaseModel):
    """LangSmith configuration."""

    enabled: bool = False
    api_key_env: str = "LANGSMITH_API_KEY"
    project: str = "rd-agent-mcp"


class AgentPaths(BaseModel):
    """Paths to agent repositories."""

    rd_agent_path: str = "./agents/rd-agent"
    adk_ralph_path: str = "./agents/adk-ralph"


class Config(BaseModel):
    """Main configuration for rd-agent-mcp."""

    chat_model: str = "ibm/granite-4-h-tiny"
    embedding_model: str = "text-embedding-nomic-embed-text-v1.5"
    base_url: str = DEFAULT_LM_STUDIO_BASE_URL
    api_key: str = "lm-studio"
    chroma_path: str = "./chroma_data"
    sqlite_path: str = "./research.db"
    langsmith: LangSmithConfig = Field(default_factory=LangSmithConfig)
    agents: AgentPaths = Field(default_factory=AgentPaths)
    cloud_providers: CloudProviderConfig = Field(default_factory=CloudProviderConfig)

    @classmethod
    def from_file(cls, path: str) -> "Config":
        """Load configuration from a JSON file."""
        import json

        with open(path) as f:
            data = json.load(f)
        return cls(**data)

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        load_dotenv()
        return cls(
            chat_model=os.getenv("CHAT_MODEL", "ibm/granite-4-h-tiny"),
            embedding_model=os.getenv("EMBEDDING_MODEL", "text-embedding-nomic-embed-text-v1.5"),
            base_url=os.getenv("LM_STUDIO_BASE_URL", DEFAULT_LM_STUDIO_BASE_URL),
            api_key=os.getenv("LM_STUDIO_API_KEY", "lm-studio"),
            chroma_path=os.getenv("CHROMA_PATH", "./chroma_data"),
            sqlite_path=os.getenv("SQLITE_PATH", "./research.db"),
            langsmith=LangSmithConfig(
                enabled=os.getenv("LANGSMITH_TRACING", "false").lower() == "true",
                api_key_env="LANGSMITH_API_KEY",
                project=os.getenv("LANGSMITH_PROJECT", "rd-agent-mcp"),
            ),
            agents=AgentPaths(
                rd_agent_path=os.getenv("RD_AGENT_PATH", "./agents/rd-agent"),
                adk_ralph_path=os.getenv("ADK_RALPH_PATH", "./agents/adk-ralph"),
            ),
            cloud_providers=CloudProviderConfig(
                openai=os.getenv("OPENAI_MODEL", "gpt-4o"),
                anthropic=os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet"),
                google=os.getenv("GOOGLE_MODEL", "gemini-2.0-flash"),
            ),
        )

    def get_chat_url(self) -> str:
        """Get the chat completions URL."""
        return f"{self.base_url}/chat/completions"

    def get_embeddings_url(self) -> str:
        """Get the embeddings URL."""
        return f"{self.base_url}/embeddings"
