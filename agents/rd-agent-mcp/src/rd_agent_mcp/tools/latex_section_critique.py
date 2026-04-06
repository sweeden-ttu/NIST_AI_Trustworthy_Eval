"""Per-section LaTeX critique bundles, hybrid RAG ground truth, merge helpers."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Literal

from rd_agent_mcp.vectorstore.chroma import ChromaStore
from rd_agent_mcp.vectorstore.embeddings import SyncLMStudioEmbeddings

GroundTruthMode = Literal["truncate", "rag"]

DEFAULT_Q1_REL = "output/results/q1-summary.json"
DEFAULT_Q2_REL = "output/results/q2/openssl_run.json"
DEFAULT_Q3_REL = "output/results/q3-cipher-summary.json"
DEFAULT_CRITIQUE_REL = "output/article_iterations/critique/latex-sections-critique.json"
DEFAULT_NUMERIC_REL = "output/article_iterations/critique/numeric-consistency.json"
DEFAULT_LATEX_GLOB = "output/results/latex-sections*.json"
DEFAULT_CRITIQUE_COLLECTION = "latex_critique_ground_truth"

TOC_MAX_CHARS_PER_FILE = 2048
_CHUNK_DELIM = "\n\n--- retrieved chunks ---\n\n"


def project_key_for_root(project_root: Path) -> str:
    return hashlib.sha256(str(project_root.resolve()).encode()).hexdigest()[:16]


def resolve_under_root(project_root: str | Path, relative: str) -> Path:
    """Resolve a path under project_root; raise ValueError if outside root."""
    root = Path(project_root).resolve()
    rel = Path(relative)
    if rel.is_absolute():
        raise ValueError("relative path must not be absolute")
    candidate = (root / rel).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as e:
        raise ValueError(f"path escapes project_root: {relative}") from e
    return candidate


def _strip_json_fence(text: str) -> str:
    text = text.strip()
    if not text.startswith("```"):
        return text
    lines = text.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines)


def parse_critique_json_response(raw: str) -> Any:
    """Parse model output; strip optional markdown fences."""
    return json.loads(_strip_json_fence(raw))


def _truncate(s: str, max_chars: int) -> str:
    if len(s) <= max_chars:
        return s
    return s[:max_chars] + "\n… [truncated] …\n"


def _type_hint(value: Any, max_depth: int = 0) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return f"string[{len(value)} chars]"
    if isinstance(value, list):
        return f"array[{len(value)}]"
    if isinstance(value, dict):
        n = len(value)
        if max_depth <= 0:
            return f"object[{n} keys]"
        keys = list(value.keys())[:8]
        inner = ", ".join(f"{k}:{_type_hint(value[k], max_depth - 1)}" for k in keys)
        more = f", +{n - len(keys)} more" if n > len(keys) else ""
        return f"object[{n} keys]: {inner}{more}"
    return type(value).__name__


def build_toc_from_file(path: Path) -> str:
    """Tiny deterministic TOC: top-level JSON keys + type/size hints, or non-JSON fallback."""
    if not path.is_file():
        return f"missing_file: {path.name}\n"
    raw = path.read_text(encoding="utf-8", errors="replace")
    lines = raw.splitlines()
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError:
        return f"non_json_lines:{len(lines)}\nfirst_line:{lines[0][:200] if lines else ''}\n"

    if isinstance(obj, dict):
        parts: list[str] = []
        for k in sorted(obj.keys(), key=str):
            parts.append(f"- {k}: {_type_hint(obj[k])}")
        text = "toc_json_top_level:\n" + "\n".join(parts) + "\n"
    elif isinstance(obj, list):
        text = f"toc_json_root_array: len={len(obj)} elem={_type_hint(obj[0]) if obj else 'empty'}\n"
    else:
        text = f"toc_json_scalar: {_type_hint(obj)}\n"
    if len(text) > TOC_MAX_CHARS_PER_FILE:
        return text[: TOC_MAX_CHARS_PER_FILE - 20] + "\n… [toc truncated] …\n"
    return text


def _overlap_chars(chunk_chars: int) -> int:
    return max(1, int(chunk_chars * 0.15))


def chunk_text(text: str, chunk_chars: int) -> list[str]:
    """Sliding windows with ~15% overlap."""
    if chunk_chars <= 0:
        raise ValueError("chunk_chars must be positive")
    if not text:
        return []
    step = max(1, chunk_chars - _overlap_chars(chunk_chars))
    chunks: list[str] = []
    i = 0
    while i < len(text):
        piece = text[i : i + chunk_chars]
        chunks.append(piece)
        if i + chunk_chars >= len(text):
            break
        i += step
    return chunks


def _sidecar_path(persist_directory: Path) -> Path:
    persist_directory.mkdir(parents=True, exist_ok=True)
    return persist_directory / "latex_critique_index_state.json"


def _load_sidecar(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"files": {}}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"files": {}}


def _save_sidecar(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _delete_chunks_for_source(
    store: ChromaStore, project_key: str, source: str
) -> None:
    coll = store.collection
    res = coll.get(
        where={"$and": [{"project_key": project_key}, {"source": source}]},
    )
    ids = res.get("ids") or []
    if ids:
        coll.delete(ids=ids)


def index_ground_truth(
    project_root: str | Path,
    *,
    q1_path: str | None = None,
    q2_path: str | None = None,
    q3_path: str | None = None,
    collection_name: str = DEFAULT_CRITIQUE_COLLECTION,
    chunk_chars: int = 1600,
    force_reindex: bool = False,
    chroma_persist_directory: str | Path | None = None,
    embedding_model: str | None = None,
    embedding_base_url: str | None = None,
) -> dict[str, Any]:
    """
    Chunk and embed q1/q2/q3 JSON files into a dedicated Chroma collection.
    Returns chunks_written, chunks_skipped, per-source breakdown.
    """
    root = Path(project_root).resolve()
    if not root.is_dir():
        raise ValueError(f"project_root is not a directory: {root}")

    rels = {
        "q1": q1_path or DEFAULT_Q1_REL,
        "q2": q2_path or DEFAULT_Q2_REL,
        "q3": q3_path or DEFAULT_Q3_REL,
    }
    pk = project_key_for_root(root)
    persist = (
        Path(chroma_persist_directory).resolve()
        if chroma_persist_directory
        else (root / ".chromadb_latex_critique")
    )
    sidecar_file = _sidecar_path(persist)
    sidecar = _load_sidecar(sidecar_file)
    files_state: dict[str, Any] = sidecar.setdefault("files", {})

    emb_model = embedding_model or os.environ.get(
        "EMBEDDING_MODEL", "text-embedding-nomic-embed-text-v1.5"
    )
    embedder = SyncLMStudioEmbeddings(model=emb_model, base_url=embedding_base_url)
    store = ChromaStore(
        persist_directory=str(persist),
        collection_name=collection_name,
        embedding_function=embedder,
    )

    chunks_written = 0
    chunks_skipped = 0
    sources_out: list[dict[str, Any]] = []

    for source, rel in rels.items():
        path = resolve_under_root(root, rel)
        if not path.is_file():
            sources_out.append(
                {"source": source, "path": rel, "status": "missing", "chunks": 0}
            )
            continue

        raw_bytes = path.read_bytes()
        sha = hashlib.sha256(raw_bytes).hexdigest()
        entry = files_state.get(rel, {})
        if (
            not force_reindex
            and entry.get("sha256") == sha
            and entry.get("chunk_count", 0) > 0
        ):
            n = int(entry["chunk_count"])
            chunks_skipped += n
            sources_out.append(
                {
                    "source": source,
                    "path": rel,
                    "status": "skipped_unchanged",
                    "chunks": n,
                }
            )
            continue

        try:
            obj = json.loads(raw_bytes.decode("utf-8"))
            text = json.dumps(obj, indent=2)
        except (UnicodeDecodeError, json.JSONDecodeError):
            text = raw_bytes.decode("utf-8", errors="replace")

        pieces = chunk_text(text, chunk_chars)
        if not pieces:
            pieces = [""]

        _delete_chunks_for_source(store, pk, source)

        doc_ids: list[str] = []
        metas: list[dict[str, Any]] = []
        for i, piece in enumerate(pieces):
            doc_id = f"{pk}:{source}:{i}"
            doc_ids.append(doc_id)
            metas.append(
                {
                    "project_key": pk,
                    "source": source,
                    "path": rel,
                    "chunk_index": str(i),
                    "content_sha256": sha,
                }
            )

        store.add_texts(
            texts=pieces,
            doc_ids=doc_ids,
            metadatas=metas,
        )
        chunks_written += len(pieces)
        files_state[rel] = {"sha256": sha, "chunk_count": len(pieces)}
        sources_out.append(
            {
                "source": source,
                "path": rel,
                "status": "indexed",
                "chunks": len(pieces),
            }
        )

    sidecar["project_key"] = pk
    _save_sidecar(sidecar_file, sidecar)

    return {
        "chunks_written": chunks_written,
        "chunks_skipped": chunks_skipped,
        "sources": sources_out,
        "collection_name": collection_name,
        "chroma_persist_directory": str(persist),
        "project_key": pk,
    }


def retrieve_ground_truth(
    project_root: str | Path,
    *,
    section_key: str,
    latex_fragment: str,
    numeric_hint_json: Any | None = None,
    top_k: int = 12,
    per_source_k: int = 4,
    collection_name: str = DEFAULT_CRITIQUE_COLLECTION,
    chroma_persist_directory: str | Path | None = None,
    embedding_model: str | None = None,
    embedding_base_url: str | None = None,
) -> dict[str, Any]:
    """Retrieve ranked chunks per source (q1/q2/q3); no LLM."""
    root = Path(project_root).resolve()
    pk = project_key_for_root(root)
    persist = (
        Path(chroma_persist_directory).resolve()
        if chroma_persist_directory
        else (root / ".chromadb_latex_critique")
    )
    emb_model = embedding_model or os.environ.get(
        "EMBEDDING_MODEL", "text-embedding-nomic-embed-text-v1.5"
    )
    embedder = SyncLMStudioEmbeddings(model=emb_model, base_url=embedding_base_url)
    store = ChromaStore(
        persist_directory=str(persist),
        collection_name=collection_name,
        embedding_function=embedder,
    )

    hint_s = ""
    if numeric_hint_json is not None:
        if isinstance(numeric_hint_json, str):
            hint_s = numeric_hint_json
        else:
            hint_s = json.dumps(numeric_hint_json, indent=2)
    query = (
        f"section={section_key}\n\nlatex:\n{latex_fragment}\n\nnumeric_hints:\n{hint_s}"
    )

    pooled: list[dict[str, Any]] = []
    for source in ("q1", "q2", "q3"):
        hits = store.search(
            query=query,
            k=per_source_k,
            where={"$and": [{"project_key": pk}, {"source": source}]},
        )
        pooled.extend(hits)

    pooled.sort(key=lambda x: (x.get("distance") is None, x.get("distance") or 0.0))
    if top_k > 0 and len(pooled) > top_k:
        pooled = pooled[:top_k]

    out_chunks: list[dict[str, Any]] = []
    for h in pooled:
        meta = h.get("metadata") or {}
        out_chunks.append(
            {
                "id": h.get("id"),
                "content": h.get("content", ""),
                "metadata": meta,
                "distance": h.get("distance"),
            }
        )

    return {"chunks": out_chunks, "section_key": section_key}


def _glob_latex_jsons(project_root: Path, pattern_from_root: str) -> list[Path]:
    parent = project_root
    parts = Path(pattern_from_root).parts
    if not parts:
        return []
    for p in parts[:-1]:
        parent = parent / p
    if not parent.is_dir():
        return []
    return sorted(parent.glob(parts[-1]))


def rel_under_root(project_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(project_root.resolve()))
    except ValueError:
        return str(path.resolve())


def list_latex_sections(
    project_root: str | Path,
    latex_glob: str = DEFAULT_LATEX_GLOB,
) -> dict[str, Any]:
    root = Path(project_root).resolve()
    files: list[dict[str, Any]] = []
    for p in _glob_latex_jsons(root, latex_glob):
        rel = rel_under_root(root, p)
        data = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            continue
        keys = sorted(data.keys())
        files.append({"path": rel, "section_keys": keys})

    crit_path = root / DEFAULT_CRITIQUE_REL
    num_path = root / DEFAULT_NUMERIC_REL
    return {
        "files": files,
        "critique_path": str(DEFAULT_CRITIQUE_REL) if crit_path.is_file() else None,
        "numeric_consistency_path": str(DEFAULT_NUMERIC_REL) if num_path.is_file() else None,
    }


def _critique_file_key(sections_by_file: dict[str, Any], latex_relative_path: str) -> str | None:
    if latex_relative_path in sections_by_file:
        return latex_relative_path
    base = Path(latex_relative_path).name
    for k in sections_by_file:
        if Path(k).name == base:
            return k
    return None


def _numeric_section_row(
    numeric_obj: dict[str, Any] | None, latex_relative_path: str, section_key: str
) -> dict[str, Any] | None:
    if not numeric_obj or "by_file" not in numeric_obj:
        return None
    base = Path(latex_relative_path).name
    by_file = numeric_obj["by_file"]
    block = by_file.get(base)
    if not isinstance(block, dict):
        return None
    sections = block.get("sections")
    if not isinstance(sections, dict):
        return None
    row = sections.get(section_key)
    return row if isinstance(row, dict) else None


def _load_json_optional(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else None


def get_section_bundle(
    project_root: str | Path,
    latex_relative_path: str,
    section_key: str,
    *,
    critique_path: str | None = None,
    numeric_path: str | None = None,
    q1_path: str | None = None,
    q2_path: str | None = None,
    q3_path: str | None = None,
    max_q1_chars: int = 14_000,
    max_q2_chars: int = 6_000,
    max_q3_chars: int = 8_000,
    ground_truth_mode: GroundTruthMode = "truncate",
    collection_name: str = DEFAULT_CRITIQUE_COLLECTION,
    chroma_persist_directory: str | Path | None = None,
    top_k: int = 12,
    per_source_k: int = 4,
    embedding_model: str | None = None,
    embedding_base_url: str | None = None,
) -> dict[str, Any]:
    root = Path(project_root).resolve()
    latex_path = resolve_under_root(root, latex_relative_path)
    data = json.loads(latex_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or section_key not in data:
        raise KeyError(f"section {section_key!r} not in {latex_relative_path}")
    fragment = data[section_key]
    if not isinstance(fragment, str):
        fragment = json.dumps(fragment)

    crit_rel = critique_path or DEFAULT_CRITIQUE_REL
    num_rel = numeric_path or DEFAULT_NUMERIC_REL
    critique_obj = _load_json_optional(resolve_under_root(root, crit_rel))
    critique_block = None
    if critique_obj and "sections_by_file" in critique_obj:
        sbf = critique_obj["sections_by_file"]
        if isinstance(sbf, dict):
            ck = _critique_file_key(sbf, latex_relative_path)
            if ck:
                file_entry = sbf.get(ck)
                if isinstance(file_entry, dict) and section_key in file_entry:
                    critique_block = file_entry[section_key]

    numeric_obj = _load_json_optional(resolve_under_root(root, num_rel))
    numeric_block = _numeric_section_row(numeric_obj, latex_relative_path, section_key)

    q1_r = q1_path or DEFAULT_Q1_REL
    q2_r = q2_path or DEFAULT_Q2_REL
    q3_r = q3_path or DEFAULT_Q3_REL
    paths = {
        "q1": resolve_under_root(root, q1_r),
        "q2": resolve_under_root(root, q2_r),
        "q3": resolve_under_root(root, q3_r),
    }

    ground_truth: dict[str, str] = {}
    if ground_truth_mode == "truncate":
        for key, rel in (("q1", q1_r), ("q2", q2_r), ("q3", q3_r)):
            p = paths[key]
            cap = {"q1": max_q1_chars, "q2": max_q2_chars, "q3": max_q3_chars}[key]
            if p.is_file():
                ground_truth[key] = _truncate(p.read_text(encoding="utf-8"), cap)
            else:
                ground_truth[key] = ""
    else:
        ret = retrieve_ground_truth(
            root,
            section_key=section_key,
            latex_fragment=fragment,
            numeric_hint_json=numeric_block,
            top_k=top_k,
            per_source_k=per_source_k,
            collection_name=collection_name,
            chroma_persist_directory=chroma_persist_directory,
            embedding_model=embedding_model,
            embedding_base_url=embedding_base_url,
        )
        by_src: dict[str, list[dict[str, Any]]] = {"q1": [], "q2": [], "q3": []}
        for ch in ret.get("chunks") or []:
            meta = ch.get("metadata") or {}
            src = meta.get("source")
            if src in by_src:
                by_src[src].append(ch)
        for src in by_src:
            by_src[src].sort(
                key=lambda x: (x.get("distance") is None, x.get("distance") or 0.0)
            )

        for key, rel in (("q1", q1_r), ("q2", q2_r), ("q3", q3_r)):
            p = paths[key]
            toc = build_toc_from_file(p)
            parts_body: list[str] = []
            for ch in by_src[key]:
                meta = ch.get("metadata") or {}
                idx = meta.get("chunk_index", "?")
                parts_body.append(f"### chunk {idx}\n{ch.get('content', '')}")
            body = "\n\n".join(parts_body) if parts_body else "(no retrieved chunks)"
            ground_truth[key] = f"{toc.strip()}{_CHUNK_DELIM}{body}"

    return {
        "latex_relative_path": latex_relative_path,
        "section_key": section_key,
        "latex_fragment": fragment,
        "critique_block": critique_block,
        "numeric_block": numeric_block,
        "ground_truth": ground_truth,
        "ground_truth_mode": ground_truth_mode,
    }


def task_from_agent_yaml(yaml_path: Path) -> str:
    try:
        import yaml  # type: ignore[import-untyped]
    except ModuleNotFoundError as e:
        raise RuntimeError("PyYAML is required to read agent yaml") from e
    spec = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    args = spec["command"]["args"]
    i = args.index("--task")
    return str(args[i + 1])


def build_section_critique_user_message(
    task_text: str,
    bundle: dict[str, Any],
    *,
    latex_relative_path: str | None = None,
    numeric_full_json: dict[str, Any] | None = None,
) -> str:
    """Build user message for one section (matches monolithic script structure)."""
    path = latex_relative_path or bundle["latex_relative_path"]
    section_key = bundle["section_key"]
    fragment = bundle["latex_fragment"]
    sections_payload = {path: {section_key: fragment}}

    numeric_slice: dict[str, Any] | None = None
    if bundle.get("numeric_block") is not None:
        base = Path(path).name
        numeric_slice = {
            "by_file": {
                base: {"sections": {section_key: bundle["numeric_block"]}},
            }
        }
    elif numeric_full_json is not None:
        numeric_slice = numeric_full_json

    gt = bundle["ground_truth"]
    user = (
        task_text
        + "\n\n## Section JSON files (relative paths as keys)\n```json\n"
        + json.dumps(sections_payload, indent=2)
        + "\n```\n\n## numeric-consistency.json (section slice)\n```json\n"
        + json.dumps(
            numeric_slice
            if numeric_slice is not None
            else {"note": "no numeric row for this section"},
            indent=2,
        )
        + "\n```\n\n## q1-summary.json (truncated or hybrid RAG)\n```json\n"
        + gt["q1"]
        + "\n```\n\n## q3-cipher-summary.json (truncated or hybrid RAG)\n```json\n"
        + gt["q3"]
        + "\n```\n\n## q2/openssl_run.json (truncated or hybrid RAG)\n```json\n"
        + gt["q2"]
        + "\n```\n"
    )
    return user


def merge_section_into_critique(
    base_critique: dict[str, Any],
    latex_relative_path: str,
    section_key: str,
    partial_section: dict[str, Any],
) -> dict[str, Any]:
    """Deep-merge one section; preserve top-level keys."""
    out = json.loads(json.dumps(base_critique))
    sbf = out.setdefault("sections_by_file", {})
    if not isinstance(sbf, dict):
        raise ValueError("sections_by_file must be a dict")
    ck = _critique_file_key(sbf, latex_relative_path)
    if ck is None:
        ck = latex_relative_path
        sbf[ck] = {}
    file_entry = sbf.setdefault(ck, {})
    if not isinstance(file_entry, dict):
        raise ValueError(f"sections_by_file[{ck}] must be a dict")
    file_entry[section_key] = partial_section
    return out


def build_cross_cutting_user_message(
    task_text: str,
    latex_relative_path: str,
    sections_subset: dict[str, str],
    ground_truth_truncate: dict[str, str],
    max_chars: int = 4000,
) -> str:
    """Prompt for cross_cutting only: abstract, results, discussion, conclusion."""
    payload = {latex_relative_path: sections_subset}
    gt = {k: _truncate(v, max_chars) for k, v in ground_truth_truncate.items()}
    return (
        task_text
        + "\n\n## Cross-cutting review only\n"
        "Fill **only** the JSON object's `cross_cutting` field: "
        "results_vs_discussion, results_vs_conclusion, abstract_vs_body. "
        "Respond with one JSON object: {\"cross_cutting\": { ... }} — no other keys.\n\n"
        "## Section excerpts\n```json\n"
        + json.dumps(payload, indent=2)
        + "\n```\n\n## Ground truth digest (q1 / q3 / q2)\n```\n"
        + "## q1\n"
        + gt.get("q1", "")
        + "\n## q3\n"
        + gt.get("q3", "")
        + "\n## q2\n"
        + gt.get("q2", "")
        + "\n```\n"
    )


def load_latex_subset_for_cross_cutting(
    project_root: str | Path,
    latex_relative_path: str,
    keys: tuple[str, ...] = ("abstract", "results", "discussion", "conclusion"),
) -> dict[str, str]:
    root = Path(project_root).resolve()
    path = resolve_under_root(root, latex_relative_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("latex json must be an object")
    out: dict[str, str] = {}
    for k in keys:
        v = data.get(k)
        out[k] = v if isinstance(v, str) else json.dumps(v)
    return out


def load_ground_truth_texts(
    project_root: str | Path,
    q1_path: str | None = None,
    q2_path: str | None = None,
    q3_path: str | None = None,
) -> dict[str, str]:
    root = Path(project_root).resolve()
    rels = {
        "q1": q1_path or DEFAULT_Q1_REL,
        "q2": q2_path or DEFAULT_Q2_REL,
        "q3": q3_path or DEFAULT_Q3_REL,
    }
    texts: dict[str, str] = {}
    for k, rel in rels.items():
        p = resolve_under_root(root, rel)
        texts[k] = p.read_text(encoding="utf-8") if p.is_file() else ""
    return texts
