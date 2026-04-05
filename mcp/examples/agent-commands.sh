#!/usr/bin/env bash
# Run from rd-ralph-template repository root after submodules are initialized.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
RD_AGENT="${RD_AGENT_PATH:-$ROOT/agents/rd-agent}"
ADK="${ADK_RALPH_PATH:-$ROOT/agents/adk-ralph}"

echo "=== rd-agent (example dry check) ==="
if [[ -d "$RD_AGENT" ]]; then
  (cd "$RD_AGENT" && python -m rdagent --help) || true
else
  echo "Skip: $RD_AGENT not found"
fi

echo "=== adk-ralph (example cargo check) ==="
if [[ -d "$ADK" ]]; then
  (cd "$ADK" && cargo check -q) || true
else
  echo "Skip: $ADK not found"
fi
