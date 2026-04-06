#!/usr/bin/env python3
"""
Print env var names that are plausible GitHub Actions repository secrets.

Excludes common OS/shell/IDE noise. Run locally; do not paste values into CI logs.

Usage:
  python scripts/list_github_secret_candidates_from_env.py
"""

from __future__ import annotations

import os
import re

# Keys that are never repository secrets for this courseware
DENY = frozenset(
    {
        "PATH",
        "HOME",
        "PWD",
        "OLDPWD",
        "SHELL",
        "SHLVL",
        "USER",
        "LOGNAME",
        "TMPDIR",
        "LANG",
        "TERM",
        "SSH_AUTH_SOCK",
        "XPC_FLAGS",
        "XPC_SERVICE_NAME",
        "MallocNanoZone",
        "OSLogRateLimit",
        "COMMAND_MODE",
        "CURSOR_AGENT",
        "CURSOR_EXTENSION_HOST_ROLE",
        "CURSOR_LAYOUT",
        "CURSOR_WORKSPACE_LABEL",
        "VSCODE_CODE_CACHE_PATH",
        "VSCODE_CRASH_REPORTER_PROCESS_TYPE",
        "VSCODE_CWD",
        "VSCODE_ESM_ENTRYPOINT",
        "VSCODE_HANDLES_UNCAUGHT_ERRORS",
        "VSCODE_IPC_HOOK",
        "VSCODE_NLS_CONFIG",
        "VSCODE_PID",
        "VSCODE_PROCESS_TITLE",
        "FORCE_COLOR",
        "NO_COLOR",
        "GITHUB_TOKEN",  # provided by Actions; do not define as repo secret
    }
)

PREFIX_DENY = (
    "CONDA",
    "CURSOR",
    "VSCODE",
    "_CE_",
    "_CONDA",
    "_ZO_",
    "__CF",
    "MACH_PORT",
)


def main() -> None:
    pat = re.compile(r"^[A-Z][A-Z0-9_]*$")
    names: list[str] = []
    for k in os.environ:
        if k in DENY or k == "_":
            continue
        if k.startswith("_") and not k.startswith("_GITHUB"):  # allow rare _GITHUB* if ever set
            continue
        if any(k.startswith(p) for p in PREFIX_DENY):
            continue
        if not pat.match(k):
            continue
        names.append(k)
    for name in sorted(set(names)):
        print(name)


if __name__ == "__main__":
    main()
