#!/usr/bin/env python3
"""
Candidate roster review using an LLM-as-judge pattern (OpenAI-compatible Chat Completions).

Reuses the JSON verdict shape from judge_evaluation_phase2_phase3.py, extended per dimension.

Dependencies:
  uv run --with pyyaml scripts/candidate_llm_judge_review.py ...

Env (same family as run_nist_llm_evaluation.py):
  OPENAI_API_KEY   — bearer token (required unless --dry-run)
  OPENAI_BASE_URL  — default http://localhost:1234/v1
  NIST_EVAL_MODEL  — model id

Optional evidence search (same keys as adk-ralph WebSearchTool):
  SERPAPI_API_KEY or BRAVE_SEARCH_API_KEY

Outputs: output/candidate_judge/candidate_review_<run_id>.json (and optional --out path).

Assistive only — not electoral or legal certification; human review is authoritative.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as e:  # pragma: no cover
    raise SystemExit(
        "PyYAML is required. Example: uv run --with pyyaml "
        f"{Path(__file__).name} --help"
    ) from e

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = REPO_ROOT / "output" / "candidate_judge"
_LL_CANDIDATES = REPO_ROOT.parent / "projects" / "ll" / "_candidates" / "candidates.yml"
DEFAULT_CANDIDATES_YML = _LL_CANDIDATES if _LL_CANDIDATES.is_file() else None
DEFAULT_OPENAI_BASE_URL = "http://localhost:1234/v1"
DEFAULT_MODEL = "unrestricted-knowledge-will-not-refuse-15b"

SYSTEM_JUDGE = """You are an assistive fact-check reviewer for a public election candidate roster (not a legal authority).
Score each dimension using Compliant (C), Partially Compliant (P), or Non-Compliant (N).

Rules:
- Embellishment in campaign-style accomplishments is ALLOWED if clearly rhetorical; flag unsupported factual claims as P or N.
- Prefer evidence in the provided excerpts and search snippets; if evidence is thin, lower confidence and use P or N.
- Social links: C only if they plausibly belong to this candidate; P if uncertain; N if broken, wrong person, or impersonation risk.
- headshot_vs_campaign_imagery: use the separate imagery_same_person block when provided; otherwise base only on URLs and excerpts.

Output a single JSON object (no markdown fences) with exactly these keys:
{
  "identity_office": { "draft_label": "C"|"P"|"N", "confidence": 0.0-1.0, "rationale": "...", "criterion_scores": {}, "concerns": [], "recommended_human_label": "C"|"P"|"N" },
  "party": { ... same shape ... },
  "social_web_links": { ... },
  "accomplishments": { ... },
  "previous_positions_titles": { ... },
  "headshot_vs_campaign_imagery": { ... },
  "human_review_required": true|false,
  "aggregate_draft_label": "C"|"P"|"N"
}

