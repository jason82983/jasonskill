"""Minimal Codex CLI Production Judge adapter for 6-0-2.

This module owns only process invocation and structured-result parsing.  It
does not classify keywords, apply local rules, or write checkpoints.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Mapping


class CodexCliError(RuntimeError):
    def __init__(self, code: str, message: str = ""):
        super().__init__(f"{code}{(': ' + message) if message else ''}")
        self.code = code


def codex_executable() -> str:
    value = shutil.which("codex")
    if not value:
        raise CodexCliError("CODEX_CLI_NOT_FOUND")
    return value


def codex_version(*, timeout: float = 15.0) -> str:
    try:
        result = subprocess.run([codex_executable(), "--version"], capture_output=True,
                                text=True, encoding="utf-8", errors="replace",
                                timeout=timeout, check=False)
    except subprocess.TimeoutExpired as exc:
        raise CodexCliError("CODEX_CLI_TIMEOUT", "version") from exc
    if result.returncode != 0:
        raise CodexCliError("CODEX_CLI_EXEC_FAILED", result.stderr.strip())
    return (result.stdout or result.stderr).strip()


def codex_login_status(*, timeout: float = 20.0) -> str:
    try:
        result = subprocess.run([codex_executable(), "login", "status"], capture_output=True,
                                text=True, encoding="utf-8", errors="replace",
                                timeout=timeout, check=False)
    except subprocess.TimeoutExpired as exc:
        raise CodexCliError("CODEX_CLI_TIMEOUT", "login status") from exc
    output = "\n".join(x for x in (result.stdout, result.stderr) if x).strip()
    if result.returncode != 0:
        raise CodexCliError("CODEX_CLI_AUTH_REQUIRED", output)
    return output


def _is_auth_error(text: str) -> bool:
    lowered = text.casefold()
    return any(token in lowered for token in (
        "authentication required", "not authenticated", "unauthorized",
        "please login", "please log in", "credential missing",
        "no credentials", "api key required",
    ))


def _parse_structured_result(path: Path, stdout: str) -> dict[str, Any]:
    raw = ""
    if path.is_file():
        raw = path.read_text(encoding="utf-8-sig").strip()
    if not raw:
        # --json is an event JSONL stream; use the last JSON object only as a
        # defensive fallback when the output-last-message file is unavailable.
        for line in reversed((stdout or "").splitlines()):
            line = line.strip()
            if line.startswith("{"):
                raw = line
                break
    if not raw:
        raise CodexCliError("CODEX_CLI_RESULT_MISSING")
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise CodexCliError("CODEX_CLI_RESULT_JSON_INVALID", str(exc)) from exc
    if not isinstance(value, Mapping):
        raise CodexCliError("CODEX_CLI_RESULT_SCHEMA_INVALID")
    return dict(value)


def run_codex_cli_judge(
    payload: Mapping[str, Any],
    *,
    schema_path: str | Path,
    result_path: str | Path | None = None,
    timeout: float = 900.0,
    cwd: str | Path | None = None,
) -> dict[str, Any]:
    """Run one non-interactive structured Codex CLI judgment."""
    executable = codex_executable()
    schema = str(Path(schema_path).resolve())
    owned_result = result_path is None
    if result_path is None:
        handle = tempfile.NamedTemporaryFile(prefix="602_codex_", suffix=".json", delete=False)
        handle.close()
        result_path = handle.name
    result_file = Path(result_path).resolve()
    # ``exec`` accepts sandbox selection but does not expose the interactive
    # ``-a/--ask-for-approval`` flag.  Supplying ``-a`` makes every production
    # call exit with code 2 before the model starts.  Read-only sandboxing is
    # sufficient for the judge, and keeps the invocation non-interactive.
    args = [executable, "exec", "-", "--json", "--output-schema", schema,
            "--output-last-message", str(result_file), "--ephemeral",
            "--skip-git-repo-check", "-s", "read-only"]
    text = json.dumps(dict(payload), ensure_ascii=False, separators=(",", ":"))
    env = os.environ.copy()
    try:
        completed = subprocess.run(args, input=text, capture_output=True,
                                   text=True, encoding="utf-8", errors="replace",
                                   timeout=timeout, cwd=str(cwd) if cwd else None,
                                   env=env, check=False)
    except subprocess.TimeoutExpired as exc:
        raise CodexCliError("CODEX_CLI_TIMEOUT") from exc
    combined = "\n".join(x for x in (completed.stdout, completed.stderr) if x)
    if completed.returncode != 0:
        code = "CODEX_CLI_AUTH_REQUIRED" if _is_auth_error(combined) else "CODEX_CLI_EXIT_NONZERO"
        detail = combined.strip().replace("\n", " ")[-1200:]
        raise CodexCliError(code, f"exit={completed.returncode}; {detail}")
    try:
        return _parse_structured_result(result_file, completed.stdout)
    finally:
        if owned_result:
            try:
                result_file.unlink()
            except OSError:
                pass
