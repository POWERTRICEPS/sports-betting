from __future__ import annotations

import os
import sys
import unittest
from unittest.mock import patch

ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from services.live_props import season_stats


class SeasonStatsTest(unittest.TestCase):
    def setUp(self) -> None:
        season_stats._cache_date = None
        season_stats._season_feature_cache.clear()
        season_stats._espn_to_nba_id_cache.clear()
        season_stats._nba_season_tables.clear()

    def test_parse_espn_payload(self) -> None:
        payload = {
            "categories": [
                {
                    "name": "avg",
                    "stats": [
                        {"name": "ppg", "displayValue": "27.1"},
                        {"name": "fga", "displayValue": "20.4"},
                        {"name": "mpg", "displayValue": "35.2"},
                        {"name": "3pa", "displayValue": "8.1"},
                        {"name": "rpg", "displayValue": "7.8"},
                        {"name": "apg", "displayValue": "8.6"},
                    ],
                }
            ]
        }

        features = season_stats._parse_espn_payload(payload)
        self.assertIsNotNone(features)
        self.assertEqual(features["season_ppg"], 27.1)
        self.assertEqual(features["season_fga"], 20.4)
        self.assertEqual(features["season_mpg"], 35.2)
        self.assertEqual(features["season_3pa"], 8.1)
        self.assertEqual(features["season_rebounds"], 7.8)
        self.assertEqual(features["season_assists"], 8.6)

    def test_parse_espn_payload_avg_core_fields(self) -> None:
        payload = {
            "splits": {
                "categories": [
                    {
                        "name": "general",
                        "stats": [
                            {"name": "avgMinutes", "value": 32.14101},
                            {"name": "avgRebounds", "value": 8.965071},
                        ],
                    },
                    {
                        "name": "offensive",
                        "stats": [
                            {"name": "avgPoints", "value": 19.23674},
                            {"name": "avgFieldGoalsAttempted", "value": 14.693402},
                            {"name": "avgThreePointFieldGoalsAttempted", "value": 3.6636481},
                            {"name": "avgAssists", "value": 3.939198},
                            # Totals should be ignored by sanity ranges when avg* exists.
                            {"name": "fieldGoalsAttempted", "value": 11358},
                            {"name": "threePointFieldGoalsAttempted", "value": 2832},
                        ],
                    },
                ]
            }
        }

        features = season_stats._parse_espn_payload(payload)
        self.assertIsNotNone(features)
        self.assertEqual(features["season_ppg"], 19.23674)
        self.assertEqual(features["season_fga"], 14.693402)
        self.assertEqual(features["season_mpg"], 32.14101)
        self.assertEqual(features["season_3pa"], 3.6636481)
        self.assertEqual(features["season_rebounds"], 8.965071)
        self.assertEqual(features["season_assists"], 3.939198)

    def test_parse_espn_common_v3_payload(self) -> None:
        payload = {
            "categories": [
                {
                    "name": "averages",
                    "labels": [
                        "GP", "GS", "MIN", "FG", "FG%", "3PT", "3P%", "FT", "FT%", "OR", "DR",
                        "REB", "AST", "BLK", "STL", "PF", "TO", "PTS"
                    ],
                    "statistics": [
                        {
                            "season": {"year": 2025, "displayName": "2024-25"},
                            "stats": ["76", "76", "34.2", "11.3-21.8", "51.9", "2.1-5.7", "37.5", "7.9-8.8", "89.8", "0.9", "4.1", "5.0", "6.4", "1.0", "1.7", "2.2", "2.4", "32.7"],
                        },
                        {
                            "season": {"year": 2026, "displayName": "2025-26"},
                            "stats": ["52", "52", "33.4", "10.9-19.8", "55.1", "1.7-4.5", "38.4", "8.2-9.2", "89.3", "0.5", "3.9", "4.4", "6.5", "0.8", "1.4", "2.0", "2.1", "31.7"],
                        },
                    ],
                }
            ]
        }

        features = season_stats._parse_espn_common_v3_payload(payload, "2025-26")
        self.assertIsNotNone(features)
        self.assertEqual(features["season_mpg"], 33.4)
        self.assertEqual(features["season_fga"], 19.8)
        self.assertEqual(features["season_3pa"], 4.5)
        self.assertEqual(features["season_rebounds"], 4.4)
        self.assertEqual(features["season_assists"], 6.5)
        self.assertEqual(features["season_ppg"], 31.7)

    @patch("services.live_props.season_stats._fetch_espn_season_features", return_value=None)
    @patch("services.live_props.season_stats._load_nba_season_table")
    def test_nba_fallback_by_name_team(self, mock_load_nba, _mock_espn) -> None:
        mock_load_nba.return_value = {
            "by_name_team": {("lebron james", "LAL"): 2544},
            "by_id": {
                2544: {
                    "season_ppg": 24.7,
                    "season_fga": 18.9,
                    "season_mpg": 34.6,
                    "season_3pa": 5.8,
                    "season_rebounds": 7.7,
                    "season_assists": 8.1,
                }
            },
        }

        features = season_stats.get_player_season_features(
            espn_player_id="1966",
            season_key="2025-26",
            player_name="LeBron James",
            team_abbr="LAL",
        )

        self.assertEqual(features["season_ppg"], 24.7)
        self.assertEqual(season_stats._espn_to_nba_id_cache.get("1966"), 2544)

    @patch("services.live_props.season_stats._fetch_espn_season_features")
    def test_daily_cache_hit(self, mock_fetch_espn) -> None:
        mock_fetch_espn.return_value = {
            "season_ppg": 20.0,
            "season_fga": 15.0,
            "season_mpg": 31.0,
            "season_3pa": 5.0,
            "season_rebounds": 6.0,
            "season_assists": 4.0,
        }

        first = season_stats.get_player_season_features("123", "2025-26")
        self.assertEqual(first["season_ppg"], 20.0)
        self.assertEqual(mock_fetch_espn.call_count, 1)

        second = season_stats.get_player_season_features("123", "2025-26")
        self.assertEqual(second["season_ppg"], 20.0)
        self.assertEqual(mock_fetch_espn.call_count, 1)

    @patch("services.live_props.season_stats._fetch_espn_season_features", return_value=None)
    @patch("services.live_props.season_stats._load_nba_season_table", return_value={"by_name_team": {}, "by_id": {}})
    def test_zero_fallback(self, _mock_load_nba, _mock_espn) -> None:
        features = season_stats.get_player_season_features("999", "2025-26")
        self.assertEqual(features, season_stats.zero_feature_set())

    @patch(
        "services.live_props.season_stats._fetch_espn_season_features",
        return_value={
            "season_ppg": 19.2,
            "season_fga": 0.0,
            "season_mpg": 0.0,
            "season_3pa": 0.0,
            "season_rebounds": 0.0,
            "season_assists": 0.0,
        },
    )
    @patch("services.live_props.season_stats._load_nba_season_table")
    def test_partial_espn_backfills_from_nba(self, mock_load_nba, _mock_espn) -> None:
        mock_load_nba.return_value = {
            "by_name_team": {("julius randle", "MIN"): 203944},
            "by_id": {
                203944: {
                    "season_ppg": 18.9,
                    "season_fga": 15.7,
                    "season_mpg": 33.8,
                    "season_3pa": 5.4,
                    "season_rebounds": 8.2,
                    "season_assists": 4.9,
                }
            },
            "by_team_top_mpg": {},
        }

        features = season_stats.get_player_season_features(
            espn_player_id="3064514",
            season_key="2025-26",
            player_name="Julius Randle",
            team_abbr="MIN",
        )

        self.assertEqual(features["season_ppg"], 19.2)
        self.assertEqual(features["season_fga"], 15.7)
        self.assertEqual(features["season_mpg"], 33.8)
        self.assertEqual(features["season_3pa"], 5.4)
        self.assertEqual(features["season_rebounds"], 8.2)
        self.assertEqual(features["season_assists"], 4.9)

    @patch("services.live_props.season_stats._load_nba_season_table")
    def test_get_team_top_mpg_players(self, mock_load_nba) -> None:
        mock_load_nba.return_value = {
            "by_id": {},
            "by_name_team": {},
            "by_team_top_mpg": {
                "LAL": [
                    {"player_id": 1, "player_name": "A", "team_abbr": "LAL", "season_mpg": 35.0},
                    {"player_id": 2, "player_name": "B", "team_abbr": "LAL", "season_mpg": 33.0},
                    {"player_id": 3, "player_name": "C", "team_abbr": "LAL", "season_mpg": 31.0},
                ]
            },
        }

        top_two = season_stats.get_team_top_mpg_players("2025-26", "LAL", limit=2)
        self.assertEqual(len(top_two), 2)
        self.assertEqual(top_two[0]["player_id"], 1)
        self.assertEqual(top_two[1]["player_id"], 2)


if __name__ == "__main__":
    unittest.main()
