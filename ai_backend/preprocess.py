from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler


GOAL_FEATURE_COLUMNS = [
    "age",
    "gender",
    "weight_kg",
    "height_m",
    "bmi",
    "fat_percentage",
    "workout_frequency_days_week",
    "experience_level",
    "calories_burned",
    "avg_bpm",
]
GOAL_TARGET_COLUMN = "goal_label"

SUCCESS_FEATURE_COLUMNS = [
    "age",
    "gender",
    "membership_type",
    "workout_type",
    "workout_duration_minutes",
    "calories_burned",
    "check_in_hour",
]
SUCCESS_TARGET_COLUMN = "success_label"


GOAL_HEADER_SIGNATURES = [
    {"age", "gender", "weight (kg)", "height (m)"},
    {"age", "gender", "actual weight", "bmi"},
    {"age", "gender", "height_cm", "weight_kg"},
    {"bodyfat", "age", "weight", "height"},
]

SUCCESS_HEADER_SIGNATURES = [
    {
        "age",
        "gender",
        "membership_type",
        "workout_type",
        "workout_duration_minutes",
        "calories_burned",
        "check_in_time",
        "attendance_status",
    }
]


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _normalize_gender(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text in {"m", "male", "man", "1"}:
        return "Male"
    if text in {"f", "female", "woman", "0"}:
        return "Female"
    return "Other"


def _read_header(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8", errors="ignore", newline="") as f:
        reader = csv.reader(f)
        return [str(h).strip().lower() for h in next(reader, [])]


def _has_any_signature(header: set[str], signatures: list[set[str]]) -> bool:
    return any(sig.issubset(header) for sig in signatures)


def _iter_candidate_csv_files(source: Path, signatures: list[set[str]]) -> list[Path]:
    if source.is_file():
        return [source]

    paths: list[Path] = []
    for file_path in source.rglob("*.csv"):
        try:
            header = set(_read_header(file_path))
        except Exception:
            continue
        if _has_any_signature(header, signatures):
            paths.append(file_path)
    return sorted(paths)


def _derive_goal_label(row: pd.Series) -> str:
    """
    Heuristic goal label:
    - fat_loss: higher BMI/fat%
    - muscle_gain: lean + higher training frequency
    - general_fitness: otherwise
    """
    bmi = _safe_float(row.get("bmi"), 0.0)
    fat_pct = _safe_float(row.get("fat_percentage"), 0.0)
    frequency = _safe_float(row.get("workout_frequency_days_week"), 0.0)

    if bmi >= 27 or fat_pct >= 27:
        return "fat_loss"
    if frequency >= 4 and bmi < 25 and fat_pct < 24:
        return "muscle_gain"
    return "general_fitness"


def _to_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def _intensity_to_experience(series: pd.Series) -> pd.Series:
    text = series.astype(str).str.strip().str.lower()
    mapped = text.map({"low": 1.0, "medium": 2.0, "high": 3.0})
    numeric = pd.to_numeric(series, errors="coerce")
    return mapped.fillna(numeric)


def _map_goal_from_gym_schema(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "age": df.get("Age"),
            "gender": df.get("Gender"),
            "weight_kg": df.get("Weight (kg)"),
            "height_m": df.get("Height (m)"),
            "bmi": df.get("BMI"),
            "fat_percentage": df.get("Fat_Percentage"),
            "workout_frequency_days_week": df.get("Workout_Frequency (days/week)"),
            "experience_level": df.get("Experience_Level"),
            "calories_burned": df.get("Calories_Burned"),
            "avg_bpm": df.get("Avg_BPM"),
        }
    )


def _map_goal_from_exercise_dataset(df: pd.DataFrame) -> pd.DataFrame:
    frame = pd.DataFrame(
        {
            "age": df.get("Age"),
            "gender": df.get("Gender"),
            "weight_kg": df.get("Actual Weight"),
            "height_m": pd.NA,
            "bmi": df.get("BMI"),
            "fat_percentage": pd.NA,
            "workout_frequency_days_week": pd.NA,
            "experience_level": _intensity_to_experience(df.get("Exercise Intensity", pd.Series(dtype="object"))),
            "calories_burned": df.get("Calories Burn"),
            "avg_bpm": df.get("Heart Rate"),
        }
    )
    duration = _to_numeric(df.get("Duration", pd.Series(dtype="float")))
    frame["workout_frequency_days_week"] = duration.apply(
        lambda x: 4.0 if pd.notna(x) and x >= 60 else 3.0 if pd.notna(x) and x >= 30 else 2.0 if pd.notna(x) else pd.NA
    )
    return frame


def _map_goal_from_health_fitness(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "age": df.get("age"),
            "gender": df.get("gender"),
            "weight_kg": df.get("weight_kg"),
            "height_m": _to_numeric(df.get("height_cm", pd.Series(dtype="float"))) / 100.0,
            "bmi": df.get("bmi"),
            "fat_percentage": pd.NA,
            "workout_frequency_days_week": 3.0,
            "experience_level": _intensity_to_experience(df.get("intensity", pd.Series(dtype="object"))),
            "calories_burned": df.get("calories_burned"),
            "avg_bpm": df.get("avg_heart_rate"),
        }
    )


