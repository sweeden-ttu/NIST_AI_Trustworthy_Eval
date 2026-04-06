"""GitHub CLI tools for rd-agent-mcp."""

import subprocess
import asyncio
from typing import Optional
from pathlib import Path


class GitHubTools:
    """Tools for GitHub operations using gh CLI."""

    @staticmethod
    def is_authenticated() -> bool:
        """Check if GitHub CLI is authenticated."""
        try:
            result = subprocess.run(
                ["gh", "auth", "status"],
                capture_output=True,
                timeout=10,
            )
            return result.returncode == 0
        except Exception:
            return False

    @staticmethod
    def clone_repo(repo: str, path: str = ".", depth: int = None) -> bool:
        """Clone a GitHub repository."""
        args = ["gh", "repo", "clone", repo]
        if depth:
            args.extend(["--", "--depth", str(depth)])
        args.append(path)

        try:
            result = subprocess.run(args, capture_output=True, timeout=60)
            return result.returncode == 0
        except Exception:
            return False

    @staticmethod
    async def clone_repo_async(repo: str, path: str = ".", depth: int = None) -> bool:
        """Clone a GitHub repository asynchronously."""
        args = ["gh", "repo", "clone", repo]
        if depth:
            args.extend(["--", "--depth", str(depth)])
        args.append(path)

        try:
            process = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await process.communicate()
            return process.returncode == 0
        except Exception:
            return False

    @staticmethod
    def create_pr(
        repo: str,
        title: str,
        body: str,
        base: str = "main",
        head: str = None,
    ) -> Optional[str]:
        """Create a pull request."""
        args = [
            "gh",
            "pr",
            "create",
            "--repo",
            repo,
            "--title",
            title,
            "--body",
            body,
            "--base",
            base,
        ]
        if head:
            args.extend(["--head", head])

        try:
            result = subprocess.run(args, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except Exception:
            return None

    @staticmethod
    def get_workflow_runs(repo: str, workflow: str = None) -> list[dict]:
        """Get workflow runs."""
        args = ["gh", "run", "list", "--repo", repo, "--json", "id,name,status,conclusion"]
        if workflow:
            args.extend(["--workflow", workflow])

        try:
            result = subprocess.run(args, capture_output=True, text=True, timeout=30)
            import json

            return json.loads(result.stdout) if result.stdout else []
        except Exception:
            return []

    @staticmethod
    def download_artifact(run_id: str, name: str, repo: str, path: str = ".") -> bool:
        """Download a workflow artifact."""
        try:
            result = subprocess.run(
                ["gh", "run", "download", run_id, "--name", name, "--repo", repo, "-D", path],
                capture_output=True,
                timeout=60,
            )
            return result.returncode == 0
        except Exception:
            return False

    @staticmethod
    def create_release(
        repo: str,
        tag: str,
        name: str,
        notes: str = None,
        files: list[str] = None,
    ) -> bool:
        """Create a GitHub release."""
        args = [
            "gh",
            "release",
            "create",
            tag,
            "--repo",
            repo,
            "--title",
            name,
        ]
        if notes:
            args.extend(["--notes", notes])
        if files:
            args.extend(files)

        try:
            result = subprocess.run(args, capture_output=True, timeout=30)
            return result.returncode == 0
        except Exception:
            return False

    @staticmethod
    def get_file_content(repo: str, path: str, ref: str = "main") -> Optional[str]:
        """Get file content from repository."""
        try:
            result = subprocess.run(
                ["gh", "api", f"/repos/{repo}/contents/{path}?ref={ref}"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                import base64

                data = __import__("json").loads(result.stdout)
                return base64.b64decode(data["content"]).decode("utf-8")
            return None
        except Exception:
            return None
