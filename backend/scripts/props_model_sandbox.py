#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd

MODEL_DIR = Path(__file__).resolve().parents[1] / "pred_models"

MODEL_FILES = {
    "pts": "pts_model.joblib",
    "reb": "reb_model.joblib",
    "ast": "ast_model.joblib",
}

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

SAMPLE = {
    "seconds_remaining": 1566,
    "current_points": 10,
    "current_rebounds": 1,
    "current_assists": 5,
    "current_minutes": 17,
    "season_ppg": 12.6,
    "season_fga": 10.1,
    "season_mpg": 27.6,
    "fga_so_far": 10,
    "3pa_so_far": 7,
    "season_3pa": 4.7,
    "season_rebounds": 5.2,
    "season_assists": 3.7,
    "score_differential": -14,
}


def parse_kv_pairs(pairs: list[str]) -> dict[str, float]:
    out: dict[str, float] = {}
    for pair in pairs:
        if "=" not in pair:
            raise ValueError(f"Invalid --set '{pair}'. Use key=value.")
        key, value = pair.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError(f"Invalid key in --set '{pair}'.")
        try:
            out[key] = float(value)
        except ValueError as e:
            raise ValueError(f"Invalid numeric value in --set '{pair}'.") from e
    return out


def load_model(stat: str) -> Any:
    path = MODEL_DIR / MODEL_FILES[stat]
    if not path.is_file():
        raise FileNotFoundError(f"Model not found: {path}")

    import joblib

    return joblib.load(path)


def predict(model: Any, features: dict[str, float], stat: str) -> float:
    cols = FEATURE_COLUMNS[stat]
    row = [float(features.get(c, 0.0)) for c in cols]
    x = pd.DataFrame([row], columns=cols)
    raw = float(model.predict(x)[0])
    return raw


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Standalone sandbox for PTS/REB/AST model inference.",
    )
    p.add_argument(
        "--stat",
        choices=["pts", "reb", "ast", "all"],
        default="all",
        help="Which model to run (default: all).",
    )
    p.add_argument(
        "--set",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Override feature values. Can be repeated.",
    )
    p.add_argument(
        "--zeros",
        action="store_true",
        help="Start from all-zero features instead of sample values.",
    )
    p.add_argument(
        "--show-features",
        action="store_true",
        help="Print the final feature vector used per model.",
    )
    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    overrides = parse_kv_pairs(args.set)
    base = {k: 0.0 for k in SAMPLE.keys()} if args.zeros else dict(SAMPLE)
    base.update(overrides)

    stats = ["pts", "reb", "ast"] if args.stat == "all" else [args.stat]

    print("Model sandbox input base:")
    print(base)
    print()

    for stat in stats:
        model = load_model(stat)
        pred = predict(model, base, stat)
        print(f"{stat.upper()} remaining prediction: {pred:.4f}")
        if args.show_features:
            print({k: base.get(k, 0.0) for k in FEATURE_COLUMNS[stat]})
            print()


if __name__ == "__main__":
    main()
