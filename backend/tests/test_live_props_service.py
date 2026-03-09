from __future__ import annotations

import os
import sys
import unittest
from unittest.mock import patch

ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from services.live_props.service import compute_live_props_snapshot


class LivePropsServiceTest(unittest.TestCase):
    @patch(
        "services.live_props.service.predict_remaining",
        side_effect=[10.0] * 60,
    )
    @patch(
        "services.live_props.service.get_player_season_features",
        return_value={
            "season_ppg": 20.0,
            "season_fga": 15.0,
            "season_mpg": 32.0,
            "season_3pa": 5.0,
            "season_rebounds": 7.0,
            "season_assists": 6.0,
        },
    )
    @patch("services.live_props.service._summary_for_game")
    @patch("services.live_props.service.fetch_espn_lineups")
    def test_pregame_fallback_projects_starters_when_no_live_players(
        self,
        mock_lineups,
        mock_summary,
        _mock_season,
        _mock_predict,
    ) -> None:
        mock_lineups.return_value = {
            "games": [
                {
                    "game_id": "401000001",
                    "home_team": {
                        "team_abbreviation": "LAL",
                        "starters": [
                            {"player_id": "101", "espn_player_id": "101", "name": "Fallback Home 1", "salary": 100, "jersey": "1"},
                            {"player_id": "102", "espn_player_id": "102", "name": "Fallback Home 2", "salary": 99, "jersey": "2"},
                        ],
                    },
                    "away_team": {
                        "team_abbreviation": "DEN",
                        "starters": [
                            {"player_id": "201", "espn_player_id": "201", "name": "Fallback Away 1", "salary": 100, "jersey": "1"},
                            {"player_id": "202", "espn_player_id": "202", "name": "Fallback Away 2", "salary": 99, "jersey": "2"},
                        ],
                    },
                }
            ]
        }

        mock_summary.return_value = {
            "header": {
                "competitions": [
                    {
                        "status": {"type": {"shortDetail": "7:30 PM ET"}},
                        "competitors": [
                            {"homeAway": "home", "score": "0", "team": {"abbreviation": "LAL"}},
                            {"homeAway": "away", "score": "0", "team": {"abbreviation": "DEN"}},
                        ],
                    }
                ]
            },
            "boxscore": {
                "players": []
            },
        }

        payload = compute_live_props_snapshot(game_date="20260308", debug=True)

        self.assertEqual(len(payload["projections"]), 4)
        self.assertEqual(payload["debug"]["games_total"], 1)
        self.assertEqual(payload["debug"]["skips"]["no_live_players"], 1)
        self.assertEqual(payload["debug"]["players_projected"], 4)
        self.assertEqual(payload["debug"]["fallback_used_pregame"], 2)
        self.assertEqual(payload["debug"]["fallback_candidates_selected"], 4)
        for row in payload["projections"]:
            self.assertFalse(row["is_starter"])

    @patch("services.live_props.service.predict_remaining", side_effect=[1.0] * 30)
    @patch(
        "services.live_props.service.get_player_season_features",
        return_value={
            "season_ppg": 20.0,
            "season_fga": 15.0,
            "season_mpg": 32.0,
            "season_3pa": 5.0,
            "season_rebounds": 7.0,
            "season_assists": 6.0,
        },
    )
    @patch("services.live_props.service._summary_for_game")
    @patch("services.live_props.service.fetch_espn_lineups")
    def test_live_no_starters_uses_boxscore_top_minutes(
        self,
        mock_lineups,
        mock_summary,
        _mock_season,
        _mock_predict,
    ) -> None:
        mock_lineups.return_value = {
            "games": [
                {
                    "game_id": "401810000",
                    "home_team": {
                        "team_abbreviation": "LAL",
                        "starters": [
                            {"player_id": f"h{i}", "espn_player_id": f"h{i}", "name": f"H{i}", "salary": 100 - i, "jersey": str(i)}
                            for i in range(5)
                        ],
                    },
                    "away_team": {
                        "team_abbreviation": "DEN",
                        "starters": [
                            {"player_id": f"a{i}", "espn_player_id": f"a{i}", "name": f"A{i}", "salary": 100 - i, "jersey": str(i)}
                            for i in range(5)
                        ],
                    },
                }
            ]
        }
        labels = ["MIN", "FG", "3PT", "REB", "AST", "PTS"]
        home_athletes = [
            {"athlete": {"id": f"h{i}", "displayName": f"H{i}"}, "stats": [f"{40-i}:00", "1-2", "0-1", "2", "3", str(10+i)]}
            for i in range(6)
        ]
        away_athletes = [
            {"athlete": {"id": f"a{i}", "displayName": f"A{i}"}, "stats": [f"{39-i}:00", "1-2", "0-1", "2", "3", str(12+i)]}
            for i in range(6)
        ]
        mock_summary.return_value = {
            "header": {
                "competitions": [
                    {
                        "status": {"type": {"shortDetail": "6:00 - 3rd"}},
                        "competitors": [
                            {"homeAway": "home", "score": "80", "team": {"abbreviation": "LAL"}},
                            {"homeAway": "away", "score": "76", "team": {"abbreviation": "DEN"}},
                        ],
                    }
                ]
            },
            "boxscore": {
                "players": [
                    {"team": {"abbreviation": "LAL"}, "statistics": [{"labels": labels, "athletes": home_athletes}]},
                    {"team": {"abbreviation": "DEN"}, "statistics": [{"labels": labels, "athletes": away_athletes}]},
                ]
            },
        }

        payload = compute_live_props_snapshot(game_date="20260308", debug=True)
        self.assertEqual(len(payload["projections"]), 10)
        self.assertEqual(payload["debug"]["fallback_used_live_or_final"], 2)
        self.assertEqual(payload["debug"]["fallback_candidates_selected"], 10)
        self.assertTrue(all(not row["is_starter"] for row in payload["projections"]))

    @patch("services.live_props.service.predict_remaining", side_effect=[1.0] * 30)
    @patch(
        "services.live_props.service.get_player_season_features",
        return_value={
            "season_ppg": 20.0,
            "season_fga": 15.0,
            "season_mpg": 32.0,
            "season_3pa": 5.0,
            "season_rebounds": 7.0,
            "season_assists": 6.0,
        },
    )
    @patch("services.live_props.service._summary_for_game")
    @patch("services.live_props.service.fetch_espn_lineups")
    def test_final_no_starters_uses_boxscore_top_minutes(
        self,
        mock_lineups,
        mock_summary,
        _mock_season,
        _mock_predict,
    ) -> None:
        mock_lineups.return_value = {
            "games": [
                {
                    "game_id": "401810001",
                    "home_team": {
                        "team_abbreviation": "MIN",
                        "starters": [
                            {"player_id": f"fh{i}", "espn_player_id": f"fh{i}", "name": f"FH{i}", "salary": 100 - i, "jersey": str(i)}
                            for i in range(5)
                        ],
                    },
                    "away_team": {
                        "team_abbreviation": "ORL",
                        "starters": [
                            {"player_id": f"fa{i}", "espn_player_id": f"fa{i}", "name": f"FA{i}", "salary": 100 - i, "jersey": str(i)}
                            for i in range(5)
                        ],
                    },
                }
            ]
        }
        labels = ["MIN", "FG", "3PT", "REB", "AST", "PTS"]
        home_athletes = [
            {"athlete": {"id": f"fh{i}", "displayName": f"FH{i}"}, "stats": [f"{38-i}:00", "1-2", "0-1", "2", "3", str(11+i)]}
            for i in range(5)
        ]
        away_athletes = [
            {"athlete": {"id": f"fa{i}", "displayName": f"FA{i}"}, "stats": [f"{37-i}:00", "1-2", "0-1", "2", "3", str(9+i)]}
            for i in range(5)
        ]
        mock_summary.return_value = {
            "header": {
                "competitions": [
                    {
                        "status": {"type": {"shortDetail": "Final"}},
                        "competitors": [
                            {"homeAway": "home", "score": "110", "team": {"abbreviation": "MIN"}},
                            {"homeAway": "away", "score": "104", "team": {"abbreviation": "ORL"}},
                        ],
                    }
                ]
            },
            "boxscore": {
                "players": [
                    {"team": {"abbreviation": "MIN"}, "statistics": [{"labels": labels, "athletes": home_athletes}]},
                    {"team": {"abbreviation": "ORL"}, "statistics": [{"labels": labels, "athletes": away_athletes}]},
                ]
            },
        }

        payload = compute_live_props_snapshot(game_date="20260308", debug=True)
        self.assertEqual(len(payload["projections"]), 10)
        self.assertEqual(payload["debug"]["fallback_used_live_or_final"], 2)
        self.assertEqual(payload["debug"]["fallback_candidates_selected"], 10)

    @patch("services.live_props.service.predict_remaining", side_effect=[4.41, 0.84, 0.83])
    @patch(
        "services.live_props.service.get_player_season_features",
        return_value={
            "season_ppg": 20.0,
            "season_fga": 15.0,
            "season_mpg": 32.0,
            "season_3pa": 5.0,
            "season_rebounds": 7.0,
            "season_assists": 6.0,
        },
    )
    @patch("services.live_props.service._summary_for_game")
    @patch("services.live_props.service.fetch_espn_lineups")
    def test_live_projection_returns_implied_finals(
        self,
        mock_lineups,
        mock_summary,
        _mock_season,
        _mock_predict,
    ) -> None:
        mock_lineups.return_value = {
            "games": [
                {
                    "game_id": "401810772",
                    "home_team": {
                        "team_abbreviation": "PHI",
                        "starters": [{"player_id": "4431678", "espn_player_id": "4431678", "name": "Tyrese Maxey"}],
                    },
                    "away_team": {
                        "team_abbreviation": "ATL",
                        "starters": [],
                    },
                }
            ]
        }

        labels = [
            "MIN", "FG", "3PT", "FT", "OREB", "DREB", "REB",
            "AST", "STL", "BLK", "TO", "PF", "+/-", "PTS"
        ]
        stats = [
            "30:00", "8-16", "2-6", "4-5", "1", "2", "3",
            "2", "1", "0", "2", "3", "+4", "22"
        ]

        mock_summary.return_value = {
            "header": {
                "competitions": [
                    {
                        "status": {"type": {"shortDetail": "6:00 - 3rd"}},
                        "competitors": [
                            {"homeAway": "home", "score": "80", "team": {"abbreviation": "PHI"}},
                            {"homeAway": "away", "score": "76", "team": {"abbreviation": "ATL"}},
                        ],
                    }
                ]
            },
            "boxscore": {
                "players": [
                    {
                        "team": {"abbreviation": "PHI"},
                        "statistics": [
                            {
                                "labels": labels,
                                "athletes": [
                                    {
                                        "athlete": {"id": "4431678", "displayName": "Tyrese Maxey"},
                                        "stats": stats,
                                    }
                                ],
                            }
                        ],
                    }
                ]
            },
        }

        payload = compute_live_props_snapshot(game_date="20260308", debug=True)
        self.assertEqual(len(payload["projections"]), 1)
        row = payload["projections"][0]
        self.assertEqual(row["player_name"], "Tyrese Maxey")
        self.assertEqual(row["projected_pts"], 26.41)
        self.assertEqual(row["projected_reb"], 3.84)
        self.assertEqual(row["projected_ast"], 2.83)
        self.assertIn("features", row)
        self.assertIn("pts_model", row["features"])
        self.assertIn("reb_model", row["features"])
        self.assertIn("ast_model", row["features"])
        self.assertIn("model_outputs", row)
        self.assertEqual(row["model_outputs"]["pts_remaining_raw"], 4.41)
        self.assertEqual(row["model_outputs"]["pts_implied_final"], 26.41)
        self.assertTrue(row["is_starter"])
        self.assertEqual(payload["debug"]["fallback_used_pregame"], 0)
        self.assertEqual(payload["debug"]["fallback_used_live_or_final"], 0)

    @patch("services.live_props.service.predict_remaining", side_effect=[2.0, 1.0, 1.0])
    @patch(
        "services.live_props.service.get_player_season_features",
        return_value={
            "season_ppg": 20.0,
            "season_fga": 15.0,
            "season_mpg": 32.0,
            "season_3pa": 5.0,
            "season_rebounds": 7.0,
            "season_assists": 6.0,
        },
    )
    @patch("services.live_props.service._summary_for_game")
    @patch("services.live_props.service.fetch_espn_lineups")
    def test_prefers_espn_player_id_over_player_id(
        self,
        mock_lineups,
        mock_summary,
        _mock_season,
        _mock_predict,
    ) -> None:
        mock_lineups.return_value = {
            "games": [
                {
                    "game_id": "401810773",
                    "home_team": {
                        "team_abbreviation": "PHI",
                        "starters": [{"player_id": "legacy-id", "espn_player_id": "4431678", "name": "Tyrese Maxey"}],
                    },
                    "away_team": {
                        "team_abbreviation": "ATL",
                        "starters": [],
                    },
                }
            ]
        }
        labels = [
            "MIN", "FG", "3PT", "FT", "OREB", "DREB", "REB",
            "AST", "STL", "BLK", "TO", "PF", "+/-", "PTS"
        ]
        stats = [
            "30:00", "8-16", "2-6", "4-5", "1", "2", "3",
            "2", "1", "0", "2", "3", "+4", "22"
        ]
        mock_summary.return_value = {
            "header": {
                "competitions": [
                    {
                        "status": {"type": {"shortDetail": "6:00 - 3rd"}},
                        "competitors": [
                            {"homeAway": "home", "score": "80", "team": {"abbreviation": "PHI"}},
                            {"homeAway": "away", "score": "76", "team": {"abbreviation": "ATL"}},
                        ],
                    }
                ]
            },
            "boxscore": {
                "players": [
                    {
                        "team": {"abbreviation": "PHI"},
                        "statistics": [
                            {
                                "labels": labels,
                                "athletes": [
                                    {
                                        "athlete": {"id": "4431678", "displayName": "Tyrese Maxey"},
                                        "stats": stats,
                                    }
                                ],
                            }
                        ],
                    }
                ]
            },
        }

        payload = compute_live_props_snapshot(game_date="20260308", debug=True)
        self.assertEqual(len(payload["projections"]), 1)
        row = payload["projections"][0]
        self.assertEqual(row["player_id"], "4431678")
        self.assertEqual(row["espn_player_id"], "4431678")

    @patch("services.live_props.service.predict_remaining", side_effect=[4.41, 0.84, 0.83, 4.41, 0.84, 0.83])
    @patch(
        "services.live_props.service.get_player_season_features",
        return_value={
            "season_ppg": 20.0,
            "season_fga": 15.0,
            "season_mpg": 32.0,
            "season_3pa": 5.0,
            "season_rebounds": 7.0,
            "season_assists": 6.0,
        },
    )
    @patch("services.live_props.service._summary_for_game")
    @patch("services.live_props.service.fetch_espn_lineups")
    def test_non_debug_payload_omits_feature_blocks(
        self,
        mock_lineups,
        mock_summary,
        _mock_season,
        _mock_predict,
    ) -> None:
        mock_lineups.return_value = {
            "games": [
                {
                    "game_id": "401810772",
                    "home_team": {
                        "team_abbreviation": "PHI",
                        "starters": [{"player_id": "4431678", "espn_player_id": "4431678", "name": "Tyrese Maxey"}],
                    },
                    "away_team": {
                        "team_abbreviation": "ATL",
                        "starters": [],
                    },
                }
            ]
        }
        labels = [
            "MIN", "FG", "3PT", "FT", "OREB", "DREB", "REB",
            "AST", "STL", "BLK", "TO", "PF", "+/-", "PTS"
        ]
        stats = [
            "30:00", "8-16", "2-6", "4-5", "1", "2", "3",
            "2", "1", "0", "2", "3", "+4", "22"
        ]
        mock_summary.return_value = {
            "header": {
                "competitions": [
                    {
                        "status": {"type": {"shortDetail": "6:00 - 3rd"}},
                        "competitors": [
                            {"homeAway": "home", "score": "80", "team": {"abbreviation": "PHI"}},
                            {"homeAway": "away", "score": "76", "team": {"abbreviation": "ATL"}},
                        ],
                    }
                ]
            },
            "boxscore": {
                "players": [
                    {
                        "team": {"abbreviation": "PHI"},
                        "statistics": [
                            {
                                "labels": labels,
                                "athletes": [
                                    {
                                        "athlete": {"id": "4431678", "displayName": "Tyrese Maxey"},
                                        "stats": stats,
                                    }
                                ],
                            }
                        ],
                    }
                ]
            },
        }

        prod_payload = compute_live_props_snapshot(game_date="20260308", debug=False)
        debug_payload = compute_live_props_snapshot(game_date="20260308", debug=True)

        self.assertEqual(len(prod_payload["projections"]), 1)
        self.assertEqual(len(debug_payload["projections"]), 1)
        self.assertNotIn("features", prod_payload["projections"][0])
        self.assertNotIn("model_outputs", prod_payload["projections"][0])
        self.assertIn("features", debug_payload["projections"][0])
        self.assertIn("model_outputs", debug_payload["projections"][0])


if __name__ == "__main__":
    unittest.main()
