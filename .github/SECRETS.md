# GitHub Actions: repository secrets and variables

GitHub does not let workflows **create** secret values; add them in the repo UI (**Settings → Secrets and variables → Actions**) or with the CLI:

```bash
gh secret set OPENAI_API_KEY --body "sk-..."
# or from a file:
gh secret set OPENAI_API_KEY < openai.key
```

Use **Secrets** for tokens and keys. Use **Variables** (same settings page) for non-sensitive config such as base URLs and model ids when you prefer not to store them as secrets.

## Names referenced by workflows (add as Repository secrets)

| Name | Used in | Notes |
|------|---------|--------|
| `OPENAI_API_KEY` | `research-pipeline.yaml`, `agent-demo.yaml`, `inject-secrets-env.yml` | Required for live LLM calls; optional for NIST dry-run steps |
| `OPENAI_BASE_URL` | `research-pipeline.yaml`, `agent-demo.yaml`, `inject-secrets-env.yml` | OpenAI-compatible API base (e.g. LM Studio) |
| `NIST_EVAL_MODEL` | `research-pipeline.yaml`, `agent-demo.yaml`, `inject-secrets-env.yml` | Model id for `run_nist_llm_evaluation.py` when not using default |
| `ANTHROPIC_API_KEY` | `research-pipeline.yaml`, `inject-secrets-env.yml` | Optional provider for rd-agent-mcp |
| `GEMINI_API_KEY` | `research-pipeline.yaml`, `inject-secrets-env.yml` | Optional provider for rd-agent-mcp |
| `HF_TOKEN` | `research-pipeline.yaml`, `inject-secrets-env.yml` | Hugging Face |
| `LANGSMITH_API_KEY` | `research-pipeline.yaml`, `inject-secrets-env.yml` | LangSmith tracing |
| `VOYAGE_API_KEY` | `inject-secrets-env.yml` | Embeddings / voyage (if you use locally) |
| `CANVAS_API_TOKEN` | `inject-secrets-env.yml` | Canvas LMS API (if used) |
| `GITHUB_CLIENT_SECRET` | `inject-secrets-env.yml` | OAuth client secret (only if a workflow needs it; prefer not to use in CI) |
| `LM_STUDIO_API_KEY` | `inject-secrets-env.yml` | LM Studio / OpenAI-compatible key (often `lm-studio`) |
| `LM_STUDIO_BASE_URL` | `inject-secrets-env.yml` | Same role as `OPENAI_BASE_URL` for local stacks |
| `CANVAS_BASE_URL` | `inject-secrets-env.yml` | Canvas API base URL (often better as a **Variable**) |
| `RD_AGENT_PATH` | `inject-secrets-env.yml` | Path to rd-agent submodule checkout in CI |
| `ADK_RALPH_PATH` | `inject-secrets-env.yml` | Path to adk-ralph submodule checkout in CI |
| `RD_AGENT_MCP_EXEC_AGENTS` | `inject-secrets-env.yml` | `true`/`false` for spawning real agents (trusted envs only) |
| `LM_STUDIO_API` | `inject-secrets-env.yml` | Present in some dev envs; map if your tools read this name |
| `OLLAMA_HOST` | `inject-secrets-env.yml` | Ollama base URL/host |
| `CHAT_MODEL` | `inject-secrets-env.yml` | Default chat model id |
| `EMBEDDING_MODEL` | `inject-secrets-env.yml` | Default embedding model id |
| `RALPH_LOCAL_MODEL` | `inject-secrets-env.yml` | adk-ralph local model |
| `RALPH_MODEL_PROVIDER` | `inject-secrets-env.yml` | e.g. `ollama` |
| `DOCKER_HOST` | `inject-secrets-env.yml` | Only if CI must reach a remote Docker socket |

## Automatic token (do not create manually)

| Name | Notes |
|------|--------|
| `GITHUB_TOKEN` | Injected by GitHub Actions; workflows use `secrets.GITHUB_TOKEN` or `github.token` |

## Optional: non-secret configuration (Actions **Variables**)

If you prefer variables instead of secrets for non-sensitive values:

- `CANVAS_BASE_URL`
- `OPENAI_BASE_URL` / `LM_STUDIO_BASE_URL`
- `NIST_EVAL_MODEL`, `CHAT_MODEL`, `EMBEDDING_MODEL`
- `RD_AGENT_PATH`, `ADK_RALPH_PATH`, `RD_AGENT_MCP_EXEC_AGENTS`

To use variables in a workflow, reference `vars.NAME` (and add the variable in **Settings → Secrets and variables → Actions → Variables**).

## Generate names from your local `env` (optional)

This prints **candidate** names (uppercase identifiers), excluding common OS/IDE keys:

```bash
python scripts/list_github_secret_candidates_from_env.py
```

Review the list before creating secrets; do not commit real values.
