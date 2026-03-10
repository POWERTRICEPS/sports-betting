from __future__ import annotations

import os
import sys
import unittest
from unittest.mock import patch

ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import database


class _FakeCursor:
    def __init__(self, seed_last_row: dict | None = None) -> None:
        self._seed_last_row = seed_last_row
        self.last_row = seed_last_row
        self.inserted: list[tuple] = []
        self._fetchone_result: dict | None = None

    def execute(self, query: str, params=None) -> None:
        normalized = " ".join(query.strip().split()).lower()
        if normalized.startswith("select") and "from game_probability_history" in normalized:
            self._fetchone_result = self.last_row
            return

        if normalized.startswith("insert into game_probability_history"):
            self.inserted.append(params)
            self.last_row = {
                "clock_display": params[1],
                "home_team_score": params[2],
                "away_team_score": params[3],
                "home_win_probability": params[4],
                "away_win_probability": params[5],
            }
            return

        raise AssertionError(f"Unexpected query executed: {query}")

    def fetchone(self):
        return self._fetchone_result

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _FakeConnection:
    def __init__(self, cursor: _FakeCursor) -> None:
        self._cursor = cursor

    def cursor(self):
        return self._cursor

    def commit(self) -> None:
        return None

    def rollback(self) -> None:
        return None

    def close(self) -> None:
        return None


class _FakeDBContext:
    def __init__(self, connection: _FakeConnection) -> None:
        self._connection = connection

    def __enter__(self):
        return self._connection

    def __exit__(self, exc_type, exc, tb):
        return False


class ProbabilityHistoryAppendTest(unittest.TestCase):
    def test_append_inserts_new_snapshots_in_order(self) -> None:
        cursor = _FakeCursor()
        fake_db = _FakeDBContext(_FakeConnection(cursor))
        snapshots = [
            {
                "clock": "7:07 - 3rd",
                "home_score": 80,
                "away_score": 76,
                "home_win_prob": 62.3,
                "away_win_prob": 37.7,
            },
            {
                "clock": "3:14 - 4th",
                "home_score": 101,
                "away_score": 95,
                "home_win_prob": 88.5,
                "away_win_prob": 11.5,
            },
        ]

        with patch.object(database, "get_db", return_value=fake_db):
            inserted = database._append_probability_history_sync("401234567", snapshots)

        self.assertEqual(inserted, 2)
        self.assertEqual(len(cursor.inserted), 2)
        self.assertEqual(cursor.inserted[0][1], "7:07 - 3rd")
        self.assertEqual(cursor.inserted[1][1], "3:14 - 4th")

    def test_append_skips_duplicate_tail_and_inserts_remaining(self) -> None:
        seed_last = {
            "clock_display": "7:07 - 3rd",
            "home_team_score": 80,
            "away_team_score": 76,
            "home_win_probability": 62.3,
            "away_win_probability": 37.7,
        }
        cursor = _FakeCursor(seed_last_row=seed_last)
        fake_db = _FakeDBContext(_FakeConnection(cursor))
        snapshots = [
            {
                "clock": "7:07 - 3rd",
                "home_score": 80,
                "away_score": 76,
                "home_win_prob": 62.3,
                "away_win_prob": 37.7,
            },
            {
                "clock": "3:14 - 4th",
                "home_score": 101,
                "away_score": 95,
                "home_win_prob": 88.5,
                "away_win_prob": 11.5,
            },
        ]

        with patch.object(database, "get_db", return_value=fake_db):
            inserted = database._append_probability_history_sync("401234567", snapshots)

        self.assertEqual(inserted, 1)
        self.assertEqual(len(cursor.inserted), 1)
        self.assertEqual(cursor.inserted[0][1], "3:14 - 4th")


if __name__ == "__main__":
    unittest.main()
