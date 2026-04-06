---
name: init
description: >-
  Bootstraps README.md and AGENTS.md, updates pyproject.toml and environment.yml
  for editable rd-agent-mcp, and emits todo.json, PRD.md, and Design.md after a
  main.tex template/homework alignment audit. Use when the user types /init or
  asks to initialize repo docs and agent planning artifacts.
---

# /init — project README and AGENTS bootstrap

## Goal

Produce three artifacts at the **repository root**:

1. **`README.md`** — how to run the project **end to end**, with **prerequisites listed first** (before install, configure, or run steps).
2. **`AGENTS.md`** — concise **file and folder architecture** summary aimed at AI coding agents (what lives where, entrypoints, conventions).
3. **pyproject.toml** - updates the dependencies and creates a miniconda yaml setup which builds all sub-agents, modules and libraries such as rd-agent-mcp module so that calling python -m rdagent.graph.edges ...
4. Evaluates the current main.tex for any occurances of the word (template) and assesses its completion with regards to homework-assignment.pdf and creates a comprehensive todo.json, PRD.md, and Design.md file for ralph-adk agent. 

## When to run

Apply this skill when the user invokes **`/init`** or explicitly asks for this pair of docs.

## Workflow

1. **Discover** (read-only pass):
   - Top-level layout (`ls` / tree-style inventory): `src/`, `scripts/`, `test_cases/`, `.github/`, `docs/`, config files, etc.
   - Package and tooling: `pyproject.toml`, `requirements*.txt`, `Makefile`, `Dockerfile`, `package.json`, `uv.lock`, etc.
   - Existing hints: any current `README.md`, `AGENTS.md`, `CONTRIBUTING.md`, `scripts/README.md`, workflow YAML under `.github/workflows/`.
   - Primary entrypoints: CLIs, `main` modules, documented `uv run` / `python` / `npm` commands.

2. **Write or update `README.md`**
   - **Start with prerequisites**: OS/runtime (e.g. Python version), required tools (`uv`, `conda`, Node, LaTeX, OpenSSL), API keys / env vars, optional services (LM Studio, databases).
   - **Then** ordered sections such as: clone → environment → install → configuration (`.env`, secrets) → **minimal “happy path” run** → full end-to-end flows (eval, tests, build, CI) → where outputs land → links to deeper docs (`scripts/README.md`, etc.).
   - Use **concrete commands** copied from the repo where possible; mark placeholders for secrets.
   - If a non-empty `README.md` already exists: **preserve** accurate unique content; **replace** only obsolete or empty sections, or merge into a clearer structure. Do not drop project-specific URLs or course instructions without cause.

3. **Write or update `AGENTS.md`**
   - **Purpose**: orient another agent in one pass—**not** a duplicate of the full README.
   - Include:
     - **Top-level map**: each important directory and its role (1–2 lines each).
     - **Key files**: configs (`pyproject.toml`, `opencode.json`), `test_cases/CONFIG`, critical scripts.
     - **Execution surfaces**: how tests/builds/evals are invoked (pointer to README for full commands).
     - **Conventions**: where to add tests, where outputs go (`output/`), branch/PR expectations if obvious from `.github/`.
     - **Pointers**: project `.cursor/skills/`, MCP notes, security cautions (secrets, `output/`).
   - Filename is **`AGENTS.md`** (repository root), not `Agents.md`, unless the repo already standardizes another casing—prefer consistency with existing files.

4. **Verify**
   - Links in README/AGENTS use **repo-relative paths** where helpful.
   - No invented commands: every command should trace to a real file or documented script in the tree.

## Anti-patterns

- Do not move prerequisites below long narrative or feature lists.
- Do not dump the entire tree; summarize **architecturally** in AGENTS.md.
- Do not strip security warnings (secrets, local-only keys) if the codebase documents them.
