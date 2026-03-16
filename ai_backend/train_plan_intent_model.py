from __future__ import annotations

import argparse
import csv
import json
import pickle
from pathlib import Path
from typing import Any

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from dataset_paths import resolve_dataset_root


DEFAULT_DATASET_ROOT = resolve_dataset_root()
DEFAULT_WEEK2_DIR = Path(__file__).resolve().parent / "data" / "week2"
DEFAULT_MODEL_OUTPUT = Path(__file__).resolve().parent / "model_plan_intent.pkl"


WORKOUT_TAG_HINTS = {"ask_exercise", "ask_muscle", "ask_home_workout", "ask_gym_workout"}
NUTRITION_TAG_HINTS = {"ask_weight_loss", "ask_nutrition", "ask_meal_plan", "ask_diet"}


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _dataset_text(value: Any) -> str:
    if isinstance(value, dict):
        en = str(value.get("en", "")).strip()
        ar = str(value.get("ar", "")).strip()
        return " ".join([v for v in (en, ar) if v]).strip()
    return str(value or "").strip()


def _load_week2_training_pairs(week2_dir: Path) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []

    intents_path = week2_dir / "conversation_intents.json"
    workout_path = week2_dir / "workout_programs.json"
    nutrition_path = week2_dir / "nutrition_programs.json"

    if intents_path.exists():
        intents_payload = _read_json(intents_path)
        intents = intents_payload.get("intents", []) if isinstance(intents_payload, dict) else []
        for item in intents:
            if not isinstance(item, dict):
                continue
            tag = str(item.get("tag", "")).strip().lower()
            label = None
            if tag in WORKOUT_TAG_HINTS:
                label = "workout"
            elif tag in NUTRITION_TAG_HINTS:
                label = "nutrition"
            if not label:
                continue
            patterns = item.get("patterns", [])
            if isinstance(patterns, list):
                for p in patterns:
                    text = _dataset_text(p)
                    if text:
                        pairs.append((text, label))

    if workout_path.exists():
        programs = _read_json(workout_path)
        if isinstance(programs, list):
            for p in programs:
                if not isinstance(p, dict):
                    continue
                texts = [
                    _dataset_text(p.get("name")),
                    _dataset_text(p.get("description")),
                    _dataset_text(p.get("goal")),
                    _dataset_text(p.get("level")),
                ]
                for t in texts:
                    if t:
                        pairs.append((t, "workout"))
                for d in p.get("days", []) if isinstance(p.get("days"), list) else []:
                    if not isinstance(d, dict):
                        continue
                    pairs.append((_dataset_text(d.get("focus")), "workout"))
                    for ex in d.get("exercises", []) if isinstance(d.get("exercises"), list) else []:
                        if not isinstance(ex, dict):
                            continue
                        ex_name = _dataset_text(ex.get("name"))
                        if ex_name:
                            pairs.append((ex_name, "workout"))

    if nutrition_path.exists():
        programs = _read_json(nutrition_path)
        if isinstance(programs, list):
            for p in programs:
                if not isinstance(p, dict):
                    continue
                texts = [
                    _dataset_text(p.get("description")),
                    _dataset_text(p.get("goal")),
                ]
                for t in texts:
                    if t:
                        pairs.append((t, "nutrition"))
                for tip in p.get("tips", []) if isinstance(p.get("tips"), list) else []:
                    tip_text = _dataset_text(tip)
                    if tip_text:
                        pairs.append((tip_text, "nutrition"))
                for meal in p.get("sample_meals", []) if isinstance(p.get("sample_meals"), list) else []:
                    if not isinstance(meal, dict):
                        continue
                    meal_text = " ".join(
                        [v for v in (_dataset_text(meal.get("meal_type")), _dataset_text(meal.get("description"))) if v]
                    ).strip()
                    if meal_text:
                        pairs.append((meal_text, "nutrition"))

    return pairs


def _load_external_training_pairs(dataset_root: Path, nutrition_sample_size: int = 15000) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []

    workout_csv = dataset_root / "Exercise Muscle Mapping" / "Workout.csv"
    if workout_csv.exists():
        df = pd.read_csv(workout_csv)
        if "Workout" in df.columns:
            for val in df["Workout"].dropna().astype(str).tolist():
                text = val.strip()
                if text:
                    pairs.append((text, "workout"))

    nutrition_csv = dataset_root / "Nutrition Dataset" / "nutrition.csv"
    if nutrition_csv.exists():
        df = pd.read_csv(nutrition_csv)
        if "name" in df.columns:
            series = df["name"].dropna().astype(str)
            if len(series) > nutrition_sample_size:
                series = series.sample(nutrition_sample_size, random_state=42)
            for val in series.tolist():
                text = val.strip()
                if text:
                    pairs.append((text, "nutrition"))

    return pairs


