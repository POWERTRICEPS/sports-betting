from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class PlayerProjection(BaseModel):
    game_id: str
    player_id: str
    espn_player_id: str
    player_name: str
    team_abbr: str
    opponent_abbr: str
    is_starter: bool
    projected_pts: float
    projected_reb: float
    projected_ast: float
    game_status: str = ""
    features: dict[str, dict[str, float]] | None = None
    model_outputs: dict[str, float] | None = None
    source: Literal["model", "mock"] = "model"


class PropsSnapshotResponse(BaseModel):
    updated_at: str | None
    projections: list[PlayerProjection]
