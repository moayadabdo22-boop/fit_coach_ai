from __future__ import annotations

import argparse
import pickle
from pathlib import Path
from typing import Any

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from dataset_paths import resolve_dataset_root
from preprocess import GOAL_FEATURE_COLUMNS, GOAL_TARGET_COLUMN, make_goal_preprocessor, prepare_goal_training_data


DEFAULT_GOAL_DATASET = resolve_dataset_root()
DEFAULT_MODEL_OUTPUT = Path(__file__).resolve().parent / "model_goal.pkl"


def _build_candidates(random_state: int = 42) -> dict[str, Any]:
    preprocessor = make_goal_preprocessor()
    return {
        "random_forest": Pipeline(
            steps=[
                ("preprocess", preprocessor),
                (
                    "model",
                    RandomForestClassifier(
                        n_estimators=120,
                        random_state=random_state,
                        class_weight="balanced_subsample",
                        n_jobs=-1,
                    ),
                ),
            ]
        ),
        "logistic_regression": Pipeline(
            steps=[
                ("preprocess", preprocessor),
                ("model", LogisticRegression(max_iter=2000, class_weight="balanced")),
            ]
        ),
    }


def train_and_save_goal_model(dataset_path: Path, output_path: Path) -> dict[str, Any]:
    df = prepare_goal_training_data(dataset_path)
    source_files = [str(v) for v in df.attrs.get("source_files", [])]
    X = df[GOAL_FEATURE_COLUMNS]
    y = df[GOAL_TARGET_COLUMN]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    candidates = _build_candidates()
    best_name = ""
    best_model = None
    best_f1 = -1.0
    best_accuracy = 0.0

    for name, pipeline in candidates.items():
        pipeline.fit(X_train, y_train)
        y_pred = pipeline.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred, average="weighted")
        if f1 > best_f1:
            best_name = name
            best_model = pipeline
            best_f1 = f1
            best_accuracy = accuracy

    artifact = {
        "model": best_model,
        "model_name": best_name,
        "feature_columns": GOAL_FEATURE_COLUMNS,
        "target_column": GOAL_TARGET_COLUMN,
        "metrics": {"accuracy": float(best_accuracy), "weighted_f1": float(best_f1)},
        "dataset_path": str(dataset_path),
        "dataset_rows": int(len(df)),
        "source_files": source_files,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("wb") as f:
        pickle.dump(artifact, f)
    return artifact


def main() -> None:
    parser = argparse.ArgumentParser(description="Train and save goal prediction model.")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_GOAL_DATASET)
    parser.add_argument("--output", type=Path, default=DEFAULT_MODEL_OUTPUT)
    args = parser.parse_args()

    artifact = train_and_save_goal_model(args.dataset, args.output)
    print("Goal model trained successfully")
    print(f"Model: {artifact['model_name']}")
    print(f"Rows: {artifact['dataset_rows']}")
    print(f"Source files: {len(artifact.get('source_files', []))}")
    print(f"Accuracy: {artifact['metrics']['accuracy']:.4f}")
    print(f"Weighted F1: {artifact['metrics']['weighted_f1']:.4f}")
    print(f"Saved: {args.output}")


if __name__ == "__main__":
    main()
