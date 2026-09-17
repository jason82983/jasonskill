"""Shared naming, path resolution, and validation for HZP Amazon reports."""
from __future__ import annotations

import re
from pathlib import Path

TIMESTAMP_RE = re.compile(r"^\d{8}_\d{6}$")


def _skill_identity(skill_dir: str | Path) -> tuple[str, str]:
    folder = Path(skill_dir)
    skill_md = folder / "SKILL.md"
    if not skill_md.is_file():
        raise ValueError("HZP_OFFICIAL_SKILL_NAME_MISSING")
    text = skill_md.read_text(encoding="utf-8-sig")
    match = re.search(r"(?m)^name:\s*(hzp-amz-[a-z0-9-]+)\s*$", text)
    if not match:
        raise ValueError("HZP_OFFICIAL_SKILL_NAME_MISSING")
    skill_id = match.group(1)
    number_match = re.match(r"(\d+(?:-\d+)+)", skill_id.removeprefix("hzp-amz-"))
    if not number_match:
        raise ValueError("HZP_OFFICIAL_SKILL_NAME_MISSING")
    skill_number = number_match.group(1)

    official_name = ""
    registry = folder / "agents" / "openai.yaml"
    if registry.is_file():
        registry_text = registry.read_text(encoding="utf-8-sig")
        display = re.search(r"(?m)^\s*display_name:\s*[\"']?([^\r\n\"']+)", registry_text)
        if display:
            value = display.group(1).strip()
            official_name = re.sub(rf"^(?:HZP Amazon\s+)?{re.escape(skill_number)}\s*[｜|\s]+\s*", "", value).strip()
    if not official_name:
        for line in text.splitlines():
            if line.startswith("#"):
                heading = line.lstrip("# ").strip()
                official_name = re.sub(rf"^(?:HZP Amazon\s+)?{re.escape(skill_number)}\s*[｜|\s]+\s*", "", heading).strip()
                if official_name and official_name != heading:
                    break
                official_name = ""
    if not official_name:
        raise ValueError("HZP_OFFICIAL_SKILL_NAME_MISSING")
    return skill_number, official_name


def resolve_hzp_amz_report_root(product_root: str | Path) -> Path:
    return Path(product_root).resolve() / "06_SKILL分析报告"


def resolve_skill_report_dir(product_root: str | Path, skill_dir: str | Path) -> Path:
    number, official_name = _skill_identity(skill_dir)
    directory = resolve_hzp_amz_report_root(product_root) / f"{number}_{official_name}"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def build_report_filename(
    skill_dir: str | Path,
    report_name: str,
    timestamp: str,
    extension: str,
    *,
    product_code: str | None = None,
) -> str:
    if not TIMESTAMP_RE.fullmatch(timestamp):
        raise ValueError("HZP_REPORT_TIMESTAMP_INVALID")
    number, _ = _skill_identity(skill_dir)
    ext = extension.lstrip(".")
    if not ext or not report_name.strip():
        raise ValueError("HZP_REPORT_PREFIX_MISSING")
    parts = [number]
    if product_code:
        parts.append(product_code.strip())
    parts.extend((report_name.strip(), timestamp))
    return "_".join(parts) + "." + ext


def validate_hzp_amz_report_path(
    path: str | Path,
    product_root: str | Path,
    skill_dir: str | Path,
    *,
    timestamp: str,
    report_identity: str | None = None,
    allow_run_folder: bool = False,
) -> str | None:
    try:
        number, official_name = _skill_identity(skill_dir)
    except ValueError as exc:
        return str(exc)
    candidate = Path(path).resolve()
    base = resolve_hzp_amz_report_root(product_root) / f"{number}_{official_name}"
    if candidate.parent == resolve_hzp_amz_report_root(product_root):
        return "HZP_REPORT_WRITTEN_TO_ROOT"
    try:
        relative = candidate.relative_to(base)
    except ValueError:
        return "HZP_SKILL_REPORT_DIR_INVALID"
    if not allow_run_folder and len(relative.parts) != 1:
        return "HZP_ONE_TIME_SKILL_RUN_FOLDER_FORBIDDEN"
    if allow_run_folder and len(relative.parts) not in (1, 2):
        return "HZP_SKILL_REPORT_DIR_INVALID"
    if not candidate.name.startswith(f"{number}_"):
        return "HZP_REPORT_PREFIX_MISSING"
    timestamps = re.findall(r"(?<!\d)(\d{8}_\d{6})(?!\d)", candidate.stem)
    if len(timestamps) != 1 or timestamps[0] != timestamp or not TIMESTAMP_RE.fullmatch(timestamp):
        return "HZP_REPORT_TIMESTAMP_INVALID"
    if report_identity and report_identity not in candidate.stem:
        return "HZP_REPORT_PREFIX_MISSING"
    if len(relative.parts) == 2 and relative.parts[0] != timestamp:
        return "HZP_BATCH_TIMESTAMP_MISMATCH"
    return None


def validate_hzp_amz_report_batch(
    paths: list[str | Path],
    product_root: str | Path,
    skill_dir: str | Path,
    *,
    timestamp: str,
    allow_run_folder: bool = False,
) -> str | None:
    for path in paths:
        reason = validate_hzp_amz_report_path(
            path, product_root, skill_dir, timestamp=timestamp,
            allow_run_folder=allow_run_folder,
        )
        if reason:
            return reason
    found = {
        re.findall(r"(?<!\d)(\d{8}_\d{6})(?!\d)", Path(path).stem)[0]
        for path in paths
        if re.findall(r"(?<!\d)(\d{8}_\d{6})(?!\d)", Path(path).stem)
    }
    return None if found == {timestamp} else "HZP_BATCH_TIMESTAMP_MISMATCH"