Choose aggregate_draft_label as the worst (most severe) among dimensions: N > P > C.
"""

SYSTEM_VISION = """You compare two images of a political candidate. Output a single JSON object (no markdown):
{
  "draft_label": "C"|"P"|"N",
  "confidence": 0.0-1.0,
  "rationale": "short paragraph",
  "concerns": ["..."],
  "recommended_human_label": "C"|"P"|"N"
}
C = very likely the same person; P = uncertain or different angle/lighting; N = likely different person or stock/unrelated photo.
Name given for context only — decide from pixels."""


def _post_chat_messages(
    base_url: str,
    api_key: str,
    model: str,
    messages: list[dict[str, Any]],
    temperature: float,
    timeout: float,
) -> str:
    url = base_url.rstrip("/") + "/chat/completions"
    body = json.dumps(
        {
            "model": model,
            "temperature": temperature,
            "messages": messages,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        payload = json.load(resp)
    return str(payload["choices"][0]["message"]["content"])


def _extract_json_object(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```\s*$", "", text)
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("No JSON object in model output")
    return json.loads(text[start : end + 1])


def _fetch_url(url: str, timeout: float, max_bytes: int) -> dict[str, Any]:
    out: dict[str, Any] = {"url": url, "ok": False, "status_code": None, "content_type": None, "excerpt": "", "error": None}
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "candidate-llm-judge/1.0 (research; +https://nist-ai-trustworthy-eval)"},
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            out["status_code"] = resp.getcode()
            out["content_type"] = resp.headers.get_content_type()
            chunk = resp.read(max_bytes)
            text = chunk.decode("utf-8", errors="replace")
            out["excerpt"] = text[:8000]
            out["ok"] = 200 <= (out["status_code"] or 0) < 400
    except urllib.error.HTTPError as e:
        out["status_code"] = e.code
        out["error"] = f"HTTP {e.code}"
        try:
            out["excerpt"] = e.read(4000).decode("utf-8", errors="replace")
        except Exception:
            pass
    except Exception as e:  # noqa: BLE001
        out["error"] = repr(e)
    return out


def _brave_search(query: str, api_key: str, max_results: int, timeout: float) -> list[dict[str, str]]:
    q = urllib.parse.quote_plus(query)
    url = f"https://api.search.brave.com/res/v1/web/search?q={q}&count={max_results}"
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "X-Subscription-Token": api_key,
        },
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.load(resp)
    web = data.get("web") or {}
    results = web.get("results") or []
    hits: list[dict[str, str]] = []
    for r in results[:max_results]:
        hits.append(
            {
                "title": str(r.get("title") or ""),
                "url": str(r.get("url") or ""),
                "snippet": str(r.get("description") or ""),
            }
        )
    return hits


def _serpapi_search(query: str, api_key: str, max_results: int, timeout: float) -> list[dict[str, str]]:
    params = urllib.parse.urlencode(
        {"q": query, "api_key": api_key, "engine": "google", "num": str(max_results)}
    )
    url = f"https://serpapi.com/search.json?{params}"
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.load(resp)
    organic = data.get("organic_results") or []
    hits: list[dict[str, str]] = []
    for r in organic[:max_results]:
        hits.append(
            {
                "title": str(r.get("title") or ""),
                "url": str(r.get("link") or ""),
                "snippet": str(r.get("snippet") or ""),
            }
        )
    return hits


def _web_search(query: str, max_results: int, timeout: float) -> list[dict[str, str]]:
    brave = os.environ.get("BRAVE_SEARCH_API_KEY", "").strip()
    serp = os.environ.get("SERPAPI_API_KEY", "").strip()
    if serp:
        return _serpapi_search(query, serp, max_results, timeout)
    if brave:
        return _brave_search(query, brave, max_results, timeout)
    return []


def _resolve_headshot_url(
    raw: str | None,
    *,
    site_base_url: str | None,
    jekyll_root: Path,
) -> tuple[str | None, str | None]:
    """Returns (resolved_http_or_data_url, error_message)."""
    if not raw or str(raw).strip().lower() in ("null", "none", ""):
        return None, None
    s = str(raw).strip()
    if s.startswith(("http://", "https://")):
        return s, None
    if s.startswith("/"):
        base = (site_base_url or "").rstrip("/")
        if not base:
            return None, "relative_headshot_needs_site_base_url"
        return base + s, None
    path = jekyll_root / s.lstrip("/")
    if not path.is_file():
        return None, f"local_headshot_missing:{path}"
    suffix = path.suffix.lower()
    mime = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp", ".gif": "image/gif"}.get(
        suffix, "application/octet-stream"
    )
    data = path.read_bytes()
    if len(data) > 4_000_000:
        return None, "local_headshot_too_large"
    b64 = base64.standard_b64encode(data).decode("ascii")
    return f"data:{mime};base64,{b64}", None


def _vision_compare(
    *,
    base_url: str,
    api_key: str,
    model: str,
    candidate_name: str,
    url_a: str,
    url_b: str,
    temperature: float,
    timeout: float,
) -> tuple[dict[str, Any] | None, str | None]:
    user_content: list[dict[str, Any]] = [
        {
            "type": "text",
            "text": f'Candidate name (context): "{candidate_name}". Image 1 is roster headshot; image 2 is campaign reference. Same person?',
        },
        {"type": "image_url", "image_url": {"url": url_a}},
        {"type": "image_url", "image_url": {"url": url_b}},
    ]
    messages = [
        {"role": "system", "content": SYSTEM_VISION},
        {"role": "user", "content": user_content},
    ]
    try:
        raw = _post_chat_messages(base_url, api_key, model, messages, temperature, timeout)
        parsed = _extract_json_object(raw)
        return parsed, None
    except Exception as e:  # noqa: BLE001
        return None, repr(e)


def _default_dimension_n(error: str) -> dict[str, Any]:
    return {
        "draft_label": "N",
        "confidence": 0.0,
        "rationale": error,
        "criterion_scores": {},
        "concerns": [error],
        "recommended_human_label": "N",
    }


def _collect_candidate_urls(c: dict[str, Any]) -> list[str]:
    keys = (
        "website_url",
        "facebook_url",
        "instagram_url",
        "linkedin_url",
        "headshot_url",
        "campaign_reference_image_url",
    )
    urls: list[str] = []
    for k in keys:
        v = c.get(k)
        if v and isinstance(v, str) and v.strip().lower() not in ("null", "") and v.startswith(("http://", "https://")):
            urls.append(v.strip())
    return urls


def _run_judge_for_candidate(
    *,
    base_url: str,
    api_key: str,
    model: str,
    temperature: float,
    timeout: float,
    candidate: dict[str, Any],
    evidence_fetch: list[dict[str, Any]],
    search_hits: list[dict[str, str]],
    imagery_block: dict[str, Any] | None,
) -> dict[str, Any]:
    payload = {
        "candidate_record": candidate,
        "evidence_fetch": evidence_fetch,
        "search_hits": search_hits,
        "imagery_same_person": imagery_block,
    }
    user = (
        "Evaluate the candidate record below.\n\n```json\n"
        + json.dumps(payload, indent=2, ensure_ascii=False)
        + "\n```"
    )
    messages = [{"role": "system", "content": SYSTEM_JUDGE}, {"role": "user", "content": user}]
    raw = _post_chat_messages(base_url, api_key, model, messages, temperature, timeout)
    return _extract_json_object(raw)


def _dry_dimensions(msg: str) -> dict[str, Any]:
    d = _default_dimension_n(msg)
    d["draft_label"] = "P"
    d["recommended_human_label"] = "P"
    d["rationale"] = msg
    return d


def review_candidates(
    *,
    candidates_yml: Path,
    base_url: str,
    api_key: str,
    model: str,
    temperature: float,
    timeout: float,
    fetch_timeout: float,
    delay_s: float,
    limit: int | None,
    ids: set[int] | None,
    dry_run: bool,
    skip_vision: bool,
    site_base_url: str | None,
    search_max: int,
    skip_fetch: bool,
) -> dict[str, Any]:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    text = candidates_yml.read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    rows: list[dict[str, Any]] = list(data.get("candidates") or [])
    jekyll_root = candidates_yml.resolve().parent.parent

    out_candidates: list[dict[str, Any]] = []
    n = 0
    for c in rows:
        cid = c.get("id")
        if ids is not None and int(cid) not in ids:
            continue
        n += 1
        if limit is not None and n > limit:
            break

        name = str(c.get("name") or "")
        evidence_urls = _collect_candidate_urls(c)
        if skip_fetch:
            evidence_fetch = []
        else:
            evidence_fetch = [_fetch_url(u, fetch_timeout, 48_000) for u in evidence_urls]

        query = f"{name} {c.get('office') or c.get('position') or ''} Texas candidate"
        search_hits = _web_search(query.strip(), search_max, timeout)
        for h in search_hits:
            if h.get("url"):
                evidence_urls.append(h["url"])

        # Imagery: headshot vs optional campaign_reference_image_url
        head_raw = c.get("headshot_url")
        camp_raw = c.get("campaign_reference_image_url")
        head_resolved, head_err = _resolve_headshot_url(
            head_raw if isinstance(head_raw, str) else None,
            site_base_url=site_base_url,
            jekyll_root=jekyll_root,
        )
        camp_resolved, camp_err = _resolve_headshot_url(
            camp_raw if isinstance(camp_raw, str) else None,
            site_base_url=site_base_url,
            jekyll_root=jekyll_root,
        )

        imagery_verdict: dict[str, Any]
        vision_json: dict[str, Any] | None = None
        vision_err: str | None = None

        if not head_resolved:
            imagery_verdict = {
                "status": "skipped_no_headshot",
                "headshot_resolved_url": None,
                "campaign_resolved_url": camp_resolved,
            }
        elif not camp_resolved:
            imagery_verdict = {
                "status": "skipped_no_campaign_reference",
                "headshot_resolved_url": head_resolved,
                "campaign_resolved_url": None,
            }
        elif head_err or camp_err:
            imagery_verdict = {
                "status": "skipped_local_path_unresolved",
                "headshot_resolved_url": head_resolved,
                "campaign_resolved_url": camp_resolved,
                "error": head_err or camp_err,
            }
        elif skip_vision or dry_run:
            imagery_verdict = {
                "status": "vision_unavailable",
                "headshot_resolved_url": head_resolved[:120] + "..."
                if head_resolved.startswith("data:")
                else head_resolved,
                "campaign_resolved_url": camp_resolved[:120] + "..."
                if camp_resolved and camp_resolved.startswith("data:")
                else camp_resolved,
            }
        else:
            vision_json, vision_err = _vision_compare(
                base_url=base_url,
                api_key=api_key,
                model=model,
                candidate_name=name,
                url_a=head_resolved,
                url_b=camp_resolved,
                temperature=temperature,
                timeout=timeout,
            )
            imagery_verdict = {
                "status": "compared" if vision_json else "vision_unavailable",
                "headshot_resolved_url": head_resolved[:80] + "...(data)"
                if head_resolved.startswith("data:")
                else head_resolved,
                "campaign_resolved_url": camp_resolved[:80] + "...(data)"
                if camp_resolved.startswith("data:")
                else camp_resolved,
                "draft_label": (vision_json or {}).get("draft_label"),
                "confidence": (vision_json or {}).get("confidence"),
                "rationale": (vision_json or {}).get("rationale"),
                "concerns": (vision_json or {}).get("concerns"),
                "recommended_human_label": (vision_json or {}).get("recommended_human_label"),
                "raw_model_response": None,
                "vision_error": vision_err,
            }

        imagery_block = vision_json if vision_json else None

        judge_error: str | None = None
        if dry_run:
            dims = {k: _dry_dimensions("--dry-run") for k in (
                "identity_office",
                "party",
                "social_web_links",
                "accomplishments",
                "previous_positions_titles",
                "headshot_vs_campaign_imagery",
            )}
            dims["headshot_vs_campaign_imagery"]["rationale"] = (
                "Dry run — no LLM call. See imagery_same_person for vision status."
            )
            verdict = {
                **dims,
                "human_review_required": True,
                "aggregate_draft_label": "P",
            }
        else:
            try:
                verdict = _run_judge_for_candidate(
                    base_url=base_url,
                    api_key=api_key,
                    model=model,
                    temperature=temperature,
                    timeout=timeout,
                    candidate=c,
                    evidence_fetch=evidence_fetch,
                    search_hits=search_hits,
                    imagery_block=imagery_block,
                )
            except Exception as e:  # noqa: BLE001
                judge_error = repr(e)
                verdict = {
                    "identity_office": _default_dimension_n(judge_error),
                    "party": _default_dimension_n(judge_error),
                    "social_web_links": _default_dimension_n(judge_error),
                    "accomplishments": _default_dimension_n(judge_error),
                    "previous_positions_titles": _default_dimension_n(judge_error),
                    "headshot_vs_campaign_imagery": _default_dimension_n(judge_error),
                    "human_review_required": True,
                    "aggregate_draft_label": "N",
                }

        dim_keys = (
            "identity_office",
            "party",
            "social_web_links",
            "accomplishments",
            "previous_positions_titles",
            "headshot_vs_campaign_imagery",
        )
        dimensions = {k: verdict.get(k) or _default_dimension_n("missing_dimension") for k in dim_keys}

        human_review = bool(verdict.get("human_review_required", True))
        if judge_error:
            human_review = True
        if imagery_verdict.get("status") not in ("compared", "skipped_no_campaign_reference", "skipped_no_headshot"):
            human_review = True

        out_candidates.append(
            {
                "candidate_id": int(cid),
                "name": name,
                "dimensions": dimensions,
                "evidence_urls": list(dict.fromkeys(evidence_urls)),
                "search_hits": search_hits,
                "evidence_fetch": evidence_fetch,
                "imagery_same_person": imagery_verdict,
                "human_review_required": human_review,
                "aggregate_draft_label": verdict.get("aggregate_draft_label") or "P",
                "judge_error": judge_error,
            }
        )

        if delay_s > 0:
            time.sleep(delay_s)

    return {
        "run_id": run_id,
        "model": model,
        "base_url": base_url,
        "temperature": temperature,
        "candidates_yml": str(candidates_yml.resolve()),
        "candidates": out_candidates,
    }


def main() -> None:
    p = argparse.ArgumentParser(description="LLM-as-judge review for candidate YAML roster.")
    p.add_argument(
        "--candidates-yml",
        type=Path,
        default=None,
        help="Path to candidates.yml (default: $CANDIDATES_YML or sibling projects/ll/_candidates/candidates.yml)",
    )
    p.add_argument("--limit", type=int, default=None, help="Max candidates to process (after --id filter).")
    p.add_argument("--id", type=int, action="append", dest="ids", help="Restrict to candidate id (repeatable).")
    p.add_argument("--temperature", type=float, default=0.2)
    p.add_argument("--timeout", type=float, default=180.0, help="LLM HTTP timeout (seconds).")
    p.add_argument("--fetch-timeout", type=float, default=25.0, help="Evidence URL fetch timeout.")
    p.add_argument("--delay", type=float, default=0.3, help="Seconds between candidates.")
    p.add_argument("--out", type=Path, default=None, help="Output JSON path.")
    p.add_argument("--dry-run", action="store_true", help="Skip LLM calls; still fetches URLs if not skipped.")
    p.add_argument("--skip-fetch", action="store_true", help="Do not HTTP-fetch candidate URLs (still may search).")
    p.add_argument("--skip-vision", action="store_true", help="Do not call multimodal compare for headshot vs campaign.")
    p.add_argument(
        "--site-base-url",
        type=str,
        default=os.environ.get("CANDIDATE_SITE_BASE_URL", "").strip() or None,
        help="Origin for site-relative headshots (e.g. https://example.com). Env: CANDIDATE_SITE_BASE_URL.",
    )
    p.add_argument("--search-max", type=int, default=5, help="Max web search hits per candidate.")
    args = p.parse_args()

    cyml = args.candidates_yml
    if cyml is None:
        env_p = os.environ.get("CANDIDATES_YML", "").strip()
        cyml = Path(env_p) if env_p else DEFAULT_CANDIDATES_YML
    if cyml is None or not cyml.is_file():
        raise SystemExit(
            "Specify --candidates-yml, set CANDIDATES_YML, or place projects/ll next to this repo."
        )

    base_url = os.environ.get("OPENAI_BASE_URL", DEFAULT_OPENAI_BASE_URL)
    api_key = os.environ.get("OPENAI_API_KEY", "")
    model = os.environ.get("NIST_EVAL_MODEL", DEFAULT_MODEL)

    if not args.dry_run and not api_key:
        raise SystemExit("OPENAI_API_KEY is not set (or use --dry-run).")

    ids_set = set(args.ids) if args.ids else None

    payload = review_candidates(
        candidates_yml=cyml,
        base_url=base_url,
        api_key=api_key or "dry-run",
        model=model,
        temperature=args.temperature,
        timeout=args.timeout,
        fetch_timeout=args.fetch_timeout,
        delay_s=args.delay,
        limit=args.limit,
        ids=ids_set,
        dry_run=args.dry_run,
        skip_vision=args.skip_vision,
        site_base_url=args.site_base_url,
        search_max=args.search_max,
        skip_fetch=args.skip_fetch,
    )

    out_path = args.out
    if out_path is None:
        DEFAULT_OUT_DIR.mkdir(parents=True, exist_ok=True)
        out_path = DEFAULT_OUT_DIR / f"candidate_review_{payload['run_id']}.json"
        latest = DEFAULT_OUT_DIR / "latest.json"
        latest.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
