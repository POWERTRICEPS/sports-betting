from __future__ import annotations

from datetime import datetime, UTC
from typing import Any

import state as app_state


def empty_snapshot() -> dict[str, Any]:
    return {
        "updated_at": None,
        "projections": [],
    }


def build_snapshot(projections: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "updated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "projections": projections,
    }


def get_snapshot() -> dict[str, Any]:
    if not app_state.PROPS_SNAPSHOT_STATE:
        return empty_snapshot()
    return dict(app_state.PROPS_SNAPSHOT_STATE)


def set_snapshot(payload: dict[str, Any]) -> None:
    app_state.PROPS_SNAPSHOT_STATE.clear()
    app_state.PROPS_SNAPSHOT_STATE.update(payload)
