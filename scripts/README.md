# Scripts

## `run_coursework_outputs.py`

Regenerates **Q1–Q3 coursework artifacts** used by `src/ieee_journal.tex` (figures under `output/diagrams/`, JSON under `output/results/`).

**What it runs**

| Block | Output |
|-------|--------|
| Q1 | Toy AES-128 traces (`toy_aes128_trace.py`), Hamming PDFs (`q1-hamming-rounds.pdf`, ablations), `output/results/q1-summary.json` |
| Q2 | `openssl enc` AES-128-ECB/CBC on `assets/Secret.bmp` (creates a minimal BMP if missing), noise + header-fixed PDFs, `output/results/q2/openssl_run.json` |
| Q3 | `openssl s_client` to nine HTTPS hosts, summary JSON + `q3-*.pdf` (openssl snapshot; Wireshark captures still manual — see `output/diagrams/q3-wireshark/README.txt`) |

**Prerequisites**

- **Conda env** `rd-ralph-template` (or any env with the deps below).
- **Python:** `matplotlib`, `numpy`, **`pycryptodome`** (validates toy AES vs reference), **`Pillow`** (BMP previews for Q2).
- **`openssl`** on `PATH` (Q2 encryption + Q3 probes).
- **Network** for Q3 (outbound HTTPS to common sites; increase timeouts or edit host list if firewalled).

**Run (repo root)**

```bash
conda activate rd-ralph-template
python scripts/run_coursework_outputs.py
```

On success you should see:

```text
Q1 wrote q1-summary.json and q1-*.pdf
Q2 wrote output/results/q2/* and q2-*.pdf
Q3 wrote q3-cipher-summary.json and q3-*.pdf
Done. Outputs under output/results and output/diagrams
```

Then rebuild the PDF from `src/`:

```bash
cd src && latexmk -pdf -interaction=nonstopmode ieee_journal.tex
```

**Security note:** `openssl_run.json` contains **key and IV hex** for the Q2 run (for local reproducibility). Do not commit if your course or org forbids it; add `output/` to `.gitignore` or strip secrets before pushing.

**Related:** iterative LaTeX section agents live under [`test_cases/article_sections/`](../test_cases/article_sections/README.md).

---

## `generate_article_section_agents.py`

Regenerates the per-section agent YAML files under `test_cases/article_sections/sec00..sec09/agents/` (`rd-agent.yaml`, `adk-ralph.yaml`). Run after you change section filenames or want to refresh embedded instructions:

```bash
python scripts/generate_article_section_agents.py
```

---

## `critique_latex_sections_stub.py`

Compares every `output/results/latex-sections*.json` against coursework summaries (`q1-summary.json`, `q2/*.json`, `q3-cipher-summary.json`) and writes heuristic numeric-token hints for the **latex sections critique** agent:

```bash
python scripts/critique_latex_sections_stub.py
```

Output: `output/article_iterations/critique/numeric-consistency.json`. See [`test_cases/latex_sections_critique/README.md`](../test_cases/latex_sections_critique/README.md).

---

## `toy_aes128_trace.py`

Imported by `run_coursework_outputs.py` for the educational AES tracer (not production-safe crypto).

---

## `sync_cursor_lmstudio_models.py`

Keeps **Cursor**’s custom model list aligned with **LM Studio**:

1. Calls `GET …/v1/models` on `LM_STUDIO_BASE_URL` (same ids the IDE sends to the server).
2. Optionally unions with `lms ls --json --llm` (disk catalog).
3. Merges ids into `state.vscdb` → `aiSettings.userAddedModels` and `modelOverrideEnabled`, and sets `openAIBaseUrl` / `useOpenAIKey`.

**Prerequisites**

- `lms` on `PATH` (default install: `~/.lmstudio/bin/lms`).
- Cursor **quit** before writing (avoids SQLite locks).

**Examples**

```bash
export LM_STUDIO_BASE_URL=http://192.168.0.13:1234/v1
export LM_STUDIO_API_KEY=lm-studio

# Preview
python3 scripts/sync_cursor_lmstudio_models.py --dry-run --union-lms

# Apply (writes DB + optional backup)
python3 scripts/sync_cursor_lmstudio_models.py --union-lms --backup
```

Flags: `--include-embeddings`, `--lms-fallback-only`, `--cursor-db /path/to/state.vscdb`.

Preset-only names (e.g. `sgskkssks`) that never appear in `/v1/models` stay in Cursor if you added them earlier; this script only **adds** discovered ids (union), it does not remove existing entries.