def _map_goal_from_bodyfat(df: pd.DataFrame) -> pd.DataFrame:
    gender_series = df.get("Sex", pd.Series(["Other"] * len(df)))
    if not isinstance(gender_series, pd.Series):
        gender_series = pd.Series(gender_series)
    return pd.DataFrame(
        {
            "age": df.get("Age"),
            "gender": gender_series,
            "weight_kg": _to_numeric(df.get("Weight", pd.Series(dtype="float"))) * 0.453592,
            "height_m": _to_numeric(df.get("Height", pd.Series(dtype="float"))) * 0.0254,
            "bmi": pd.NA,
            "fat_percentage": df.get("BodyFat"),
            "workout_frequency_days_week": pd.NA,
            "experience_level": pd.NA,
            "calories_burned": pd.NA,
            "avg_bpm": pd.NA,
        }
    )


def _map_goal_file(path: Path) -> pd.DataFrame | None:
    try:
        header = set(_read_header(path))
    except Exception:
        return None

    if not _has_any_signature(header, GOAL_HEADER_SIGNATURES):
        return None

    try:
        df = pd.read_csv(path, low_memory=False)
    except Exception:
        return None

    lower_cols = {c.strip().lower() for c in df.columns}

    if {"age", "gender", "weight (kg)", "height (m)"}.issubset(lower_cols):
        return _map_goal_from_gym_schema(df)
    if {"age", "gender", "actual weight", "bmi"}.issubset(lower_cols):
        return _map_goal_from_exercise_dataset(df)
    if {"age", "gender", "height_cm", "weight_kg"}.issubset(lower_cols):
        return _map_goal_from_health_fitness(df)
    if {"bodyfat", "age", "weight", "height"}.issubset(lower_cols):
        return _map_goal_from_bodyfat(df)

    return None


