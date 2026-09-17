"""Compatibility shim to the single shared HZP report contract.

The 6-0-2 Skill previously carried a snapshot of the report system.  Keeping
this import shim preserves old direct imports while ensuring all path,
registry, staging and rollback behavior comes from the shared implementation.
"""
from __future__ import annotations
import sys
from pathlib import Path

_SHARED_ROOT = Path(__file__).resolve().parents[2]
if str(_SHARED_ROOT) not in sys.path:
    sys.path.insert(0, str(_SHARED_ROOT))
from scripts.hzp_amz_report_contract import *  # noqa: F401,F403,E402
