# LaTeX sections critique (`output/results/latex-sections*.json`)

**Purpose:** After section JSON exists (e.g. `latex-sections-stub.json` or fuller exports), run a **critique pass** that grades each section, checks claims against NIST Quiz #3 artifacts, and verifies that **Results** align with **Discussion** / **Conclusion**.

## 1. Regenerate ground truth (recommended)

Refresh `output/results/nist_eval_latest.json` (and rubric TeX when `nist_quiz_scores.json` has entries) per `test_cases/CONFIG`:

```bash
python scripts/run_coursework_outputs.py                 # live NIST driver + rubric when scores exist
python scripts/run_coursework_outputs.py --skip-nist-eval  # manifest + rubric only
```

## 2. Optional: numeric consistency hints

Emits `output/article_iterations/critique/numeric-consistency.json` (tokens in LaTeX fragments vs values appearing in summary JSON). Safe to run without LM Studio.

```bash
python scripts/critique_latex_sections_stub.py
```

## 3. Run the critique agent (rd-agent)

From repo root, with submodules and LM Studio per `SUBMODULES.md` / `skills/rd-agent-mcp-operator/SKILL.md`:

- Spec: [`agents/rd-agent.yaml`](./agents/rd-agent.yaml)
- Primary artifact: `output/article_iterations/critique/latex-sections-critique.json` (structured grades + claim audit + cross-section consistency).

Adjust `LM_STUDIO_BASE_URL` in the YAML if your server is not at `192.168.0.13:1234`.

## Relationship to `article_sections/`

[`test_cases/article_sections/`](../article_sections/) refines **`src/sec/*.tex`**. This bundle reviews **JSON bundles** under **`output/results/`** that map logical section names to LaTeX strings—useful for pipelines that assemble the article from JSON before or alongside `.tex` sources.
