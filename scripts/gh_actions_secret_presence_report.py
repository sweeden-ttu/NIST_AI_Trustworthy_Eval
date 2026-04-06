#!/usr/bin/env python3
"""Print which expected env keys are set (names only; never values). Used by inject-secrets-env workflow."""

from __future__ import annotations

import os
import sys

EXPECTED = [
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
    "GEMINI_API_KEY",
    "HF_TOKEN",
    "LANGSMITH_API_KEY",
    "VOYAGE_API_KEY",
    "CANVAS_API_TOKEN",
    "GITHUB_CLIENT_SECRET",
    "LM_STUDIO_API_KEY",
    "OPENAI_BASE_URL",
    "NIST_EVAL_MODEL",
    "LM_STUDIO_BASE_URL",
    "LM_STUDIO_API",
    "OLLAMA_HOST",
    "CHAT_MODEL",
    "EMBEDDING_MODEL",
    "RALPH_LOCAL_MODEL",
    "RALPH_MODEL_PROVIDER",
    "DOCKER_HOST",
    "CANVAS_BASE_URL",
    "RD_AGENT_PATH",
    "ADK_RALPH_PATH",
    "RD_AGENT_MCP_EXEC_AGENTS",
    # Optional OpenCode / multi-provider (see `.github/SECRETS.md`)
    "OPENCODE_API_KEY",
    "OPENROUTER_API_KEY",
    "GOOGLE_GENERATIVE_AI_API_KEY",
    "LMSTUDIO_API_KEY",
    "DEEPSEEK_API_KEY",
    "GROQ_API_KEY",
    "MISTRAL_API_KEY",
]


def main() -> int:
    set_names = [k for k in EXPECTED if os.environ.get(k)]
    missing = [k for k in EXPECTED if not os.environ.get(k)]
    print("Non-empty secret-backed env keys:", ", ".join(set_names) or "(none)")
    print("Missing or empty:", ", ".join(missing) or "(none)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