def _file_level_label(path: Path) -> str:
    name = str(path).lower()
    if any(k in name for k in ("nutrition", "food", "meal", "calorie", "macro", "diet")):
        return "nutrition"
    if any(k in name for k in ("workout", "exercise", "muscle", "gym", "body", "progress", "attendance", "plan")):
        return "workout"
    return "workout"


def _read_csv_header(path: Path) -> list[str]:
    try:
        with path.open("r", encoding="utf-8", errors="ignore", newline="") as f:
            reader = csv.reader(f)
            header = next(reader, [])
            return [str(h).strip() for h in header if str(h).strip()]
    except Exception:
        return []


def _load_all_files_metadata_pairs(dataset_root: Path) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for file_path in dataset_root.rglob("*"):
        if not file_path.is_file():
            continue
        label = _file_level_label(file_path)
        rel = str(file_path.relative_to(dataset_root))
        stem = file_path.stem.replace("_", " ").replace("-", " ")
        ext = file_path.suffix.lower().replace(".", "")
        base_text = f"{rel} {stem} {ext}".strip()
        if base_text:
            pairs.append((base_text, label))

        if file_path.suffix.lower() == ".csv":
            header = _read_csv_header(file_path)
            if header:
                pairs.append((" ".join(header[:40]), label))
    return pairs


def _synthetic_pairs() -> list[tuple[str, str]]:
    workout_templates = [
        "workout plan",
        "training plan",
        "gym plan",
        "home workout plan",
        "برنامج تمارين",
        "خطة تمارين",
        "جدول تدريب",
        "خطة جيم",
        "تمارين للصدر",
        "تمارين للظهر",
    ]
    nutrition_templates = [
        "nutrition plan",
        "diet plan",
        "meal plan",
        "calorie plan",
        "خطة تغذية",
        "خطة غذائية",
        "جدول وجبات",
        "دايت",
        "وجبات للتنشيف",
        "اكل لزيادة الوزن",
    ]
    pairs = [(t, "workout") for t in workout_templates]
    pairs += [(t, "nutrition") for t in nutrition_templates]
    return pairs


def build_training_dataset(dataset_root: Path, week2_dir: Path) -> pd.DataFrame:
    pairs = []
    pairs.extend(_load_week2_training_pairs(week2_dir))
    pairs.extend(_load_external_training_pairs(dataset_root))
    pairs.extend(_load_all_files_metadata_pairs(dataset_root))
    pairs.extend(_synthetic_pairs())

    if not pairs:
        raise ValueError("No training pairs found for plan-intent model.")

    df = pd.DataFrame(pairs, columns=["text", "label"])
    df["text"] = df["text"].astype(str).str.strip()
    df = df[df["text"] != ""]
    df = df.drop_duplicates()
    return df


def train_and_save_plan_intent_model(dataset_root: Path, week2_dir: Path, output_path: Path) -> dict[str, Any]:
    df = build_training_dataset(dataset_root, week2_dir)
    X = df["text"]
    y = df["label"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    pipeline = Pipeline(
        steps=[
            ("tfidf", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=2)),
            ("model", LogisticRegression(max_iter=2000, class_weight="balanced")),
        ]
    )
    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)

    artifact = {
        "model": pipeline,
        "model_name": "tfidf_logistic_regression",
        "metrics": {
            "accuracy": float(accuracy_score(y_test, y_pred)),
            "weighted_f1": float(f1_score(y_test, y_pred, average="weighted")),
        },
        "dataset_rows": int(len(df)),
        "labels": sorted(set(y.tolist())),
        "dataset_root": str(dataset_root),
        "week2_dir": str(week2_dir),
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("wb") as f:
        pickle.dump(artifact, f)
    return artifact


def main() -> None:
    parser = argparse.ArgumentParser(description="Train plan intent model (workout vs nutrition).")
    parser.add_argument("--dataset-root", type=Path, default=DEFAULT_DATASET_ROOT)
    parser.add_argument("--week2-dir", type=Path, default=DEFAULT_WEEK2_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_MODEL_OUTPUT)
    args = parser.parse_args()

    artifact = train_and_save_plan_intent_model(args.dataset_root, args.week2_dir, args.output)
    print("Plan-intent model trained successfully")
    print(f"Model: {artifact['model_name']}")
    print(f"Rows: {artifact['dataset_rows']}")
    print(f"Labels: {artifact['labels']}")
    print(f"Accuracy: {artifact['metrics']['accuracy']:.4f}")
    print(f"Weighted F1: {artifact['metrics']['weighted_f1']:.4f}")
    print(f"Saved: {args.output}")


if __name__ == "__main__":
    main()
