"""
topology_reader.py — Parse the ``## Service Topology`` section of product.md.

Produces a ``Topology`` object consumed by phase5 and phase56 to:
  - Declare which service calls which (HTTP/RPC fallback for dynamic URLs)
  - Map Kafka/event topic publishers and subscribers
  - Record DB ownership per service
  - Record config keys per service

Product.md format (additive — existing product.md without this section still works):

    ## Service Topology

    ### backend-api
    calls: [auth-service, notification-service]
    publishes: [user.created, order.placed]
    db-owner: [users_db, orders_db]
    config: [DATABASE_URL, JWT_SECRET]

    ### frontend
    calls: [backend-api]
    subscribes: []
    config: [NEXT_PUBLIC_API_URL]

    ### auth-service
    calls: []
    subscribes: [user.created]
    db-owner: [auth_db]
    config: [JWT_SECRET, REDIS_URL]

Unknown keys are silently ignored (forward-compatible).
If the section is absent or parsing fails, ``read_topology`` returns ``None``
and callers fall back to URL-only mode.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class ServiceEntry:
    role: str
    calls: list[str] = field(default_factory=list)
    publishes: list[str] = field(default_factory=list)
    subscribes: list[str] = field(default_factory=list)
    db_owner: list[str] = field(default_factory=list)
    config: list[str] = field(default_factory=list)


@dataclass
class Topology:
    services: dict[str, ServiceEntry] = field(default_factory=dict)

    # Derived convenience views (populated by read_topology)
    call_edges: list[tuple[str, str]] = field(default_factory=list)
    # (role, topic, "pub" | "sub")
    topic_edges: list[tuple[str, str, str]] = field(default_factory=list)
    # (role, db_name)
    db_edges: list[tuple[str, str]] = field(default_factory=list)

    def callers_of(self, callee_role: str) -> list[str]:
        """Return all roles that declare ``calls: [callee_role]``."""
        return [src for src, dst in self.call_edges if dst == callee_role]

    def callees_of(self, caller_role: str) -> list[str]:
        """Return all roles that ``caller_role`` declares it calls."""
        return [dst for src, dst in self.call_edges if src == caller_role]

    def publishers_of(self, topic: str) -> list[str]:
        return [role for role, t, kind in self.topic_edges if t == topic and kind == "pub"]

    def subscribers_of(self, topic: str) -> list[str]:
        return [role for role, t, kind in self.topic_edges if t == topic and kind == "sub"]

    def all_topics(self) -> set[str]:
        return {t for _, t, _ in self.topic_edges}


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

_SECTION_H2 = re.compile(r"^##\s+(.+)$")
_SERVICE_H3 = re.compile(r"^###\s+(.+)$")
_KV_LINE = re.compile(r"^\s*([a-zA-Z_-]+)\s*:\s*\[([^\]]*)\]\s*$")


def _parse_list(raw: str) -> list[str]:
    """Parse ``item1, item2, item3`` inside ``[...]`` into a Python list."""
    return [item.strip() for item in raw.split(",") if item.strip()]


def _extract_topology_section(text: str) -> str | None:
    """
    Return the raw text of the ``## Service Topology`` section,
    or ``None`` if not present.
    """
    lines = text.splitlines()
    in_section = False
    section_lines: list[str] = []
    for line in lines:
        m = _SECTION_H2.match(line)
        if m:
            if m.group(1).strip().lower() == "service topology":
                in_section = True
                continue
            elif in_section:
                break  # reached next ## heading — stop
        if in_section:
            section_lines.append(line)
    return "\n".join(section_lines) if section_lines else None


def _parse_service_entries(section_text: str) -> dict[str, ServiceEntry]:
    entries: dict[str, ServiceEntry] = {}
    current: ServiceEntry | None = None

    for line in section_text.splitlines():
        h3 = _SERVICE_H3.match(line)
        if h3:
            role = h3.group(1).strip()
            current = ServiceEntry(role=role)
            entries[role] = current
            continue

        if current is None:
            continue

        kv = _KV_LINE.match(line)
        if not kv:
            continue

        key = kv.group(1).strip().lower()
        values = _parse_list(kv.group(2))

        if key == "calls":
            current.calls = values
        elif key == "publishes":
            current.publishes = values
        elif key == "subscribes":
            current.subscribes = values
        elif key in ("db-owner", "db_owner"):
            current.db_owner = values
        elif key == "config":
            current.config = values
        # Unknown keys silently ignored

    return entries


def _build_topology(entries: dict[str, ServiceEntry]) -> Topology:
    topo = Topology(services=entries)

    for role, entry in entries.items():
        for callee in entry.calls:
            topo.call_edges.append((role, callee))
        for topic in entry.publishes:
            topo.topic_edges.append((role, topic, "pub"))
        for topic in entry.subscribes:
            topo.topic_edges.append((role, topic, "sub"))
        for db in entry.db_owner:
            topo.db_edges.append((role, db))

    return topo


def read_topology(product_md: Path) -> Topology | None:
    """
    Parse ``product_md`` and return a ``Topology`` or ``None``.

    Returns ``None`` when:
    - File does not exist or cannot be read
    - ``## Service Topology`` section is absent
    - No valid ``### ServiceName`` blocks found
    - Any unexpected parse error

    Callers must treat ``None`` as "no topology declared — fall back to
    URL-only cross-repo matching".
    """
    if not product_md or not product_md.is_file():
        return None
    try:
        text = product_md.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None

    try:
        section = _extract_topology_section(text)
        if not section:
            return None
        entries = _parse_service_entries(section)
        if not entries:
            return None
        return _build_topology(entries)
    except Exception:  # noqa: BLE001
        # Never crash the scan pipeline due to topology parsing errors
        return None
