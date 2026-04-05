# Local LM Studio endpoint (agent-to-agent)

## Default

This template and **rd-agent-mcp** use:

`http://192.168.0.13:1234/v1`

Set `LM_STUDIO_BASE_URL` to override (must include `/v1` for OpenAI-compatible clients).

## LiteLLM / rd-agent subprocess

`rd-agent-mcp` sets for child processes (unless already in the environment):

- `LM_STUDIO_BASE_URL`
- `LITELLM_OPENAI_API_BASE`
- `OPENAI_API_BASE`

## Chat template

See [`config/lmstudio-granite-agent-to-agent.jinja`](../../config/lmstudio-granite-agent-to-agent.jinja) and [`config/README.md`](../../config/README.md). Sync changes into LM Studio presets (e.g. `~/.lmstudio/config-presets/sgskkssks.preset.json`).

## Cursor IDE: sync model picker with `lms` + server

Script: [`scripts/sync_cursor_lmstudio_models.py`](../../scripts/sync_cursor_lmstudio_models.py)

Uses **`GET /v1/models`** (OpenAI-compatible, matches runtime) and optionally **`lms ls --json --llm`**, then merges ids into Cursor’s `state.vscdb`. See [`scripts/README.md`](../../scripts/README.md).
