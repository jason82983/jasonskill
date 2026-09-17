"""Shared naming, path resolution, and validation for HZP Amazon reports."""
from __future__ import annotations

import re
import shutil
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

TIMESTAMP_RE = re.compile(r"^\d{8}_\d{6}$")
HUMAN_HISTORY_DIR_NAME = "历史HTML"
MACHINE_HISTORY_DIR_NAME = "历史数据"
SYSTEM_DIR_NAME = "_system"
STAGING_DIR_NAME = "staging"
GOVERNANCE_DIRS = {
    "data": "data",
    "history_html": HUMAN_HISTORY_DIR_NAME,
    "history_data": MACHINE_HISTORY_DIR_NAME,
    "metadata": f"{SYSTEM_DIR_NAME}/metadata",
    "manifests": f"{SYSTEM_DIR_NAME}/manifests",
    "registry": f"{SYSTEM_DIR_NAME}/registry",
    "logs": f"{SYSTEM_DIR_NAME}/logs",
    "staging": f"{SYSTEM_DIR_NAME}/{STAGING_DIR_NAME}",
}


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


def governance_paths(report_dir: str | Path, *, create: bool = True) -> dict[str, Path]:
    """Return the one shared filesystem layout for a Skill report directory.

    The returned ``data`` directory is the only current machine-data location.
    Historical batches and governance assets are deliberately separated so a
    downstream resolver cannot accidentally select a human HTML or an old CSV.
    """
    root = Path(report_dir)
    result = {key: root / value for key, value in GOVERNANCE_DIRS.items()}
    if create:
        for key in ("data", "history_html", "history_data", "metadata", "manifests", "registry", "logs"):
            result[key].mkdir(parents=True, exist_ok=True)
    return result


def staging_batch_dir(report_dir: str | Path, timestamp: str, *, create: bool = True) -> Path:
    if not TIMESTAMP_RE.fullmatch(str(timestamp)):
        raise ValueError("HZP_REPORT_TIMESTAMP_INVALID")
    path = governance_paths(report_dir, create=create)["staging"] / str(timestamp)
    if create:
        path.mkdir(parents=True, exist_ok=False)
    return path


def _timestamp_from_name(path: Path) -> str | None:
    matches = re.findall(r"(?<!\d)(\d{8}_\d{6})(?!\d)", path.name)
    return matches[0] if len(matches) == 1 else None


def _batch_timestamp(paths: Iterable[Path]) -> str | None:
    stamps = {_timestamp_from_name(path) for path in paths}
    stamps.discard(None)
    return next(iter(stamps)) if len(stamps) == 1 else None


def _copy_or_move(source: Path, target: Path, *, move: bool) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        raise FileExistsError(target)
    if move:
        shutil.move(str(source), str(target))
    else:
        shutil.copy2(source, target)


