# LM Studio: local inference and chat template

## Server URL (default in this template)

Agents and **rd-agent-mcp** default to the OpenAI-compatible endpoint:

`http://192.168.0.13:1234/v1`

Override anytime with:

```bash
export LM_STUDIO_BASE_URL=http://YOUR_HOST:1234/v1
```

## Granite / agent-to-agent chat template

The Jinja prompt in [`lmstudio-granite-agent-to-agent.jinja`](./lmstudio-granite-agent-to-agent.jinja) matches the tool-call and role format used for multi-step agent workflows.

**Install in LM Studio**

1. Open LM Studio → **Developer** (or model settings) → **Presets** / **Edit LLM** → **Prompt template**.
2. Paste the contents of `lmstudio-granite-agent-to-agent.jinja`, or merge into your preset JSON.
3. You can keep a working copy at `~/.lmstudio/config-presets/sgskkssks.preset.json` (or any name) and iterate there; treat this repo file as the versioned source of truth to copy from.

Ensure the **local server** is bound so LAN clients (e.g. `192.168.0.13`) can reach port **1234** if you run agents on another machine.
