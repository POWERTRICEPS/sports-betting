from __future__ import annotations

import os
import sys
import unittest
from unittest.mock import patch

ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from util import fetch_salary_based_lineups, _pick_starters_by_salary


class _FakeResponse:
    def __init__(self, payload: dict, raise_error: Exception | None = None):
        self._payload = payload
        self._raise_error = raise_error

    def raise_for_status(self) -> None:
        if self._raise_error is not None:
            raise self._raise_error

    def json(self) -> dict:
        return self._payload


def _scoreboard_payload() -> dict:
    return {
        "events": [
            {
                "id": "401000001",
                "competitions": [
                    {
                        "competitors": [
                            {
                                "homeAway": "home",
                                "team": {"displayName": "Lakers", "abbreviation": "LAL"},
                            },
                            {
                                "homeAway": "away",
                                "team": {"displayName": "Nuggets", "abbreviation": "DEN"},
                            },
                        ]
                    }
                ],
            }
        ]
    }


def _posted_starters_summary(home_count: int, away_count: int) -> dict:
    def _athletes(prefix: str, count: int) -> list[dict]:
        athletes = []
        for i in range(count):
            athletes.append(
                {
                    "starter": True,
                    "athlete": {
                        "id": f"{prefix}{i}",
                        "displayName": f"{prefix.upper()} Player {i}",
                        "position": {"abbreviation": "G"},
                    },
                }
            )
        return athletes

    return {
        "boxscore": {
            "players": [
                {
                    "team": {"abbreviation": "LAL"},
                    "statistics": [{"athletes": _athletes("h", home_count)}],
                },
                {
                    "team": {"abbreviation": "DEN"},
                    "statistics": [{"athletes": _athletes("a", away_count)}],
                },
            ]
        }
    }


