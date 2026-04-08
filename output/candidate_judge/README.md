# Candidate LLM-as-judge outputs

This directory holds **assistive** review runs for political candidate YAML rosters. These JSON files are **not** electoral certification, legal findings, or a substitute for human editorial review before publication.

## Artifacts

- `candidate_review_<run_id>.json` — full run (see schema [`../../schemas/candidate_review.schema.json`](../../schemas/candidate_review.schema.json)).
- `latest.json` — copy of the most recent run from the default driver path.

## How to run

From the repo root, with PyYAML:

```bash
uv run --with pyyaml scripts/candidate_llm_judge_review.py \
  --candidates-yml /path/to/projects/ll/_candidates/candidates.yml \
  --limit 5
```

Environment (same family as `run_nist_llm_evaluation.py`):

- `OPENAI_API_KEY` — required unless `--dry-run`
- `OPENAI_BASE_URL` — default `http://localhost:1234/v1`
- `NIST_EVAL_MODEL` — model id

Optional web evidence (same keys as **adk-ralph** `web_search`):

- `SERPAPI_API_KEY` or `BRAVE_SEARCH_API_KEY`

Optional imagery:

- `campaign_reference_image_url` on a candidate row (documented in YAML `metadata.field_descriptions`) for **headshot vs campaign** multimodal compare.
- `CANDIDATE_SITE_BASE_URL` or `--site-base-url` to resolve site-relative `headshot_url` values for vision APIs.

Flags: `--dry-run`, `--skip-vision`, `--skip-fetch`, `--id` (repeatable), `--limit`.

## Human authority

Per [`knowledge_base/opencode/NIST_JUDGE_INSTRUCTOR_SYSTEM.md`](../../knowledge_base/opencode/NIST_JUDGE_INSTRUCTOR_SYSTEM.md), automated judge output is **triage**. Editors should set final pass/fail on names, party, links, bios, and images.

## Registry sync

To merge a run into the LLM-as-a-judge registry:

```bash
python3 /path/to/LLM-as-a-judge/scripts/sync_candidate_review_registry.py \
  --input output/candidate_judge/latest.json
```

See the **Candidate review registry** section in the LLM-as-a-judge repo: `LLM-as-a-judge/output/results/README.md` (sibling checkout under the same parent directory as this repo).
