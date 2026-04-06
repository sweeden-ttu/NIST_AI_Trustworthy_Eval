"""Tests for per-section LaTeX critique helpers (no LM Studio by default)."""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from rd_agent_mcp.tools import latex_section_critique as lc
from rd_agent_mcp.vectorstore.embeddings import SyncLMStudioEmbeddings


def test_resolve_under_root_rejects_escape(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="escapes"):
        lc.resolve_under_root(tmp_path, "../outside")


def test_build_toc_from_json_dict(tmp_path: Path) -> None:
    p = tmp_path / "toc.json"
    p.write_text(json.dumps({"a": 1, "b": [1, 2], "c": {"x": 1}}), encoding="utf-8")
    out = lc.build_toc_from_file(p)
    assert "toc_json_top_level" in out
    assert "a: number" in out
    assert "b: array[2]" in out
    assert "c: object[1 keys]" in out


def test_merge_section_into_critique() -> None:
    base = {
        "critique_version": 1,
        "sections_by_file": {
            "out/stub.json": {
                "introduction": {"grades": {"letter": "C", "numeric": 60}},
            }
        },
        "cross_cutting": {"a": "b"},
    }
    partial = {
        "grades": {"letter": "B", "numeric": 80},
        "claims": [],
        "action_items": ["fix"],
    }
    out = lc.merge_section_into_critique(base, "out/stub.json", "introduction", partial)
    assert out["sections_by_file"]["out/stub.json"]["introduction"]["grades"]["letter"] == "B"
    assert out["cross_cutting"]["a"] == "b"


def test_get_section_bundle_truncate(tmp_path: Path) -> None:
    root = tmp_path
    (root / "out").mkdir(parents=True)
    (root / "out" / "stub.json").write_text(
        json.dumps({"methodology": "\\section{M}body"}),
        encoding="utf-8",
    )
    (root / "crit").mkdir(parents=True)
    (root / "crit" / "num.json").write_text(
        json.dumps(
            {
                "by_file": {
                    "stub.json": {
                        "sections": {
                            "methodology": {"char_count": 3},
                        }
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    (root / "q1.json").write_text('{"x": 1}', encoding="utf-8")
    (root / "q2.json").write_text('{"y": 2}', encoding="utf-8")
    (root / "q3.json").write_text('{"z": 3}', encoding="utf-8")

    b = lc.get_section_bundle(
        root,
        "out/stub.json",
        "methodology",
        numeric_path="crit/num.json",
        q1_path="q1.json",
        q2_path="q2.json",
        q3_path="q3.json",
        max_q1_chars=100,
        max_q2_chars=100,
        max_q3_chars=100,
        ground_truth_mode="truncate",
    )
    assert b["latex_fragment"] == "\\section{M}body"
    assert b["numeric_block"]["char_count"] == 3
    assert '"x": 1' in b["ground_truth"]["q1"]


def test_chunk_text_overlap() -> None:
    text = "a" * 100
    chunks = lc.chunk_text(text, chunk_chars=30)
    assert len(chunks) >= 3
    assert all(len(c) <= 30 for c in chunks)


def test_index_and_retrieve_with_mock_embeddings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path
    (root / "output" / "results").mkdir(parents=True)
    (root / "output" / "results" / "q2").mkdir(parents=True)
    (root / "output" / "results" / "q1-summary.json").write_text(
        json.dumps({"part1": "alpha " * 200, "part2": "beta " * 200}),
        encoding="utf-8",
    )
    (root / "output" / "results" / "q2" / "openssl_run.json").write_text('{"cmd": "openssl"}', encoding="utf-8")
    (root / "output" / "results" / "q3-cipher-summary.json").write_text('{"ciphers": []}', encoding="utf-8")

    def fake_embed_docs(self: SyncLMStudioEmbeddings, texts: list[str]) -> list[list[float]]:
        return [[0.01 * (i % 7 + 1)] * 16 for i in range(len(texts))]

    def fake_embed_query(self: SyncLMStudioEmbeddings, text: str) -> list[float]:
        return [0.05] * 16

    monkeypatch.setattr(SyncLMStudioEmbeddings, "embed_documents", fake_embed_docs)
    monkeypatch.setattr(SyncLMStudioEmbeddings, "embed_query", fake_embed_query)

    persist = root / "chroma_here"
    res = lc.index_ground_truth(
        root,
        collection_name="tcol",
        chunk_chars=400,
        force_reindex=True,
        chroma_persist_directory=str(persist),
        q1_path="output/results/q1-summary.json",
        q2_path="output/results/q2/openssl_run.json",
        q3_path="output/results/q3-cipher-summary.json",
    )
    assert res["chunks_written"] >= 3
    assert res["chunks_skipped"] == 0

    res2 = lc.index_ground_truth(
        root,
        collection_name="tcol",
        chunk_chars=400,
        force_reindex=False,
        chroma_persist_directory=str(persist),
    )
    assert res2["chunks_written"] == 0
    assert res2["chunks_skipped"] >= 3

    (root / "out").mkdir(parents=True)
    (root / "out" / "stub.json").write_text(
        json.dumps({"methodology": "text"}), encoding="utf-8"
    )

    ret = lc.retrieve_ground_truth(
        root,
        section_key="methodology",
        latex_fragment="AES discussion",
        top_k=8,
        per_source_k=3,
        collection_name="tcol",
        chroma_persist_directory=str(persist),
    )
    assert "chunks" in ret
    assert len(ret["chunks"]) <= 8
    sources = {c["metadata"].get("source") for c in ret["chunks"]}
    assert sources <= {"q1", "q2", "q3"}

    bundle = lc.get_section_bundle(
        root,
        "out/stub.json",
        "methodology",
        ground_truth_mode="rag",
        collection_name="tcol",
        chroma_persist_directory=str(persist),
    )
    assert bundle["ground_truth_mode"] == "rag"
    for k in ("q1", "q2", "q3"):
        assert "toc_json" in bundle["ground_truth"][k] or "missing_file" in bundle["ground_truth"][k]
        assert "retrieved chunks" in bundle["ground_truth"][k] or "no retrieved chunks" in bundle["ground_truth"][k]


def test_build_section_critique_user_message_contains_slice() -> None:
    bundle = {
        "latex_relative_path": "p/stub.json",
        "section_key": "intro",
        "latex_fragment": "hi",
        "numeric_block": {"char_count": 1},
        "ground_truth": {"q1": "{}", "q2": "{}", "q3": "{}"},
    }
    msg = lc.build_section_critique_user_message("TASK", bundle)
    assert "TASK" in msg
    assert "p/stub.json" in msg
    assert "stub.json" in msg
    assert "char_count" in msg


def test_parse_critique_json_response_fence() -> None:
    raw = '```json\n{"a": 1}\n```'
    assert lc.parse_critique_json_response(raw) == {"a": 1}
