from __future__ import annotations

import asyncio
from typing import Any

from .broadcast import broadcast_props_snapshot
from .service import compute_live_props_snapshot
from .store import set_snapshot


async def update_player_props(manager: Any, game_date: str | None = None) -> None:
    payload = await asyncio.to_thread(compute_live_props_snapshot, game_date)
    set_snapshot(payload)
    await broadcast_props_snapshot(manager, payload)


async def props_poll_loop(manager: Any, interval_s: int = 30) -> None:
    while True:
        try:
            await update_player_props(manager)
        except Exception as e:
            print(f"props poll loop error: {e}")
        await asyncio.sleep(interval_s)
