# Archived ICLR-style R&D-Agent paper

This tree was the previous default LaTeX entry (`main.tex`, `math_commands.tex`, ICLR style).

Build from this directory (requires TeX Live with ICLR style on `TEXINPUTS` or local `.sty`):

```bash
cd src/archive/rd-agent-paper
latexmk -lualatex -interaction=nonstopmode main.tex
```

The repository default build targets the IEEE journal article: [`../ieee_journal.tex`](../ieee_journal.tex).
