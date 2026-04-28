from __future__ import annotations

import os
import re
from pathlib import Path

_TASK_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def default_brain_root() -> Path:
    """Honor FORGE_BRAIN/FORGE_BRAIN_PATH, then ~/forge/brain."""
    for key in ("FORGE_BRAIN", "FORGE_BRAIN_PATH"):
        raw = os.environ.get(key, "").strip()
        if raw:
            return Path(raw).expanduser()
    return Path.home() / "forge" / "brain"


def sanitize_task_id(task_id: str) -> str:
    """Reject traversal and unsafe task-id values before path joins."""
    value = str(task_id).strip()
    if not value:
        raise ValueError("task_id must be non-empty")
    if "/" in value or "\\" in value or ".." in value:
        raise ValueError(f"unsafe task_id path component: {task_id!r}")
    if not _TASK_ID_RE.match(value):
        raise ValueError(
            f"task_id must match {_TASK_ID_RE.pattern!r}; got {task_id!r}"
        )
    return value