def _finalize_goal_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame

    work = frame.copy()

    for col in (
        "age",
        "weight_kg",
        "height_m",
        "bmi",
        "fat_percentage",
        "workout_frequency_days_week",
        "experience_level",
        "calories_burned",
        "avg_bpm",
    ):
        work[col] = _to_numeric(work[col])

    work["gender"] = work["gender"].map(_normalize_gender)

    # Derive missing height using BMI and weight when possible.
    missing_height = work["height_m"].isna() | (work["height_m"] <= 0)
    has_weight_and_bmi = (work["weight_kg"] > 0) & (work["bmi"] > 0)
    work.loc[missing_height & has_weight_and_bmi, "height_m"] = (
        work.loc[missing_height & has_weight_and_bmi, "weight_kg"] / work.loc[missing_height & has_weight_and_bmi, "bmi"]
    ) ** 0.5

    # Derive BMI when missing.
    missing_bmi = work["bmi"].isna() | (work["bmi"] <= 0)
    has_weight_and_height = (work["weight_kg"] > 0) & (work["height_m"] > 0)
    work.loc[missing_bmi & has_weight_and_height, "bmi"] = (
        work.loc[missing_bmi & has_weight_and_height, "weight_kg"]
        / (work.loc[missing_bmi & has_weight_and_height, "height_m"] ** 2)
    )

    # Keep only rows with essential body profile fields.
    work = work.dropna(subset=["age", "weight_kg", "height_m"])
    work = work[(work["weight_kg"] > 0) & (work["height_m"] > 0)]

    fill_defaults = {
        "bmi": work["bmi"].median(),
        "fat_percentage": work["fat_percentage"].median(),
        "workout_frequency_days_week": work["workout_frequency_days_week"].median(),
        "experience_level": work["experience_level"].median(),
        "calories_burned": work["calories_burned"].median(),
        "avg_bpm": work["avg_bpm"].median(),
    }
    for key, value in fill_defaults.items():
        if pd.isna(value):
            if key == "workout_frequency_days_week":
                value = 3.0
            elif key == "experience_level":
                value = 2.0
            elif key == "avg_bpm":
                value = 120.0
            elif key == "calories_burned":
                value = 300.0
            elif key == "fat_percentage":
                value = 22.0
            else:
                value = 0.0
        work[key] = work[key].fillna(value)

    work[GOAL_TARGET_COLUMN] = work.apply(_derive_goal_label, axis=1)
    work = work[GOAL_FEATURE_COLUMNS + [GOAL_TARGET_COLUMN]].dropna()
    work = work.drop_duplicates()
    return work


def prepare_goal_training_data(dataset_path: str | Path) -> pd.DataFrame:
    source = Path(dataset_path)
    candidate_files = _iter_candidate_csv_files(source, GOAL_HEADER_SIGNATURES)
    if not candidate_files:
        raise ValueError(f"No compatible goal-training CSV files found in: {source}")

    mapped_frames: list[pd.DataFrame] = []
    used_files: list[str] = []

    for file_path in candidate_files:
        mapped = _map_goal_file(file_path)
        if mapped is None or mapped.empty:
            continue
        finalized = _finalize_goal_frame(mapped)
        if finalized.empty:
            continue
        mapped_frames.append(finalized)
        used_files.append(str(file_path))

    if not mapped_frames:
        raise ValueError(f"No usable rows found for goal training in: {source}")

    combined = pd.concat(mapped_frames, ignore_index=True)
    combined.attrs["source_files"] = used_files
    return combined


def _parse_check_in_hour(value: Any) -> int:
    text = str(value or "").strip()
    if ":" in text:
        return _safe_int(text.split(":")[0], 0)
    return _safe_int(text, 0)


def _map_success_file(path: Path) -> pd.DataFrame | None:
    try:
        header = set(_read_header(path))
    except Exception:
        return None
    if not _has_any_signature(header, SUCCESS_HEADER_SIGNATURES):
        return None

    try:
        df = pd.read_csv(path, low_memory=False)
    except Exception:
        return None

    mapped = pd.DataFrame(
        {
            "age": df.get("age"),
            "gender": df.get("gender"),
            "membership_type": df.get("membership_type"),
            "workout_type": df.get("workout_type"),
            "workout_duration_minutes": df.get("workout_duration_minutes"),
            "calories_burned": df.get("calories_burned"),
            "check_in_hour": df.get("check_in_time").map(_parse_check_in_hour),
            "attendance_status": df.get("attendance_status"),
        }
    )

    mapped["age"] = _to_numeric(mapped["age"])
    mapped["workout_duration_minutes"] = _to_numeric(mapped["workout_duration_minutes"])
    mapped["calories_burned"] = _to_numeric(mapped["calories_burned"])
    mapped["gender"] = mapped["gender"].map(_normalize_gender)
    mapped["membership_type"] = mapped["membership_type"].fillna("Unknown").astype(str)
    mapped["workout_type"] = mapped["workout_type"].fillna("Unknown").astype(str)

    status_text = mapped["attendance_status"].astype(str).str.strip().str.lower()
    valid_status = ~status_text.isin({"", "nan", "none"})
    mapped = mapped[valid_status]

    mapped = mapped.dropna(subset=["age", "workout_duration_minutes", "calories_burned"])
    mapped[SUCCESS_TARGET_COLUMN] = status_text.loc[mapped.index].isin({"present", "attended", "yes"}).astype(int)
    return mapped[SUCCESS_FEATURE_COLUMNS + [SUCCESS_TARGET_COLUMN]]