class SalaryBasedLineupsTest(unittest.TestCase):
    def test_pick_starters_prefers_positive_salary_players(self) -> None:
        roster = [
            {"name": "G1", "position": "G", "salary": 10, "player_id": "g1", "espn_player_id": "g1", "jersey": "1"},
            {"name": "G2", "position": "G", "salary": 9, "player_id": "g2", "espn_player_id": "g2", "jersey": "2"},
            {"name": "F1", "position": "F", "salary": 8, "player_id": "f1", "espn_player_id": "f1", "jersey": "3"},
            {"name": "F2", "position": "F", "salary": 7, "player_id": "f2", "espn_player_id": "f2", "jersey": "4"},
            {"name": "X1", "position": "F", "salary": 6, "player_id": "x1", "espn_player_id": "x1", "jersey": "5"},
            {"name": "C0", "position": "C", "salary": 0, "player_id": "c0", "espn_player_id": "c0", "jersey": "6"},
        ]

        starters = _pick_starters_by_salary(roster)
        salaries = [float(p.get("salary") or 0) for p in starters]
        player_ids = {p["player_id"] for p in starters}

        self.assertEqual(len(starters), 5)
        self.assertTrue(all(s > 0 for s in salaries))
        self.assertNotIn("c0", player_ids)

    def test_pick_starters_allows_zero_salary_when_not_enough_positive_players(self) -> None:
        roster = [
            {"name": "G1", "position": "G", "salary": 10, "player_id": "g1", "espn_player_id": "g1", "jersey": "1"},
            {"name": "G2", "position": "G", "salary": 9, "player_id": "g2", "espn_player_id": "g2", "jersey": "2"},
            {"name": "F1", "position": "F", "salary": 8, "player_id": "f1", "espn_player_id": "f1", "jersey": "3"},
            {"name": "C1", "position": "C", "salary": 7, "player_id": "c1", "espn_player_id": "c1", "jersey": "4"},
            {"name": "X0", "position": "F", "salary": 0, "player_id": "x0", "espn_player_id": "x0", "jersey": "5"},
        ]

        starters = _pick_starters_by_salary(roster)
        player_ids = {p["player_id"] for p in starters}

        self.assertEqual(len(starters), 5)
        self.assertIn("x0", player_ids)

    @patch("util._pick_starters_by_salary")
    @patch("util._fetch_team_roster")
    @patch("util.requests.get")
    def test_both_teams_posted_starters_no_fallback(
        self,
        mock_get,
        mock_roster,
        mock_pick,
    ) -> None:
        mock_get.side_effect = [
            _FakeResponse(_scoreboard_payload()),
            _FakeResponse(_posted_starters_summary(home_count=5, away_count=5)),
        ]

        payload = fetch_salary_based_lineups("20260308")

        self.assertEqual(payload["lineup_status"], "confirmed")
        self.assertEqual(payload["total_games"], 1)
        self.assertEqual(len(payload["games"][0]["home_team"]["starters"]), 5)
        self.assertEqual(len(payload["games"][0]["away_team"]["starters"]), 5)
        self.assertFalse(mock_roster.called)
        self.assertFalse(mock_pick.called)

    @patch("util._pick_starters_by_salary")
    @patch("util._fetch_team_roster")
    @patch("util.requests.get")
    def test_partial_posted_starters_fallback_per_team_only(
        self,
        mock_get,
        mock_roster,
        mock_pick,
    ) -> None:
        mock_get.side_effect = [
            _FakeResponse(_scoreboard_payload()),
            _FakeResponse(_posted_starters_summary(home_count=5, away_count=0)),
        ]
        mock_roster.return_value = [{"name": "Fallback A", "position": "F", "salary": 1, "player_id": "fa", "espn_player_id": "fa", "jersey": "1"}]
        mock_pick.return_value = [{"name": "Fallback A", "position": "F", "salary": 1, "player_id": "fa", "espn_player_id": "fa", "jersey": "1"}]

        payload = fetch_salary_based_lineups("20260308")
        game = payload["games"][0]
        home_starters = game["home_team"]["starters"]
        away_starters = game["away_team"]["starters"]

        self.assertEqual(payload["lineup_status"], "confirmed")
        self.assertEqual(len(home_starters), 5)
        self.assertEqual(len(away_starters), 1)
        self.assertEqual(mock_roster.call_count, 1)
        self.assertEqual(mock_pick.call_count, 1)
        for row in home_starters + away_starters:
            self.assertIn("player_id", row)
            self.assertIn("espn_player_id", row)

    @patch("util._pick_starters_by_salary")
    @patch("util._fetch_team_roster")
    @patch("util.requests.get")
    def test_summary_failure_falls_back_for_both_teams(
        self,
        mock_get,
        mock_roster,
        mock_pick,
    ) -> None:
        mock_get.side_effect = [
            _FakeResponse(_scoreboard_payload()),
            _FakeResponse({}, raise_error=Exception("summary failed")),
        ]
        mock_roster.return_value = [{"name": "Fallback A", "position": "F", "salary": 1, "player_id": "fa", "espn_player_id": "fa", "jersey": "1"}]
        mock_pick.return_value = [{"name": "Fallback A", "position": "F", "salary": 1, "player_id": "fa", "espn_player_id": "fa", "jersey": "1"}]

        payload = fetch_salary_based_lineups("20260308")
        game = payload["games"][0]

        self.assertEqual(payload["lineup_status"], "projected")
        self.assertEqual(len(game["home_team"]["starters"]), 1)
        self.assertEqual(len(game["away_team"]["starters"]), 1)
        self.assertEqual(mock_roster.call_count, 2)
        self.assertEqual(mock_pick.call_count, 2)

    @patch("util.requests.get")
    def test_no_games_returns_not_available(self, mock_get) -> None:
        mock_get.return_value = _FakeResponse({"events": []})

        payload = fetch_salary_based_lineups("20260308")

        self.assertEqual(payload["lineup_status"], "not_available")
        self.assertEqual(payload["games"], [])
        self.assertEqual(payload["total_games"], 0)


if __name__ == "__main__":
    unittest.main()
