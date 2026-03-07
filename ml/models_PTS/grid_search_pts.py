#!/usr/bin/env python3
"""
Grid search over XGBRegressor hyperparameters for the PTS model.
Runs eval_model (MAE, RMSE, R²) on all hyperparameter combinations.
"""

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor
from itertools import product
import json
from pathlib import Path


def load_and_prepare_data(csv_path: str) -> tuple:
    """Load and preprocess data to match the notebook."""
    pbp_df = pd.read_csv(csv_path)
    pbp_df["points_remaining"] = pbp_df["final_points"] - pbp_df["current_points"]
    pbp_df = pbp_df.drop(
        columns=[
            "game_id",
            "player_id",
            "season",
            "current_rebounds",
            "season_rebounds",
            "current_assists",
            "season_assists",
            "final_rebounds",
            "final_assists",
            "final_points",
        ]
    )
    pbp_df = pbp_df.drop_duplicates()

    feature_cols = [
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
    ]
    X = pbp_df[feature_cols]
    y = pbp_df["points_remaining"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42
    )
    X_tr, X_val, y_tr, y_val = train_test_split(
        X_train, y_train, test_size=0.2, random_state=42
    )
    return X_tr, X_val, X_test, y_tr, y_val, y_test


def eval_model(model, X_test, y_test: pd.Series) -> dict:
    """Compute MAE, RMSE, R² for a fitted model. Returns dict of metrics."""
    y_pred = model.predict(X_test)
    return {
        "mae": mean_absolute_error(y_test, y_pred),
        "rmse": mean_squared_error(y_test, y_pred),
        "r2": r2_score(y_test, y_pred),
    }


def main():
    script_dir = Path(__file__).resolve().parent
    csv_path = script_dir.parent / "datasets" / "props_training.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"Dataset not found: {csv_path}")

    X_tr, X_val, X_test, y_tr, y_val, y_test = load_and_prepare_data(csv_path)

    param_grid = {
        "n_estimators": [100, 300, 500],
        "max_depth": [3, 5, 7],
        "learning_rate": [0.01, 0.05, 0.1],
        "subsample": [0.7, 0.8, 0.9],
        "colsample_bytree": [0.7, 0.8, 0.9],
    }

    keys = list(param_grid.keys())
    values = list(param_grid.values())
    combinations = list(product(*values))
    n_combos = len(combinations)
    print(f"Grid search: {n_combos} combinations")
    print("=" * 80)

    results = []
    best_r2 = float("-inf")
    best_params = None
    best_model = None

    for i, combo in enumerate(combinations):
        params = dict(zip(keys, combo))
        model = XGBRegressor(
            objective="reg:squarederror",
            random_state=42,
            **params,
        )
        model.fit(
            X_tr,
            y_tr,
            eval_set=[(X_val, y_val)],
            verbose=False,
        )
        metrics = eval_model(model, X_test, y_test)
        metrics["params"] = params
        results.append(metrics)

        if metrics["r2"] > best_r2:
            best_r2 = metrics["r2"]
            best_params = params
            best_model = model

        print(
            f"[{i + 1}/{n_combos}] "
            f"MAE={metrics['mae']:.2f} RMSE={metrics['rmse']:.2f} R²={metrics['r2']:.3f} "
            f"| {params}"
        )

    print("=" * 80)
    print("BEST (by R²):")
    print(f"  MAE:  {eval_model(best_model, X_test, y_test)['mae']:.2f}")
    print(f"  RMSE: {eval_model(best_model, X_test, y_test)['rmse']:.2f}")
    print(f"  R²:   {best_r2:.3f}")
    print(f"  Params: {best_params}")

if __name__ == "__main__":
    main()
