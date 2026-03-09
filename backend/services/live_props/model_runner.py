from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

MODEL_DIR = Path(__file__).resolve().parents[2] / "pred_models"

_MODEL_FILES = {
    "pts": "pts_model.joblib",
    "reb": "reb_model.joblib",
    "ast": "ast_model.joblib",
}

# These are based on the current model training notebooks.
FEATURE_COLUMNS = {
    "pts": [
        "seconds_remaining",
        "current_points",
        "current_minutes",
        "season_ppg",
        "season_fga",
        "season_mpg",
        "fga_so_far",
        "3pa_so_far",
        "season_3pa",
        "score_differential",
    ],
    "reb": [
        "seconds_remaining",
        "current_minutes",
        "season_mpg",
        "current_rebounds",
        "season_rebounds",
        "score_differential",
    ],
    "ast": [
        "seconds_remaining",
        "current_minutes",
        "season_mpg",
        "current_assists",
        "season_assists",
        "score_differential",
    ],
}

_loaded_models: dict[str, Any | None] = {}
_load_attempted: set[str] = set()
_schema_validated: set[str] = set()


def _expected_feature_count(stat: str) -> int:
    return len(FEATURE_COLUMNS[stat])


def _model_feature_count(model: Any) -> int | None:
    try:
        if hasattr(model, "n_features_in_"):
            return int(model.n_features_in_)
    except Exception:
        pass
    try:
        if hasattr(model, "get_booster"):
            booster = model.get_booster()
            return int(booster.num_features())
    except Exception:
        pass
    return None


def _validate_model_schema(stat: str, model: Any) -> None:
    if stat in _schema_validated:
        return
    _schema_validated.add(stat)
    expected = _expected_feature_count(stat)
    actual = _model_feature_count(model)
    if actual is not None and actual != expected:
        print(
            f"[live_props] feature schema mismatch stat={stat}: "
            f"model expects {actual}, code provides {expected}. "
            f"Check FEATURE_COLUMNS order/shape."
        )


def _load_model(stat: str) -> Any | None:
    if stat in _loaded_models:
        return _loaded_models[stat]
    if stat in _load_attempted:
        return None

    _load_attempted.add(stat)
    filename = _MODEL_FILES[stat]
    path = MODEL_DIR / filename
    if not path.is_file():
        print(f"[live_props] model not found: {path}")
        _loaded_models[stat] = None
        return None

    try:
        import joblib

        model = joblib.load(path)
        _validate_model_schema(stat, model)
        _loaded_models[stat] = model
        return model
    except Exception as e:
        print(f"[live_props] failed to load model {path}: {e}")
        _loaded_models[stat] = None
        return None


def sanitize_prediction(value: Any) -> float:
    try:
        pred = float(value)
    except (TypeError, ValueError):
        return 0.0
    if pred < 0:
        return 0.0
    if pred > 100:
        return 100.0
    return round(pred, 2)


def predict_remaining(stat: str, features: dict[str, float]) -> float:
    model = _load_model(stat)
    if model is None:
        return 0.0

    cols = FEATURE_COLUMNS[stat]
    row = [float(features.get(col, 0.0) or 0.0) for col in cols]
    x = pd.DataFrame([row], columns=cols)

    try:
        raw = model.predict(x)[0]
    except Exception as e:
        print(f"[live_props] prediction failed for stat={stat}: {e}")
        return 0.0

    return sanitize_prediction(raw)
