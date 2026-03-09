from __future__ import annotations

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from services.live_props import model_runner


class LivePropsModelRunnerTest(unittest.TestCase):
    def setUp(self) -> None:
        model_runner._loaded_models.clear()
        model_runner._load_attempted.clear()

    def test_sanitize_prediction_bounds(self) -> None:
        self.assertEqual(model_runner.sanitize_prediction(-2), 0.0)
        self.assertEqual(model_runner.sanitize_prediction(12.3456), 12.35)
        self.assertEqual(model_runner.sanitize_prediction(101), 100.0)
        self.assertEqual(model_runner.sanitize_prediction("bad"), 0.0)

    def test_predict_remaining_returns_float(self) -> None:
        # With missing model files or failed loads this should safely return 0.0.
        features = {key: 0.0 for key in model_runner.FEATURE_COLUMNS["pts"]}
        pred = model_runner.predict_remaining("pts", features)
        self.assertIsInstance(pred, float)
        self.assertGreaterEqual(pred, 0.0)


if __name__ == "__main__":
    unittest.main()
