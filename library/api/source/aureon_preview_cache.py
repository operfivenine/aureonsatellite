"""Persistent scene/package preview locations owned by the Aureon folder."""
from __future__ import annotations

from pathlib import Path
import shutil
from aureon_paths import data_path

ROOT = data_path('previews')
SCENE_DIR = ROOT / "scenes" / "v2"
PACKAGE_DIR = ROOT / "packages" / "v1"


def clear_root_cache() -> int:
    if not ROOT.exists():
        return 0
    count = sum(1 for p in ROOT.rglob('*') if p.is_file())
    shutil.rmtree(ROOT, ignore_errors=True)
    return count
