# Examples

This directory contains example code for demonstrating agent capabilities.

## Python Examples

### generate_results.py
Generates JSON results from data analysis.

```bash
python examples/python/generate_results.py --question q1
```

Output: `output/results.json`

### plot_diagram.py
Generates matplotlib diagrams from results.

```bash
python examples/python/plot_diagram.py --input output/results.json
```

Output: `output/diagrams/performance.pdf`

## Rust Examples

### analyze_stats.rs
Statistics analysis CLI tool.

```bash
cd examples/rust
cargo build --release
./target/release/analyze_stats --input ../../output/results.json
```

Output: `output/rust_output.json`

## LaTeX Examples

### results_table.tex
LaTeX table generation template.

```latex
\section{Results}
\input{tables/results.tex}
```

## Combined Workflow

```bash
# 1. Python analysis
python examples/python/generate_results.py --question q1

# 2. Rust analysis
cd examples/rust && cargo run -- analyze --input ../../output/results.json

# 3. Generate LaTeX table
pdflatex -interaction=nonstopmode tables/results.tex
```

## Integration with GitHub Actions

See `.github/workflows/agent-demo.yaml` for automated examples.
