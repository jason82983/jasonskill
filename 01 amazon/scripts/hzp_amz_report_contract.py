"""Shared naming, path resolution, and validation for HZP Amazon reports."""
from __future__ import annotations

import re
import hashlib
import os
import json
from pathlib import Path
from datetime import datetime

TIMESTAMP_RE = re.compile(r"^\d{8}_\d{6}$")
DISPLAY_TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}_\d{6}$")


def report_data_dir(product_root: str | Path, skill_dir: str | Path) -> Path:
    """Return the machine-consumable data layer for one Skill report identity."""
    path = skill_report_directory_path(product_root, skill_dir) / "data"
    path.mkdir(parents=True, exist_ok=True)
    return path


def report_history_html_dir(product_root: str | Path, skill_dir: str | Path) -> Path:
    path = skill_report_directory_path(product_root, skill_dir) / "历史HTML"
    path.mkdir(parents=True, exist_ok=True)
    return path


def report_system_dir(product_root: str | Path, skill_dir: str | Path, category: str) -> Path:
    """Return one of metadata/manifests/registry/logs under the private system layer."""
    if category not in {"metadata", "manifests", "registry", "logs"}:
        raise ValueError("HZP_SYSTEM_ASSET_CATEGORY_INVALID")
    path = skill_report_directory_path(product_root, skill_dir) / "_system" / category
    path.mkdir(parents=True, exist_ok=True)
    return path


def display_timestamp(run_timestamp: str) -> str:
    if not TIMESTAMP_RE.fullmatch(str(run_timestamp)):
        raise ValueError("HZP_HTML_TIMESTAMP_INVALID")
    try:
        value = datetime.strptime(str(run_timestamp), "%Y%m%d_%H%M%S")
    except ValueError as exc:
        raise ValueError("HZP_HTML_TIMESTAMP_INVALID") from exc
    return value.strftime("%Y-%m-%d_%H%M%S")


def build_latest_html_filename(skill_dir: str | Path, report_identity: str, run_timestamp: str) -> str:
    number, _ = _skill_identity(skill_dir)
    if not report_identity.strip():
        raise ValueError("HZP_REPORT_PREFIX_MISSING")
    return f"{number}_{report_identity.strip()}_最新_{display_timestamp(run_timestamp)}.html"


def latest_html_path(product_root: str | Path, skill_dir: str | Path, report_identity: str, run_timestamp: str) -> Path:
    return skill_report_directory_path(product_root, skill_dir) / build_latest_html_filename(skill_dir, report_identity, run_timestamp)


def system_metadata_path(product_root: str | Path, skill_dir: str | Path, filename: str) -> Path:
    return report_system_dir(product_root, skill_dir, "metadata") / filename


def system_manifest_path(product_root: str | Path, skill_dir: str | Path, filename: str) -> Path:
    return report_system_dir(product_root, skill_dir, "manifests") / filename


def write_system_json(path: str | Path, payload: Mapping[str, Any]) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        raise FileExistsError("HZP_SYSTEM_ASSET_EXISTS")
    target.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def publish_latest_html(
    temporary_html: str | Path,
    product_root: str | Path,
    skill_dir: str | Path,
    report_identity: str,
    run_timestamp: str,
) -> Path:
    """Atomically publish one valid HTML and archive the previous latest.

    The caller must finish data validation and HTML/data reconciliation before
    calling this function.  Existing history collisions fail closed.
    """
    temp = Path(temporary_html).resolve()
    root = skill_report_directory_path(product_root, skill_dir)
    root.mkdir(parents=True, exist_ok=True)
    history = report_history_html_dir(product_root, skill_dir)
    number, _ = _skill_identity(skill_dir)
    pattern = f"{number}_{report_identity.strip()}_最新_*.html"
    current = sorted(root.glob(pattern))
    if len(current) > 1:
        raise ValueError("HZP_HTML_LATEST_DUPLICATE")
    target = root / build_latest_html_filename(skill_dir, report_identity, run_timestamp)
    if target.exists():
        raise ValueError("HZP_HTML_HISTORY_COLLISION")
    archived = None
    if current:
        old = current[0]
        archived = history / old.name.replace("_最新_", "_")
        if archived.exists():
            if _sha256(archived) != _sha256(old):
                raise ValueError("HZP_HTML_HISTORY_COLLISION")
            raise ValueError("HZP_HTML_HISTORY_COLLISION")
    if not temp.is_file():
        raise ValueError("HZP_HTML_TEMP_MISSING")
    try:
        if archived is not None:
            os.replace(old, archived)
        os.replace(temp, target)
    except Exception:
        if archived is not None and archived.exists() and not old.exists():
            os.replace(archived, old)
        raise
    return target


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


def skill_report_directory_path(product_root: str | Path, skill_dir: str | Path) -> Path:
    number, official_name = _skill_identity(skill_dir)
    return resolve_hzp_amz_report_root(product_root) / f"{number}_{official_name}"


def resolve_skill_report_dir(product_root: str | Path, skill_dir: str | Path) -> Path:
    directory = skill_report_directory_path(product_root, skill_dir)
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


def validate_layered_asset_path(
    path: str | Path,
    product_root: str | Path,
    skill_dir: str | Path,
    *,
    timestamp: str,
    layer: str,
) -> str | None:
    """Validate a new data/system asset without weakening the legacy contract."""
    try:
        number, official_name = _skill_identity(skill_dir)
    except ValueError as exc:
        return str(exc)
    candidate = Path(path).resolve()
    base = resolve_hzp_amz_report_root(product_root) / f"{number}_{official_name}"
    try:
        relative = candidate.relative_to(base)
    except ValueError:
        return "HZP_SKILL_REPORT_DIR_INVALID"
    allowed = {"data", "_system/metadata", "_system/manifests", "_system/registry", "_system/logs"}
    if layer not in allowed or not relative.parts or "/".join(relative.parts[:-1]) != layer:
        return "HZP_SYSTEM_ASSET_IN_HUMAN_ROOT" if layer.startswith("_system") else "HZP_SKILL_REPORT_DIR_INVALID"
    if not candidate.name.startswith(f"{number}_") and not (layer.startswith("_system") and candidate.name.startswith(("run_manifest_", "stable_", "batch_"))):
        return "HZP_REPORT_PREFIX_MISSING"
    matches = re.findall(r"(?<!\d)(\d{8}_\d{6})(?!\d)", candidate.name)
    if matches and matches[-1] != timestamp:
        return "HZP_DATA_TIMESTAMP_INVALID"
    if not matches and layer == "data":
        return "HZP_DATA_TIMESTAMP_INVALID"
    return None
