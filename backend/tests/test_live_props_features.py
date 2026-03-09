from __future__ import annotations

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from services.live_props.features import build_player_feature_context, build_stat_features, parse_minutes


class LivePropsFeaturesTest(unittest.TestCase):
    def test_parse_minutes_mm_ss(self) -> None:
        self.assertAlmostEqual(parse_minutes("12:30"), 12.5)

    def test_parse_minutes_fallback(self) -> None:
        self.assertEqual(parse_minutes(None), 0.0)
        self.assertEqual(parse_minutes(""), 0.0)

    def test_build_player_feature_context(self) -> None:
        player = {
            "minutes": "18:30",
            "stats": ["", "", "", "", "", "", "8", "5", "", "6-11", "", "", "2-5", "17"],
        }
        game = {
            "status": "4:00 - 2nd",
            "home_score": 62,
            "away_score": 58,
            "is_home": True,
        }

        base = build_player_feature_context(player, game)

        self.assertEqual(base["current_points"], 17.0)
        self.assertEqual(base["current_rebounds"], 8.0)
        self.assertEqual(base["current_assists"], 5.0)
        self.assertEqual(base["fga_so_far"], 11.0)
        self.assertEqual(base["3pa_so_far"], 5.0)
        self.assertAlmostEqual(base["current_minutes"], 18.5)
        self.assertEqual(base["score_differential"], 4.0)

    def test_build_stat_features_column_subset(self) -> None:
        base = {
            "seconds_remaining": 300.0,
            "current_points": 12.0,
            "current_minutes": 20.0,
            "season_ppg": 0.0,
            "season_fga": 0.0,
            "season_mpg": 0.0,
            "fga_so_far": 9.0,
            "3pa_so_far": 3.0,
            "season_3pa": 0.0,
            "score_differential": -2.0,
            "current_rebounds": 6.0,
            "season_rebounds": 0.0,
            "current_assists": 4.0,
            "season_assists": 0.0,
        }

        pts = build_stat_features("pts", base)
        reb = build_stat_features("reb", base)
        ast = build_stat_features("ast", base)

        self.assertEqual(len(pts), 10)
        self.assertEqual(len(reb), 6)
        self.assertEqual(len(ast), 6)
        self.assertIn("current_points", pts)
        self.assertIn("current_rebounds", reb)
        self.assertIn("current_assists", ast)

    def test_build_player_feature_context_prefers_label_stats(self) -> None:
        player = {
            "minutes": "0",
            # Intentionally misleading indexes so we can prove label-driven parsing.
            "stats": ["0"] * 14,
            "label_stats": {
                "MIN": "35",
                "PTS": "34",
                "REB": "6",
                "AST": "8",
                "FG": "12-21",
                "3PT": "4-9",
            },
        }
        game = {
            "status": "Final",
            "home_score": 110,
            "away_score": 102,
            "is_home": True,
        }

        base = build_player_feature_context(player, game)
        self.assertEqual(base["current_points"], 34.0)
        self.assertEqual(base["current_rebounds"], 6.0)
        self.assertEqual(base["current_assists"], 8.0)
        self.assertEqual(base["fga_so_far"], 21.0)
        self.assertEqual(base["3pa_so_far"], 9.0)
        self.assertEqual(base["current_minutes"], 35.0)

    def test_build_player_feature_context_with_season_features(self) -> None:
        player = {
            "minutes": "12:00",
            "stats": ["", "", "", "", "", "", "4", "3", "", "2-5", "", "", "1-3", "10"],
        }
        game = {
            "status": "7:00 - 3rd",
            "home_score": 70,
            "away_score": 64,
            "is_home": True,
        }
        season = {
            "season_ppg": 25.2,
            "season_fga": 18.1,
            "season_mpg": 34.0,
            "season_3pa": 7.3,
            "season_rebounds": 8.8,
            "season_assists": 6.4,
        }

        base = build_player_feature_context(player, game, season_features=season)
        self.assertEqual(base["season_ppg"], 25.2)
        self.assertEqual(base["season_fga"], 18.1)
        self.assertEqual(base["season_mpg"], 34.0)
        self.assertEqual(base["season_3pa"], 7.3)
        self.assertEqual(base["season_rebounds"], 8.8)
        self.assertEqual(base["season_assists"], 6.4)


if __name__ == "__main__":
    unittest.main()