def prepare_success_training_data(dataset_path: str | Path) -> pd.DataFrame:
    source = Path(dataset_path)
    candidate_files = _iter_candidate_csv_files(source, SUCCESS_HEADER_SIGNATURES)
    if not candidate_files:
        raise ValueError(f"No compatible success-training CSV files found in: {source}")

    mapped_frames: list[pd.DataFrame] = []
    used_files: list[str] = []

    for file_path in candidate_files:
        mapped = _map_success_file(file_path)
        if mapped is None or mapped.empty:
            continue
        mapped_frames.append(mapped)
        used_files.append(str(file_path))

    if not mapped_frames:
        raise ValueError(f"No usable rows found for success training in: {source}")

    combined = pd.concat(mapped_frames, ignore_index=True).drop_duplicates()
    combined.attrs["source_files"] = used_files
    return combined


def make_goal_preprocessor() -> ColumnTransformer:
    numeric_features = [
        "age",
        "weight_kg",
        "height_m",
        "bmi",
        "fat_percentage",
        "workout_frequency_days_week",
        "experience_level",
        "calories_burned",
        "avg_bpm",
    ]
    categorical_features = ["gender"]
    return ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numeric_features),
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features),
        ]
    )


def make_success_preprocessor() -> ColumnTransformer:
    numeric_features = ["age", "workout_duration_minutes", "calories_burned", "check_in_hour"]
    categorical_features = ["gender", "membership_type", "workout_type"]
    return ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numeric_features),
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features),
        ]
    )


def build_goal_features_from_payload(payload: dict[str, Any]) -> pd.DataFrame:
    height_m = _safe_float(payload.get("height_m"), 0.0)
    if not height_m:
        height_cm = _safe_float(payload.get("height_cm"), 0.0)
        if height_cm:
            height_m = height_cm / 100.0

    weight_kg = _safe_float(payload.get("weight_kg", payload.get("weight")), 0.0)
    bmi = _safe_float(payload.get("bmi"), 0.0)
    if bmi == 0.0 and height_m > 0 and weight_kg > 0:
        bmi = weight_kg / (height_m * height_m)

    frame = pd.DataFrame(
        [
            {
                "age": _safe_float(payload.get("age"), 0.0),
                "gender": _normalize_gender(payload.get("gender")),
                "weight_kg": weight_kg,
                "height_m": height_m,
                "bmi": bmi,
                "fat_percentage": _safe_float(payload.get("fat_percentage"), 0.0),
                "workout_frequency_days_week": _safe_float(payload.get("workout_frequency_days_week"), 0.0),
                "experience_level": _safe_float(payload.get("experience_level"), 0.0),
                "calories_burned": _safe_float(payload.get("calories_burned"), 0.0),
                "avg_bpm": _safe_float(payload.get("avg_bpm"), 0.0),
            }
        ]
    )
    return frame[GOAL_FEATURE_COLUMNS]


def build_success_features_from_payload(payload: dict[str, Any]) -> pd.DataFrame:
    check_in_hour = _safe_int(payload.get("check_in_hour"), 0)
    if check_in_hour == 0 and payload.get("check_in_time"):
        text = str(payload.get("check_in_time"))
        if ":" in text:
            check_in_hour = _safe_int(text.split(":")[0], 0)

    frame = pd.DataFrame(
        [
            {
                "age": _safe_float(payload.get("age"), 0.0),
                "gender": _normalize_gender(payload.get("gender")),
                "membership_type": str(payload.get("membership_type", "Unknown")),
                "workout_type": str(payload.get("workout_type", "Unknown")),
                "workout_duration_minutes": _safe_float(payload.get("workout_duration_minutes"), 0.0),
                "calories_burned": _safe_float(payload.get("calories_burned"), 0.0),
                "check_in_hour": check_in_hour,
            }
        ]
    )
    return frame[SUCCESS_FEATURE_COLUMNS]

