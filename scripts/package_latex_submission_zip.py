#!/usr/bin/env python3
"""
Refresh NIST LaTeX-related outputs (manifest + rubric table), rebuild main.pdf, and
write a zip archive suitable for upload: src/*.tex, styles, bibliography, output/results,
output/diagrams, and a short build README.

Usage (repo root):
  python scripts/package_latex_submission_zip.py
  python scripts/package_latex_submission_zip.py --out output/submission/my_bundle.zip
  python scripts/package_latex_submission_zip.py --skip-pdf-build
  python scripts/package_latex_submission_zip.py --skip-refresh-outputs
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"
RESULTS = REPO_ROOT / "output" / "results"
DIAGRAMS = REPO_ROOT / "output" / "diagrams"
SUBMISSION_DIR = REPO_ROOT / "output" / "submission"

SRC_SKIP_SUFFIXES = frozenset(
    {
        ".aux",
        ".log",
        ".out",
        ".toc",
        ".bbl",
        ".blg",
        ".fls",
        ".fdb_latexmk",
        ".synctex.gz",
        ".pdf",
    }
)


BUILD_README = """# LaTeX submission bundle (NIST Quiz #3)

## Build the course report PDF (`main.tex`)

Requirements: TeX distribution with **latexmk**, **newtx** (`newtxtext`, `newtxmath`), **natbib**, **hyperref**, **fancyhdr**, **booktabs**.

```bash
cd src
latexmk -pdf -interaction=nonstopmode main.tex
```

The first run may call **bibtex**; `latexmk` runs the full cycle. Output: `src/main.pdf`.

If `src/main.pdf` is bundled, it was rebuilt when the archive was created; you can submit it directly or rebuild from sources.

Paths in this bundle mirror the repository: `experiment.tex` inputs `../output/results/nist_rubric_table.tex`.
Optional figures belong in `output/diagrams/` (see `output/diagrams/README.txt`).

## Optional: IEEE legacy layout

```bash
cd src
latexmk -pdf -interaction=nonstopmode ieee_journal.tex
```

Requires the **IEEEtran** class (e.g. `texlive-publishers`).

## Regenerate the rubric table fragment

If you edit `output/results/nist_quiz_scores.json`:

```bash
python scripts/emit_nist_rubric_table.py
```

(Requires the full repo with `scripts/`; this zip focuses on compiling the PDF from frozen outputs.)
"""


DIAGRAMS_README = """This directory is on the LaTeX graphics path for `src/main.tex` (`\\\\graphicspath`).

The default NIST Quiz #3 track in `main.tex` does not require figures here. Add PDF, PNG, or EPS
assets if your write-up references them via `\\\\includegraphics`.
"""


def run(cmd: list[str], *, cwd: Path) -> None:
    print("+", " ".join(cmd), flush=True)
    r = subprocess.run(cmd, cwd=str(cwd))
    if r.returncode != 0:
        raise SystemExit(r.returncode)


def iter_src_files() -> list[Path]:
    files: list[Path] = []
    for p in SRC.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(SRC)
        if rel.parts and rel.parts[0] == "archive":
            continue
        if p.suffix.lower() in SRC_SKIP_SUFFIXES:
            continue
        suf = p.suffix.lower()
        name = p.name
        if suf in {".tex", ".bib", ".sty", ".bst", ".cls", ".md", ".json"} or name == "00README.json":
            files.append(p)
    return sorted(files)


def add_tree(z: zipfile.ZipFile, base: Path, arc_prefix: str, paths: list[Path]) -> None:
    for p in paths:
        arc = f"{arc_prefix}/{p.relative_to(base).as_posix()}"
        z.write(p, arcname=arc)


def collect_results_files() -> list[Path]:
    if not RESULTS.is_dir():
        return []
    out: list[Path] = []
    for p in sorted(RESULTS.rglob("*")):
        if not p.is_file():
            continue
        if p.suffix.lower() in {".json", ".tex", ".txt", ".md"}:
            out.append(p)
    return out


def collect_diagram_files() -> list[Path]:
    if not DIAGRAMS.is_dir():
        return []
    return [p for p in sorted(DIAGRAMS.iterdir()) if p.is_file()]


def main() -> int:
    ap = argparse.ArgumentParser(description="Zip LaTeX sources + output/results + diagrams for upload.")
    ap.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Zip path (default: output/submission/NIST_latex_bundle_<UTC>.zip)",
    )
    ap.add_argument(
        "--skip-refresh-outputs",
        action="store_true",
        help="Do not run run_coursework_outputs.py --skip-nist-eval",
    )
    ap.add_argument(
        "--skip-pdf-build",
        action="store_true",
        help="Do not run latexmk on src/main.tex",
    )
    args = ap.parse_args()

    if not args.skip_refresh_outputs:
        run(
            [sys.executable, str(REPO_ROOT / "scripts" / "run_coursework_outputs.py"), "--skip-nist-eval"],
            cwd=REPO_ROOT,
        )

    DIAGRAMS.mkdir(parents=True, exist_ok=True)
    readme_d = DIAGRAMS / "README.txt"
    if not readme_d.is_file():
        readme_d.write_text(DIAGRAMS_README, encoding="utf-8")

    if not args.skip_pdf_build:
        run(
            [
                "latexmk",
                "-g",
                "-pdf",
                "-interaction=nonstopmode",
                "main.tex",
            ],
            cwd=SRC,
        )

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_zip = args.out or (SUBMISSION_DIR / f"NIST_latex_bundle_{ts}.zip")
    out_zip.parent.mkdir(parents=True, exist_ok=True)

    src_files = iter_src_files()
    result_files = collect_results_files()
    diagram_files = collect_diagram_files()
    if readme_d not in diagram_files and readme_d.is_file():
        diagram_files.append(readme_d)
        diagram_files.sort()

    pdf_path = SRC / "main.pdf"

    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("BUILD_PDF_README.md", BUILD_README)
        add_tree(z, SRC, "src", src_files)
        add_tree(z, RESULTS, "output/results", result_files)
        add_tree(z, DIAGRAMS, "output/diagrams", diagram_files)
        if pdf_path.is_file():
            z.write(pdf_path, arcname="src/main.pdf")

    print(f"Wrote {out_zip.relative_to(REPO_ROOT)} ({out_zip.stat().st_size // 1024} KiB)")
    print(f"  src files: {len(src_files)}")
    print(f"  output/results files: {len(result_files)}")
    print(f"  output/diagrams files: {len(diagram_files)}")
    if pdf_path.is_file():
        print(f"  included prebuilt: src/main.pdf ({pdf_path.stat().st_size // 1024} KiB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