def _write_json_atomic(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            json.dump(dict(payload), handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def publish_latest_valid_batch(
    report_dir: str | Path,
    timestamp: str,
    business_files: Sequence[str | Path],
    *,
    manifest_files: Sequence[str | Path] = (),
    metadata_files: Sequence[str | Path] = (),
    registry_files: Sequence[str | Path] = (),
    registry_payload: Mapping[str, Any] | None = None,
    validator: Callable[[Path, Sequence[Path]], str | None] | None = None,
    move_sources: bool = False,
) -> dict[str, Any]:
    """Atomically publish one complete VALID batch and archive the old batch.

    ``business_files`` are staged first.  A validator may inspect the staged
    copies and return an error code.  Only after validation does the current
    ``data`` directory move to ``历史数据/{timestamp}`` and the new directory
    become visible.  Any failure restores the previous data directory.
    """
    stamp = str(timestamp)
    if not TIMESTAMP_RE.fullmatch(stamp):
        raise ValueError("HZP_REPORT_TIMESTAMP_INVALID")
    root = Path(report_dir)
    dirs = governance_paths(root, create=True)
    sources = [Path(item) for item in business_files]
    if not sources or any(not item.is_file() for item in sources):
        raise FileNotFoundError("HZP_BATCH_SOURCE_MISSING")
    if _batch_timestamp(sources) != stamp:
        raise ValueError("HZP_BATCH_TIMESTAMP_MISMATCH")
    manifest_sources = [Path(item) for item in manifest_files]
    metadata_sources = [Path(item) for item in metadata_files]
    registry_sources = [Path(item) for item in registry_files]
    if any(not item.is_file() for item in [*manifest_sources, *metadata_sources, *registry_sources]):
        raise FileNotFoundError("HZP_SYSTEM_ASSET_MISSING")

    stage = staging_batch_dir(root, stamp)
    staged_data = stage / "data"
    staged_manifests = stage / "manifests"
    staged_metadata = stage / "metadata"
    staged_registry = stage / "registry"
    staged_business: list[Path] = []
    try:
        for source in sources:
            target = staged_data / source.name
            _copy_or_move(source, target, move=move_sources)
            staged_business.append(target)
            sidecar = Path(str(source) + ".meta.json")
            if sidecar.is_file():
                _copy_or_move(sidecar, staged_metadata / sidecar.name, move=move_sources)
        for source in manifest_sources:
            target = staged_manifests / source.name
            _copy_or_move(source, target, move=move_sources)
        for source in metadata_sources:
            _copy_or_move(source, staged_metadata / source.name, move=move_sources)
        for source in registry_sources:
            _copy_or_move(source, staged_registry / source.name, move=move_sources)
        if validator:
            error = validator(staged_data, staged_business)
            if error:
                raise ValueError(str(error))

        old_data = dirs["data"]
        rollback = stage / "rollback_data"
        system_backup = stage / "_system_backup"
        for key in ("manifests", "metadata", "registry"):
            source_dir = dirs[key]
            if source_dir.is_dir():
                shutil.copytree(source_dir, system_backup / key)
        old_stamp: str | None = None
        old_files = [item for item in old_data.iterdir()] if old_data.is_dir() else []
        old_business = [item for item in old_files if item.is_file() and not item.name.endswith(".meta.json")]
        if old_business:
            batch_stamp = _batch_timestamp(old_business)
            if batch_stamp:
                old_stamp = batch_stamp
            else:
                # A previous Windows in-place publish can leave old and new
                # timestamped assets together. Archive the mixed directory as
                # one legacy batch instead of blocking the next valid run.
                old_stamp = f"legacy_{stamp}"
        in_place_data_publish = False
        if old_data.exists():
            try:
                old_data.rename(rollback)
            except PermissionError:
                # Windows may keep a report data directory open while a
                # browser previews an asset. Preserve the old batch by copy,
                # then publish the new batch in place instead of failing the
                # entire run on a directory rename.
                in_place_data_publish = True
                if old_stamp:
                    archive = dirs["history_data"] / old_stamp
                    if archive.exists():
                        raise FileExistsError(archive)
                    shutil.copytree(old_data, archive)
        try:
            if in_place_data_publish:
                shutil.copytree(staged_data, dirs["data"], dirs_exist_ok=True)
                staged_names = {item.name for item in staged_data.iterdir()}
                for child in list(dirs["data"].iterdir()):
                    if child.name in staged_names:
                        continue
                    try:
                        if child.is_dir():
                            shutil.rmtree(child)
                        else:
                            child.unlink()
                    except PermissionError:
                        # A preview lock must not invalidate the new batch;
                        # the locked legacy asset remains auditable until the
                        # next cleanup pass.
                        continue
            else:
                staged_data.rename(dirs["data"])
            if old_stamp and rollback.exists():
                archive = dirs["history_data"] / old_stamp
                if archive.exists():
                    raise FileExistsError(archive)
                rollback.rename(archive)
            elif rollback.exists():
                shutil.rmtree(rollback)

            for child in staged_manifests.iterdir() if staged_manifests.exists() else ():
                _copy_or_move(child, dirs["manifests"] / child.name, move=True)
            for child in staged_metadata.iterdir() if staged_metadata.exists() else ():
                _copy_or_move(child, dirs["metadata"] / child.name, move=True)
            for child in staged_registry.iterdir() if staged_registry.exists() else ():
                _copy_or_move(child, dirs["registry"] / child.name, move=True)
            if registry_payload is not None:
                registry_payload = dict(registry_payload)
                registry_payload.setdefault("RUN_TIMESTAMP", stamp)
                registry_payload.setdefault("Status", "LATEST_VALID")
                _write_json_atomic(dirs["registry"] / "latest.json", registry_payload)
        except Exception:
            new_data = dirs["data"]
            if new_data.exists():
                shutil.rmtree(new_data)
            archive = dirs["history_data"] / old_stamp if old_stamp else None
            if archive and archive.exists() and not rollback.exists():
                archive.rename(rollback)
            if rollback.exists():
                rollback.rename(dirs["data"])
            for key in ("manifests", "metadata", "registry"):
                current_dir = dirs[key]
                backup_dir = system_backup / key
                if current_dir.exists():
                    shutil.rmtree(current_dir)
                if backup_dir.is_dir():
                    shutil.copytree(backup_dir, current_dir)
            raise
    except Exception:
        # Keep the failed staging package for audit; it is never a current batch.
        raise
    else:
        shutil.rmtree(stage, ignore_errors=True)
    return {
        "status": "LATEST_VALID",
        "run_timestamp": stamp,
        "data_dir": str(dirs["data"]),
        "business_files": [str(dirs["data"] / path.name) for path in sources],
        "manifest_files": [str(dirs["manifests"] / path.name) for path in manifest_sources],
        "metadata_dir": str(dirs["metadata"]),
    }


def resolve_latest_valid_data(report_dir: str | Path) -> dict[str, Any]:
    """Resolve the formal current batch from registry and the ``data`` folder."""
    root = Path(report_dir)
    dirs = governance_paths(root, create=False)
    registry = dirs["registry"] / "latest.json"
    payload: dict[str, Any] = {}
    if registry.is_file():
        try:
            value = json.loads(registry.read_text(encoding="utf-8-sig"))
            if isinstance(value, dict):
                payload = value
        except (OSError, UnicodeError, json.JSONDecodeError):
            payload = {}
    files = sorted(item for item in dirs["data"].glob("*") if item.is_file() and not item.name.endswith(".meta.json")) if dirs["data"].is_dir() else []
    stamp = _batch_timestamp(files)
    registry_status = str(payload.get("Status") or payload.get("Run_Status") or "").upper()
    invalid_registry = registry_status not in {"", "LATEST_VALID", "VALID", "FULL_SUCCESS", "SUCCESS", "COMPLETE"}
    if not files or not stamp or invalid_registry or (payload.get("RUN_TIMESTAMP") and payload.get("RUN_TIMESTAMP") != stamp):
        return {"status": "NO_LATEST_VALID_DATA", "files": [], "run_timestamp": stamp}
    return {"status": "LATEST_VALID_DATA", "run_timestamp": stamp, "data_dir": str(dirs["data"]), "files": [str(item) for item in files], "registry": payload}


def audit_legacy_root_assets(report_dir: str | Path) -> dict[str, Any]:
    """Audit root-level machine assets before any one-time migration.

    The audit is intentionally read-only.  A caller may migrate only a batch
    whose manifest, identities and references have been validated; ambiguous
    assets are reported as ``UNRESOLVED`` and left in place.
    """
    root = Path(report_dir)
    machine = [item for item in root.iterdir() if item.is_file() and item.suffix.lower() in {".csv", ".json"} and item.name.lower() != "index.html"] if root.is_dir() else []
    grouped: dict[str, list[str]] = {}
    unresolved: list[str] = []
    for item in machine:
        stamp = _timestamp_from_name(item)
        if stamp:
            grouped.setdefault(stamp, []).append(item.name)
        else:
            unresolved.append(item.name)
    return {
        "status": "LEGACY_ROOT_ASSETS_FOUND" if machine else "CLEAN",
        "report_dir": str(root),
        "root_machine_assets": sorted(item.name for item in machine),
        "batches": {stamp: sorted(names) for stamp, names in sorted(grouped.items())},
        "unresolved": sorted(unresolved),
        "safe_to_migrate": bool(machine) and not unresolved and len(grouped) == 1,
    }


def publish_latest_html(
    source_path: str | Path,
    report_dir: str | Path | None = None,
    *,
    copy_from_package: bool = True,
) -> dict[str, object]:
    """Keep one human-facing HTML at a skill root and archive older root HTML.

    Run-package HTML remains in its immutable package folder.  When the source
    is in a package folder, a copy is published at the skill report root for
    human viewing; older root HTML files (and their metadata sidecars) move to
    ``历史HTML``.  No files are deleted or overwritten.
    """
    source = Path(source_path)
    if not source.is_file():
        raise FileNotFoundError(source)
    root = Path(report_dir) if report_dir is not None else source.parent
    root.mkdir(parents=True, exist_ok=True)
    history = root / HUMAN_HISTORY_DIR_NAME
    history.mkdir(parents=True, exist_ok=True)
    target = root / source.name
    if source.parent.resolve() == root.resolve():
        target = source
        copy_from_package = False

    old_files = [
        old for old in sorted(root.glob("*.html"), key=lambda item: item.name.casefold())
        if old.resolve() != target.resolve() and old.name.casefold() != "index.html"
    ]
    planned: list[tuple[Path, Path, Path | None, Path | None]] = []
    for old in old_files:
        destination = history / old.name
        sidecar = Path(str(old) + ".meta.json")
        sidecar_destination = history / sidecar.name if sidecar.exists() else None
        if destination.exists():
            raise FileExistsError(destination)
        if sidecar_destination is not None and sidecar_destination.exists():
            raise FileExistsError(sidecar_destination)
        planned.append((old, destination, sidecar if sidecar.exists() else None, sidecar_destination))

    archived: list[Path] = []
    for old, destination, sidecar, sidecar_destination in planned:
        shutil.move(str(old), str(destination))
        archived.append(destination)
        if sidecar is not None and sidecar_destination is not None:
            shutil.move(str(sidecar), str(sidecar_destination))
            archived.append(sidecar_destination)

    if copy_from_package:
        if target.exists():
            raise FileExistsError(target)
        target_sidecar = Path(str(target) + ".meta.json")
        source_sidecar = Path(str(source) + ".meta.json")
        if source_sidecar.exists() and target_sidecar.exists():
            raise FileExistsError(target_sidecar)
        shutil.copy2(source, target)
        if source_sidecar.exists():
            shutil.copy2(source_sidecar, target_sidecar)
    return {"latest": target, "archived": archived}


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
    if not allow_run_folder:
        # One-time machine assets live directly in data/.  Historical copies
        # are allowed only below 历史数据/{timestamp}; the human HTML history
        # remains a separate namespace.
        allowed = (
            len(relative.parts) == 2 and relative.parts[0] == "data"
        ) or (
            len(relative.parts) == 3 and relative.parts[0] == MACHINE_HISTORY_DIR_NAME
            and TIMESTAMP_RE.fullmatch(relative.parts[1] or "")
        ) or (
            len(relative.parts) == 3 and relative.parts[0] == SYSTEM_DIR_NAME
            and relative.parts[1] == STAGING_DIR_NAME
            and TIMESTAMP_RE.fullmatch(relative.parts[2] or "")
        ) or (
            len(relative.parts) == 1
        ) or (
            len(relative.parts) == 2 and relative.parts[0] == HUMAN_HISTORY_DIR_NAME
        )
        if not allowed:
            return "HZP_ONE_TIME_SKILL_RUN_FOLDER_FORBIDDEN"
        if len(relative.parts) == 1 and candidate.suffix.lower() in {".csv", ".json"}:
            return "HZP_ROOT_MACHINE_ASSET_FORBIDDEN"
    if allow_run_folder and len(relative.parts) not in (1, 2, 3, 4):
        return "HZP_SKILL_REPORT_DIR_INVALID"
    if not candidate.name.startswith(f"{number}_"):
        return "HZP_REPORT_PREFIX_MISSING"
    timestamps = re.findall(r"(?<!\d)(\d{8}_\d{6})(?!\d)", candidate.stem)
    if len(timestamps) != 1 or timestamps[0] != timestamp or not TIMESTAMP_RE.fullmatch(timestamp):
        return "HZP_REPORT_TIMESTAMP_INVALID"
    if report_identity and report_identity not in candidate.stem:
        return "HZP_REPORT_PREFIX_MISSING"
    if len(relative.parts) == 2 and relative.parts[0] == "data":
        return None
    if len(relative.parts) == 3 and relative.parts[:2] == (SYSTEM_DIR_NAME, STAGING_DIR_NAME):
        return None
    if len(relative.parts) >= 3 and relative.parts[0] == MACHINE_HISTORY_DIR_NAME and relative.parts[1] != timestamp:
        return "HZP_BATCH_TIMESTAMP_MISMATCH"
    if len(relative.parts) == 2 and relative.parts[0] != HUMAN_HISTORY_DIR_NAME and relative.parts[0] != timestamp:
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
