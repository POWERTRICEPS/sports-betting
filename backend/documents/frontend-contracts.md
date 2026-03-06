# Frontend Contracts

This document defines frontend-facing contracts derived from current backend implementation.

## TypeScript Types

```ts
export interface GameWithProbability {
  game_id: string;
  status: string;

  home_team: string;
  home_city: string;
  home_abbreviation: string;
  home_wins: number;
  home_losses: number;
  home_score: number;
  home_q1: number | null;
  home_q2: number | null;
  home_q3: number | null;
  home_q4: number | null;

  home_leader_pts_name: string | null;
  home_leader_pts_val: string | null;
  home_leader_reb_name: string | null;
  home_leader_reb_val: string | null;
  home_leader_ast_name: string | null;
  home_leader_ast_val: string | null;

  home_reb: string | null;
  home_ast: string | null;
  home_fga: string | null;
  home_fgm: string | null;
  home_fta: string | null;
  home_ftm: string | null;
  home_points: string | null;
  home_3pa: string | null;
  home_3pm: string | null;

  away_team: string;
  away_city: string;
  away_abbreviation: string;
  away_wins: number;
  away_losses: number;
  away_score: number;
  away_q1: number | null;
  away_q2: number | null;
  away_q3: number | null;
  away_q4: number | null;

  away_leader_pts_name: string | null;
  away_leader_pts_val: string | null;
  away_leader_reb_name: string | null;
  away_leader_reb_val: string | null;
  away_leader_ast_name: string | null;
  away_leader_ast_val: string | null;

  away_reb: string | null;
  away_ast: string | null;
  away_fga: string | null;
  away_fgm: string | null;
  away_fta: string | null;
  away_ftm: string | null;
  away_points: string | null;
  away_3pa: string | null;
  away_3pm: string | null;

  home_win_prob: number | null; // percent scale [0,100]
  away_win_prob: number | null; // percent scale [0,100]
}

export interface TeamStanding {
  team_id: number;
  team_city: string;
  team_name: string;
  conference: "East" | "West";
  rank: number;
  record: string;
  win_pct: number;
  team_L10: string;
  curr_streak: string;
}

export interface LeagueStandingsItem {
  east_standings: TeamStanding[];
  west_standings: TeamStanding[];
}

export type LeagueStandingsResponse = LeagueStandingsItem[];
```

## REST Contracts

### `GET /api/games`
- Response: `GameWithProbability[]`
- Poll-safe for frontend refresh.

### `GET /api/games/stats/{game_id}`
- Response on success: `GameWithProbability`
- Response on missing `game_id`: non-standard error behavior; frontend should defensively handle unexpected response shape.

### `GET /api/standings`
- Response: `LeagueStandingsResponse`

### `GET /api/props`
- Response: `PropsSnapshotResponse`
- Current source: mock snapshot updated every 5 seconds by backend poll loop.
- Future source: same shape backed by live ML projections.

## WebSocket Contract

### Endpoint
- `ws://<host>/ws`

### Topics
- `games`: full snapshot stream (`GameWithProbability[]`).
- `game:<game_id>`: single-game stream (`GameWithProbability`).
- `props`: player props snapshot stream (`PropsSnapshotResponse`).

### Client-to-server messages
- Message type: text frame containing JSON.
- Subscribe:
```json
{"action":"subscribe","topic":"games"}
```
- Subscribe to one game:
```json
{"action":"subscribe","topic":"game:401706123"}
```
- Subscribe to props:
```json
{"action":"subscribe","topic":"props"}
```
- Unsubscribe:
```json
{"action":"unsubscribe","topic":"game:401706123"}
```
- Heartbeat:
  - Non-JSON text is allowed and ignored by backend.

### Server-to-client events
- Message type: text frame containing JSON.
- Subscription ack shape:
```json
{"ok":true,"action":"subscribe","topic":"games"}
```
- `games` topic payload: `GameWithProbability[]`.
- `game:<game_id>` topic payload: `GameWithProbability`.
- `props` topic payload: `PropsSnapshotResponse`.

## Player Props Contracts

### TypeScript Types

```ts
export interface PlayerProjection {
  game_id: string;
  player_id: string; // backend primary id (string for transport consistency)
  espn_player_id: string; // required for frontend headshot rendering
  player_name: string;
  team_abbr: string;
  opponent_abbr: string;
  is_starter: boolean;
  projected_pts: number;
  projected_reb: number;
  projected_ast: number;
  source: "mock" | "model";
}

export interface PropsSnapshotResponse {
  updated_at: string | null;
  projections: PlayerProjection[];
}
```

### Frontend Mapping Notes

- Frontend props card should map `espn_player_id` to UI field `espnPlayerId`.
- Headshot URL format:
  - `https://a.espncdn.com/i/headshots/nba/players/full/{espn_player_id}.png`
- If `espn_player_id` is missing/invalid, frontend should show fallback initials/avatar.

### Future-Proofing Rules

- Keep `PropsSnapshotResponse` shape stable when switching from mock data to ML model output.
- Only change `source` from `"mock"` to `"model"` and update numeric projection values.
- Do not remove `espn_player_id`; this is required for consistent image rendering.

## Contract Caveats

- `home_win_prob`/`away_win_prob` use percentage scale (`0` to `100`), not normalized probability (`0` to `1`).
- Some stats/leader fields may be `null` when source feed omits data.
- `game_id` is treated as string in responses.
- `/api/games/stats?game_date=...` is currently non-functional and should not be integrated.
