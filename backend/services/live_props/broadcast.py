from __future__ import annotations

from typing import Any


async def broadcast_props_snapshot(manager: Any, payload: dict[str, Any]) -> None:
    count = len(payload.get("projections") or [])
    targets = manager.topic_connection_labels("props")
    print(
        f"[broadcast] topic=props payload=PropsSnapshot projections={count} "
        f"subscribers={len(targets)} active_total={len(manager.active_connections)} "
        f"targets={targets}"
    )
    await manager.broadcast_to_topic("props", payload)
