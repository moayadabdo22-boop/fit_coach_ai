"""
Multi-Dataset Loader and Indexer

Loads all 50+ datasets and creates indexed collections for:
- Exercises, Fitness Programs, Gym Recommendations
- Food, Nutrition, Diet Recommendations  
- Fitness Profiles, User Progress, Activity Data
- Health Conditions, Disease Impacts, Medical Rules

This enables the AI to train on comprehensive data patterns.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


def _safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert value to float."""
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    """Safely convert value to int."""
    try:
        if value is None or value == "":
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


class MultiDatasetLoader:
    """Loads and indexes all available datasets in the datasets folder."""
    
    def __init__(self, dataset_root: Path):
        self.dataset_root = Path(dataset_root)
        self.datasets: dict[str, list[dict[str, Any]]] = {}
        self.metadata: dict[str, dict[str, Any]] = {}
        self.loaded = False
    
    def load_all(self) -> None:
        """Load and index all datasets."""
        logger.info(f"Starting to load all datasets from {self.dataset_root}")
        
        # Load different dataset categories
        self._load_exercise_datasets()
        self._load_food_nutrition_datasets()
        self._load_activity_datasets()
        self._load_fitness_profile_datasets()
        self._load_health_datasets()
        self._load_recommendation_datasets()
        
        self.loaded = True
        logger.info(f"Loaded {len(self.datasets)} dataset categories with {sum(len(v) for v in self.datasets.values())} total records")
    
    def _load_csv(self, filename: str, dataset_name: str, required_fields: list[str] | None = None) -> list[dict[str, Any]]:
        """Load a CSV file and return as list of dicts."""
        filepath = self.dataset_root / filename
        rows = []
        
        if not filepath.exists():
            logger.debug(f"Dataset not found: {filename}")
            return rows
        
        try:
            with filepath.open("r", encoding="utf-8", errors="ignore", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if required_fields and not all(row.get(field) for field in required_fields):
                        continue
                    rows.append(row)
            
            logger.info(f"Loaded {len(rows)} records from {filename}")
            self.metadata[dataset_name] = {
                "type": "csv",
                "file": filename,
                "record_count": len(rows),
                "sample_columns": list(rows[0].keys()) if rows else []
            }
        except Exception as e:
            logger.error(f"Error loading {filename}: {e}")
        
        return rows
    
    def _load_exercise_datasets(self) -> None:
        """Load all exercise and gym-related datasets."""
        logger.info("Loading exercise datasets...")
        
        # Main gym dataset
        gym_data = self._load_csv("megaGymDataset.csv", "exercises_mega_gym")
        if gym_data:
            exercises = []
            for row in gym_data:
                exercise = {
                    "exercise": (row.get("Title") or row.get("Exercise") or "").strip(),
                    "muscle": (row.get("BodyPart") or row.get("Body Part") or "").strip(),
                    "difficulty": (row.get("Level") or row.get("Difficulty") or "Beginner").strip(),
                    "equipment": (row.get("Equipment") or "Bodyweight").strip(),
                    "type": (row.get("Type") or "Strength").strip(),
                    "reps": (row.get("Reps") or "").strip(),
                    "description": (row.get("Desc") or row.get("Description") or "").strip(),
                }
                if exercise["exercise"]:
                    exercises.append(exercise)
            self.datasets["exercises"] = exercises
        
        # Gym recommendation dataset
        gym_rec = self._load_csv("gym recommendation.xlsx", "gym_recommendations")
        self.datasets["gym_recommendations"] = gym_rec
    
    def _load_food_nutrition_datasets(self) -> None:
        """Load all food and nutrition datasets."""
        logger.info("Loading food and nutrition datasets...")
        
        # Daily food nutrition
        food_data = self._load_csv("daily_food_nutrition_dataset.csv", "daily_food_nutrition")
        if food_data:
            foods = []
            for row in food_data:
                food = {
                    "name": (row.get("Food_Item") or row.get("Food") or row.get("name") or "").strip(),
                    "category": (row.get("Category") or row.get("Group") or "").strip(),
                    "calories": _safe_int(row.get("Calories (kcal)") or row.get("Calories")),
                    "protein_g": _safe_float(row.get("Protein (g)") or row.get("Protein")),
                    "carbs_g": _safe_float(row.get("Carbohydrates (g)") or row.get("Carbs")),
                    "fat_g": _safe_float(row.get("Fat (g)") or row.get("Fat")),
                    "fiber_g": _safe_float(row.get("Fiber (g)") or row.get("Fiber")),
                    "sugars_g": _safe_float(row.get("Sugars (g)") or row.get("Sugars")),
                    "sodium_mg": _safe_float(row.get("Sodium (mg)") or row.get("Sodium")),
                    "cholesterol_mg": _safe_float(row.get("Cholesterol (mg)") or row.get("Cholesterol")),
                    "meal_type": (row.get("Meal_Type") or row.get("Meal Type") or "any").strip(),
                }
                if food["name"]:
                    foods.append(food)
            self.datasets["foods"] = foods
        
        # Diet recommendations
        diet_rec = self._load_csv("diet_recommendations_dataset.csv", "diet_recommendations")
        if diet_rec:
            self.datasets["diet_recommendations"] = diet_rec
        
        # Personalized diet recommendations
        pers_diet = self._load_csv("Personalized_Diet_Recommendations.csv", "personalized_diet_recommendations")
        if pers_diet:
            self.datasets["personalized_diet_recommendations"] = pers_diet
        
        # Food allergens
        allergens = self._load_csv("food-allergens.csv", "food_allergens")
        if allergens:
            self.datasets["food_allergens"] = allergens
        
        # Fitness recommendation dataset (often has diet info)
        fitness_rec = self._load_csv("fitness-recommendation-dataset.csv", "fitness_recommendations")
        if fitness_rec:
            self.datasets["fitness_recommendations"] = fitness_rec
        
        # Open Food Facts
        open_food = self._load_csv("en.openfoodfacts.org.products.csv", "open_food_facts")
        if open_food:
            self.datasets["open_food_facts"] = open_food
    
    def _load_activity_datasets(self) -> None:
        """Load all activity tracking datasets."""
        logger.info("Loading activity and tracking datasets...")
        
        activity_files = {
            "dailyActivity_merged.csv": "daily_activity",
            "dailyCalories_merged.csv": "daily_calories",
            "dailyIntensities_merged.csv": "daily_intensities",
            "dailySteps_merged.csv": "daily_steps",
            "hourlyCalories_merged.csv": "hourly_calories",
            "hourlyIntensities_merged.csv": "hourly_intensities",
            "hourlySteps_merged.csv": "hourly_steps",
            "heartrate_seconds_merged.csv": "heart_rate",
            "minuteCaloriesNarrow_merged.csv": "minute_calories_narrow",
            "minuteCaloriesWide_merged.csv": "minute_calories_wide",
            "minuteIntensitiesNarrow_merged.csv": "minute_intensities_narrow",
            "minuteIntensitiesWide_merged.csv": "minute_intensities_wide",
            "minuteMETsNarrow_merged.csv": "minute_mets",
            "minuteSleep_merged.csv": "minute_sleep",
            "minuteStepsNarrow_merged.csv": "minute_steps_narrow",
            "minuteStepsWide_merged.csv": "minute_steps_wide",
            "sleepDay_merged.csv": "sleep_day",
            "weightLogInfo_merged.csv": "weight_log",
        }
        
        for filename, dataset_name in activity_files.items():
            data = self._load_csv(filename, dataset_name)
            if data:
                self.datasets[dataset_name] = data
    
    def _load_fitness_profile_datasets(self) -> None:
        """Load fitness profile and user datasets."""
        logger.info("Loading fitness profile datasets...")
        
        # Sample data CSVs
        profile_files = {
            "acquisition_samples.csv": "acquisition_samples",
            "agricultural_samples.csv": "agricultural_samples",
        }
        
        for filename, dataset_name in profile_files.items():
            data = self._load_csv(filename, dataset_name)
            if data:
                self.datasets[dataset_name] = data
    
    def _load_health_datasets(self) -> None:
        """Load health condition and disease-related datasets."""
        logger.info("Loading health datasets...")
        
        # Food allergy dataset  
        allergy_data = self._load_csv("food_allergy_dataset.csv", "food_allergy_detailed")
        if allergy_data:
            self.datasets["food_allergy_detailed"] = allergy_data
    
    def _load_recommendation_datasets(self) -> None:
        """Load recommendation and pattern datasets."""
        logger.info("Loading recommendation datasets...")
        
        # These would be any other recommendation files
        nutrition_file = self._load_csv("nutrition.xlsx", "nutrition_patterns")
        if nutrition_file:
            self.datasets["nutrition_patterns"] = nutrition_file
    
    def get_dataset(self, name: str) -> list[dict[str, Any]]:
        """Get a specific dataset by name."""
        return self.datasets.get(name, [])
    
    def get_all_datasets(self) -> dict[str, list[dict[str, Any]]]:
        """Get all loaded datasets."""
        return self.datasets
    
    def get_metadata(self) -> dict[str, dict[str, Any]]:
        """Get metadata about all loaded datasets."""
        return self.metadata
    
    def search_datasets(self, query: str, dataset_name: str | None = None) -> dict[str, list[dict[str, Any]]]:
        """
        Search for records matching the query across datasets.
        
        Args:
            query: Search query
            dataset_name: Optional specific dataset to search in
            
        Returns:
            Dictionary of dataset_name -> matching records
        """
        results: dict[str, list[dict[str, Any]]] = {}
        query_lower = query.lower()
        
        datasets_to_search = {dataset_name: self.datasets[dataset_name]} if dataset_name else self.datasets
        
        for name, records in datasets_to_search.items():
            matches = []
            for record in records:
                # Search across all string values in the record
                record_text = " ".join(str(v).lower() for v in record.values())
                if query_lower in record_text:
                    matches.append(record)
            
            if matches:
                results[name] = matches
        
        return results
    
    def get_exercise_patterns(self) -> dict[str, Any]:
        """Extract patterns from exercise datasets for training."""
        patterns = {
            "muscle_groups": defaultdict(int),
            "difficulties": defaultdict(int),
            "equipment": defaultdict(int),
            "exercise_types": defaultdict(int),
        }
        
        exercises = self.datasets.get("exercises", [])
        for ex in exercises:
            patterns["muscle_groups"][ex.get("muscle", "unknown")] += 1
            patterns["difficulties"][ex.get("difficulty", "unknown")] += 1
            patterns["equipment"][ex.get("equipment", "unknown")] += 1
            patterns["exercise_types"][ex.get("type", "unknown")] += 1
        
        return {k: dict(v) for k, v in patterns.items()}
    
    def get_nutrition_patterns(self) -> dict[str, Any]:
        """Extract patterns from nutrition datasets for training."""
        patterns = {
            "food_categories": defaultdict(int),
            "macro_ranges": {
                "protein_high": 0,
                "carbs_high": 0,
                "fat_high": 0,
                "low_calorie": 0,
            },
            "avg_macros": {
                "protein_g": 0,
                "carbs_g": 0,
                "fat_g": 0,
                "calories": 0,
            }
        }
        
        foods = self.datasets.get("foods", [])
        macro_counts = {"protein_g": 0, "carbs_g": 0, "fat_g": 0, "calories": 0}
        
        for food in foods:
            patterns["food_categories"][food.get("category", "unknown")] += 1
            
            # Count high-macro foods
            if food.get("protein_g", 0) > 20:
                patterns["macro_ranges"]["protein_high"] += 1
            if food.get("carbs_g", 0) > 40:
                patterns["macro_ranges"]["carbs_high"] += 1
            if food.get("fat_g", 0) > 15:
                patterns["macro_ranges"]["fat_high"] += 1
            if food.get("calories", 0) < 100:
                patterns["macro_ranges"]["low_calorie"] += 1
            
            # Accumulate for averages
            if food.get("protein_g"):
                macro_counts["protein_g"] += food["protein_g"]
            if food.get("carbs_g"):
                macro_counts["carbs_g"] += food["carbs_g"]
            if food.get("fat_g"):
                macro_counts["fat_g"] += food["fat_g"]
            if food.get("calories"):
                macro_counts["calories"] += food["calories"]
        
        # Calculate averages
        if foods:
            for macro, total in macro_counts.items():
                patterns["avg_macros"][macro] = round(total / len(foods), 2)
        
        return patterns


if __name__ == "__main__":
    # Example usage
    import sys
    from dataset_paths import resolve_dataset_root
    
    root = resolve_dataset_root()
    loader = MultiDatasetLoader(root)
    loader.load_all()
    
    print("\n=== Loaded Datasets ===")
    for name, records in loader.get_all_datasets().items():
        print(f"{name}: {len(records)} records")
    
    print("\n=== Exercise Patterns ===")
    ex_patterns = loader.get_exercise_patterns()
    print(json.dumps(ex_patterns, indent=2))
    
    print("\n=== Nutrition Patterns ===")
    nut_patterns = loader.get_nutrition_patterns()
    print(json.dumps(nut_patterns, indent=2))
