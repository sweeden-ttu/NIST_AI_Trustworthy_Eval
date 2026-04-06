# Conda environment `NIST_AI_Trustworthy_Eval`

Reproducible **Miniconda** setup for course Autogen packages and NIST evaluation scripts.

## Create and install (one-time)

```bash
conda create -n NIST_AI_Trustworthy_Eval python=3.11 -y
conda activate NIST_AI_Trustworthy_Eval

# Same order as scripts/course/run-AgentEval.txt and run-nonAgentEval.txt
pip install autogen-agentchat==0.2.38
pip install autogen-agentchat autogen-core autogen-ext asyncio python-dotenv openai tiktoken streamlit arxiv ipykernel "autogen-ext[ollama]" "autogen-ext[http-tool]" "autogen-ext[chromadb]" langchain-community html2text bs4 pypdf python-docx autogenstudio==0.4.2.2
```

Non-interactive equivalent:

```bash
conda run -n NIST_AI_Trustworthy_Eval pip install autogen-agentchat==0.2.38
conda run -n NIST_AI_Trustworthy_Eval pip install autogen-agentchat autogen-core autogen-ext asyncio python-dotenv openai tiktoken streamlit arxiv ipykernel "autogen-ext[ollama]" "autogen-ext[http-tool]" "autogen-ext[chromadb]" langchain-community html2text bs4 pypdf python-docx autogenstudio==0.4.2.2
```

## Run NIST experiments (repo root)

```bash
conda activate NIST_AI_Trustworthy_Eval
cd /path/to/NIST_AI_Trustworthy_Eval

# No API / no LM Studio: validates JSON shape for all 14 items
python scripts/verify_nist_prompt_inventory.py

# Live run: start LM Studio (or other OpenAI-compatible server), then:
export OPENAI_API_KEY=lm-studio   # or your provider token
export OPENAI_BASE_URL=http://localhost:1234/v1
export NIST_EVAL_MODEL=unrestricted-knowledge-will-not-refuse-15b
python scripts/run_nist_llm_evaluation.py
```

After human rubric in `output/results/nist_quiz_scores.json`:

```bash
python scripts/emit_nist_rubric_table.py
```

## Notes

- **`nist_experiment_graph_loop.py`** (LangGraph + optional Docling) uses **`uv sync --extra nist-loop`** in the main README; it is not part of the Autogen pip bundle above.
- **`scripts/run_coursework_outputs.py`** is the **NIST Quiz #3** orchestrator (reads `test_cases/CONFIG`, runs `run_nist_llm_evaluation.py`, optional rubric TeX). It does **not** require matplotlib, pycryptodome, Pillow, or OpenSSL. Install those only if you **manually** regenerate legacy toy-crypto figures; see `scripts/README.md`.
