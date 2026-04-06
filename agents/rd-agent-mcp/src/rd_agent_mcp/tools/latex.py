"""LaTeX tools for rd-agent-mcp."""

import subprocess
import asyncio
from pathlib import Path
from typing import Optional


class LaTeXTools:
    """Tools for LaTeX document processing."""

    def __init__(self, tex_bin: str = "latexmk", working_dir: str = "."):
        self.tex_bin = tex_bin
        self.working_dir = Path(working_dir)

    def compile(
        self,
        main_file: str,
        format: str = "pdf",
        options: list[str] = None,
    ) -> bool:
        """Compile LaTeX document."""
        if options is None:
            options = ["-pdf", "-file-line-error", "-halt-on-error"]

        args = [self.tex_bin] + options + ["-f", main_file]

        try:
            result = subprocess.run(
                args,
                cwd=str(self.working_dir),
                capture_output=True,
                text=True,
                timeout=120,
            )
            return result.returncode == 0
        except Exception:
            return False

    async def compile_async(
        self,
        main_file: str,
        format: str = "pdf",
        options: list[str] = None,
    ) -> bool:
        """Compile LaTeX document asynchronously."""
        if options is None:
            options = ["-pdf", "-file-line-error", "-halt-on-error"]

        args = [self.tex_bin] + options + ["-f", main_file]

        try:
            process = await asyncio.create_subprocess_exec(
                *args,
                cwd=str(self.working_dir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await process.communicate()
            return process.returncode == 0
        except Exception:
            return False

    def extract_section(
        self,
        tex_file: str,
        section_name: str,
    ) -> Optional[str]:
        """Extract a section from LaTeX file."""
        try:
            with open(self.working_dir / tex_file) as f:
                content = f.read()

            # Simple regex to extract section
            import re

            pattern = rf"\\section\{{[^}}*{section_name}[^}}*\}}[^$]*"
            match = re.search(pattern, content, re.DOTALL)
            if match:
                return match.group()
            return None
        except Exception:
            return None

    def find_missing_packages(self, log_file: str) -> list[str]:
        """Find missing packages from LaTeX log."""
        try:
            with open(self.working_dir / log_file) as f:
                content = f.read()

            import re

            pattern = r"You can't use `([^\']+)' in ([^\n]+) mode"
            matches = re.findall(pattern, content)
            return [f"{cmd} (in {mode} mode)" for cmd, mode in matches]
        except Exception:
            return []

    def count_words(self, tex_file: str) -> int:
        """Count words in LaTeX document (excluding commands)."""
        try:
            with open(self.working_dir / tex_file) as f:
                content = f.read()

            # Remove LaTeX commands
            import re

            content = re.sub(r"\\[a-zA-Z]+\{[^}]*\}", "", content)
            content = re.sub(r"\\[a-zA-Z]+", "", content)
            content = re.sub(r"\{[^}]*\}", "", content)

            # Count words
            words = content.split()
            return len(words)
        except Exception:
            return 0

    def create_abstract(self, content: str, output_file: str = "abstract.tex") -> Path:
        """Create an abstract section."""
        abstract = f"""\\section*{{Abstract}}
\\label{{sec:abstract}}

{content}
"""
        path = self.working_dir / output_file
        with open(path, "w") as f:
            f.write(abstract)
        return path

    def create_results_table(
        self,
        data: dict,
        caption: str,
        label: str,
        output_file: str = "results_table.tex",
    ) -> Path:
        """Create a results table in LaTeX format."""
        import json

        if isinstance(data, str):
            data = json.loads(data)

        # Build table
        lines = [
            "\\begin{table}[htbp]",
            f"\\centering",
            f"\\caption{{{caption}}}",
            f"\\label{{{label}}}",
            "\\begin{tabular}{l|c}",
            "\\toprule",
        ]

        # Header
        if "headers" in data:
            headers = " & ".join(str(h) for h in data["headers"])
            lines.append(f"{headers} \\\\")
            lines.append("\\midrule")

        # Rows
        for row in data.get("rows", []):
            lines.append(" & ".join(str(v) for v in row) + " \\\\")

        lines.extend(
            [
                "\\bottomrule",
                "\\end{tabular}",
                "\\end{table}",
            ]
        )

        path = self.working_dir / output_file
        with open(path, "w") as f:
            f.write("\n".join(lines))
        return path

    def create_figure(
        self,
        image_path: str,
        caption: str,
        label: str,
        width: str = "\\linewidth",
        output_file: str = "figure.tex",
    ) -> Path:
        """Create a figure in LaTeX format."""
        figure = f"""\\begin{{figure}}[htbp]
\\centering
\\includegraphics[width={width}]{{{image_path}}}
\\caption{{{caption}}}
\\label{{{label}}}
\\end{{figure}}
"""
        path = self.working_dir / output_file
        with open(path, "w") as f:
            f.write(figure)
        return path
