"""
Training Engine for AI Coach

Learns patterns from multiple datasets to enable:
- Profile-based personalization
- Intelligent exercise recommendations
- Diet planning based on health profiles
- Performance predictions
- Disease/health condition awareness
"""

from __future__ import annotations

import json
import pickle
from pathlib import Path
from typing import Any
from collections import defaultdict
import statistics
import logging

logger = logging.getLogger(__name__)


class TrainingEngine:
    """
    Trains the coach on patterns from all datasets.
    Creates models and indexes for efficient recommendations.
    """
    
    def __init__(self, dataset_loader):
        """
        Initialize training engine with a dataset loader.
        
        Args:
            dataset_loader: MultiDatasetLoader instance
        """
        self.loader = dataset_loader
        self.exercise_model = {}
        self.nutrition_model = {}
        self.fitness_profiles_model = {}
        self.health_conditions_model = {}
        self.trained = False
    
    def train(self) -> None:
        """Train on all loaded datasets."""
        logger.info("Starting training on all datasets...")
        
        self._train_exercise_model()
        self._train_nutrition_model()
        self._train_fitness_profiles_model()
        self._train_health_conditions_model()
        
        self.trained = True
        logger.info("Training complete!")
    
    def _train_exercise_model(self) -> None:
        """Train exercise patterns model."""
        logger.info("Training exercise model...")
        
        exercises = self.loader.get_dataset("exercises")
        if not exercises:
            logger.warning("No exercise dataset found")
            return
        
        # Index exercises by muscle group
        by_muscle = defaultdict(list)
        by_difficulty = defaultdict(list)
        by_equipment = defaultdict(list)
        by_type = defaultdict(list)
        
        for ex in exercises:
            muscle = (ex.get("muscle") or "").strip().lower()
            difficulty = (ex.get("difficulty") or "").strip().lower()
            equipment = (ex.get("equipment") or "").strip().lower()
            ex_type = (ex.get("type") or "").strip().lower()
            
            if muscle:
                by_muscle[muscle].append(ex)
            if difficulty:
                by_difficulty[difficulty].append(ex)
            if equipment:
                by_equipment[equipment].append(ex)
            if ex_type:
                by_type[ex_type].append(ex)
        
        self.exercise_model = {
            "total_exercises": len(exercises),
            "by_muscle": dict(by_muscle),
            "by_difficulty": dict(by_difficulty),
            "by_equipment": dict(by_equipment),
            "by_type": dict(by_type),
            "muscle_distribution": {k: len(v) for k, v in by_muscle.items()},
            "difficulty_distribution": {k: len(v) for k, v in by_difficulty.items()},
        }
        
        logger.info(f"Trained exercise model with {len(exercises)} exercises")
        logger.info(f"  Muscle groups: {len(by_muscle)}")
        logger.info(f"  Difficulty levels: {len(by_difficulty)}")
        logger.info(f"  Equipment types: {len(by_equipment)}")
    
    def _train_nutrition_model(self) -> None:
        """Train nutrition and diet patterns model."""
        logger.info("Training nutrition model...")
        
        foods = self.loader.get_dataset("foods")
        if not foods:
            logger.warning("No food dataset found")
            return
        
        # Index foods by category and macro profile
        by_category = defaultdict(list)
        high_protein_foods = []
        high_carb_foods = []
        low_calorie_foods = []
        high_fiber_foods = []
        
        macro_stats = {
            "calories": [],
            "protein_g": [],
            "carbs_g": [],
            "fat_g": [],
            "fiber_g": [],
        }
        
        for food in foods:
            category = (food.get("category") or "").strip().lower()
            if category:
                by_category[category].append(food)
            
            # Classify by macro profile
            calories = food.get("calories", 0) or 0
            protein = food.get("protein_g", 0) or 0
            carbs = food.get("carbs_g", 0) or 0
            fiber = food.get("fiber_g", 0) or 0
            
            if protein > 20:
                high_protein_foods.append(food)
            if carbs > 40:
                high_carb_foods.append(food)
            if calories < 100:
                low_calorie_foods.append(food)
            if fiber > 5:
                high_fiber_foods.append(food)
            
            # Collect stats
            if calories:
                macro_stats["calories"].append(calories)
            if protein:
                macro_stats["protein_g"].append(protein)
            if carbs:
                macro_stats["carbs_g"].append(carbs)
            if fiber:
                macro_stats["fat_g"].append(food.get("fat_g", 0) or 0)
            if fiber:
                macro_stats["fiber_g"].append(fiber)
        
        # Calculate statistics
        macro_means = {}
        macro_medians = {}
        for macro, values in macro_stats.items():
            if values:
                macro_means[macro] = round(statistics.mean(values), 2)
                macro_medians[macro] = round(statistics.median(values), 2)
        
        self.nutrition_model = {
            "total_foods": len(foods),
            "by_category": dict(by_category),
            "categories": list(by_category.keys()),
            "high_protein_foods": high_protein_foods,
            "high_carb_foods": high_carb_foods,
            "low_calorie_foods": low_calorie_foods,
            "high_fiber_foods": high_fiber_foods,
            "macro_statistics": {
                "means": macro_means,
                "medians": macro_medians,
            },
            "category_distribution": {k: len(v) for k, v in by_category.items()},
        }
        
        logger.info(f"Trained nutrition model with {len(foods)} foods")
        logger.info(f"  Categories: {len(by_category)}")
        logger.info(f"  High protein foods: {len(high_protein_foods)}")
        logger.info(f"  Low calorie foods: {len(low_calorie_foods)}")
    
    def _train_fitness_profiles_model(self) -> None:
        """Train fitness profile patterns model."""
        logger.info("Training fitness profiles model...")
        
        # Analyze activity datasets for common patterns
        activity_datasets = [
            "daily_activity", "daily_calories", "daily_steps", "heart_rate", "sleep_day", "weight_log"
        ]
        
        activity_data = []
        for dataset_name in activity_datasets:
            data = self.loader.get_dataset(dataset_name)
            if data:
                activity_data.extend(data)
        
        if activity_data:
            logger.info(f"Analyzing {len(activity_data)} activity records")
            
            # Build patterns from activity data
            self.fitness_profiles_model = {
                "total_activity_records": len(activity_data),
                "common_metrics": self._extract_activity_metrics(activity_data),
                "activity_patterns": self._build_activity_patterns(activity_data),
            }
        else:
            self.fitness_profiles_model = {
                "total_activity_records": 0,
                "common_metrics": {},
                "activity_patterns": {},
            }
    
    def _extract_activity_metrics(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        """Extract common metrics from activity records."""
        metrics = {}
        
        # Look for common activity fields
        common_fields = [
            "calories", "Calories", "TotalSteps", "steps", "HeartRate", "SleepDuration",
            "steps_range", "minute_step", "intensity"
        ]
        
        # This helps understand what metrics are available in the data
        field_counts = defaultdict(int)
        for record in records:
            for field in common_fields:
                if field in record and record[field]:
                    field_counts[field] += 1
        
        metrics["available_fields"] = dict(field_counts)
        return metrics
    
    def _build_activity_patterns(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        """Build patterns from activity records."""
        return {
            "record_count": len(records),
            "data_types": list(set(str(type(v).__name__) for r in records for v in r.values())),
        }
    
    def _train_health_conditions_model(self) -> None:
        """Train health conditions and restrictions model."""
        logger.info("Training health conditions model...")
        
        # Load health/allergy data
        allergen_foods = self.loader.get_dataset("food_allergens")
        food_allergy_data = self.loader.get_dataset("food_allergy_detailed")
        
        # Build health condition to food restrictions mapping
        health_food_restrictions = {
            "diabetes": {
                "avoid": ["sugar", "high_carb", "sweet", "refined", "processed"],
                "prefer": ["low_carb", "high_fiber", "vegetables", "nuts"],
                "macro_targets": {"carbs_g": 130}
            },
            "hypertension": {
                "avoid": ["salt", "sodium", "processed", "canned"],
                "prefer": ["potassium_rich", "low_sodium", "vegetables"],
                "macro_targets": {"sodium_mg": 2300}
            },
            "obesity": {
                "avoid": ["high_calorie", "sugars", "fried", "fatty"],
                "prefer": ["low_calorie", "high_fiber", "lean_protein"],
                "macro_targets": {"calories": 2000}
            },
            "celiac": {
                "avoid": ["gluten", "wheat", "barley", "bread", "pasta"],
                "prefer": ["gluten_free", "rice", "corn"],
            },
            "lactose_intolerance": {
                "avoid": ["dairy", "milk", "cheese", "yogurt", "cream"],
                "prefer": ["non_dairy", "plant_based", "lactose_free"],
            }
        }
        
        self.health_conditions_model = {
            "health_food_restrictions": health_food_restrictions,
            "allergen_datasets_loaded": bool(allergen_foods),
            "allergy_data_loaded": bool(food_allergy_data),
            "common_conditions": list(health_food_restrictions.keys()),
        }
        
        logger.info(f"Trained health conditions model with {len(health_food_restrictions)} conditions")
    
    def get_recommended_exercises(self, profile: dict[str, Any], limit: int = 10) -> list[dict[str, Any]]:
        """
        Get recommended exercises based on user profile.
        
        Args:
            profile: User profile with goal, fitness_level, available_equipment
            limit: Max number of recommendations
            
        Returns:
            List of recommended exercises
        """
        if not self.trained:
            return []
        
        goal = (profile.get("goal") or "").strip().lower()
        level = (profile.get("fitness_level") or "").strip().lower()
        equipment = (profile.get("available_equipment") or "").strip().lower()
        
        candidates = []
        
        # Get exercises by difficulty
        if level in self.exercise_model.get("by_difficulty", {}):
            candidates.extend(self.exercise_model["by_difficulty"][level])
        
        # Filter by equipment if specified
        if equipment and equipment in self.exercise_model.get("by_equipment", {}):
            candidates = [ex for ex in candidates if equipment in (ex.get("equipment") or "").lower()]
        
        # Prioritize by goal (muscle group)
        goal_muscle_map = {
            "muscle_gain": ["chest", "back", "legs", "shoulders", "arms"],
            "fat_loss": ["full body", "cardio", "core"],
            "endurance": ["cardio", "legs"],
        }
        
        target_muscles = goal_muscle_map.get(goal, [])
        
        if target_muscles:
            candidates.sort(
                key=lambda ex: any(
                    tm in (ex.get("muscle") or "").lower() for tm in target_muscles
                ),
                reverse=True
            )
        
        return candidates[:limit]
    
    def get_recommended_foods(self, profile: dict[str, Any], limit: int = 15) -> list[dict[str, Any]]:
        """
        Get recommended foods based on user profile.
        
        Args:
            profile: User profile with goal, calorie_target, allergies, dietary_preferences
            limit: Max number of recommendations
            
        Returns:
            List of recommended foods
        """
        if not self.trained:
            return []
        
        goal = (profile.get("goal") or "").strip().lower()
        calorie_target = profile.get("calorie_target")
        allergies = (profile.get("allergies") or "").lower().split(",")
        dietary_prefs = (profile.get("dietary_preferences") or "").lower().split(",")
        
        candidates = []
        
        # Select foods based on goal
        if goal == "fat_loss":
            candidates = self.nutrition_model.get("low_calorie_foods", [])
        elif goal == "muscle_gain":
            candidates = self.nutrition_model.get("high_protein_foods", [])
        else:
            # Get balanced foods
            all_foods = []
            for foods in self.nutrition_model.get("by_category", {}).values():
                all_foods.extend(foods)
            candidates = all_foods
        
        # Filter by allergies
        if allergies and allergies[0]:
            candidates = [
                food for food in candidates
                if not any(allergy in (food.get("name") or "").lower() for allergy in allergies)
            ]
        
        return candidates[:limit]
    
    def analyze_health_restrictions(self, conditions: list[str]) -> dict[str, Any]:
        """
        Analyze food restrictions based on health conditions.
        
        Args:
            conditions: List of health conditions (e.g., ["diabetes", "hypertension"])
            
        Returns:
            Dictionary with food recommendations and restrictions
        """
        if not self.trained:
            return {}
        
        restrictions = {
            "avoid_foods": set(),
            "prefer_foods": set(),
            "macro_targets": {},
            "notes": []
        }
        
        health_model = self.health_conditions_model.get("health_food_restrictions", {})
        
        for condition in conditions:
            condition_lower = condition.lower().strip()
            if condition_lower in health_model:
                cond_rules = health_model[condition_lower]
                restrictions["avoid_foods"].update(cond_rules.get("avoid", []))
                restrictions["prefer_foods"].update(cond_rules.get("prefer", []))
                restrictions["macro_targets"].update(cond_rules.get("macro_targets", {}))
                restrictions["notes"].append(f"Based on {condition}")
        
        # Convert sets to lists for JSON serialization
        restrictions["avoid_foods"] = list(restrictions["avoid_foods"])
        restrictions["prefer_foods"] = list(restrictions["prefer_foods"])
        
        return restrictions
    
    def save_model(self, path: Path) -> None:
        """Save trained model to disk."""
        path.parent.mkdir(parents=True, exist_ok=True)
        model_data = {
            "exercise_model": self.exercise_model,
            "nutrition_model": self.nutrition_model,
            "fitness_profiles_model": self.fitness_profiles_model,
            "health_conditions_model": self.health_conditions_model,
        }
        with path.open("wb") as f:
            pickle.dump(model_data, f)
        logger.info(f"Saved model to {path}")
    
    def load_model(self, path: Path) -> bool:
        """Load trained model from disk."""
        if not path.exists():
            return False
        
        try:
            with path.open("rb") as f:
                model_data = pickle.load(f)
            self.exercise_model = model_data.get("exercise_model", {})
            self.nutrition_model = model_data.get("nutrition_model", {})
            self.fitness_profiles_model = model_data.get("fitness_profiles_model", {})
            self.health_conditions_model = model_data.get("health_conditions_model", {})
            self.trained = True
            logger.info(f"Loaded model from {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False
    
    def get_training_summary(self) -> dict[str, Any]:
        """Get summary of what the model has learned."""
        return {
            "trained": self.trained,
            "exercises_count": self.exercise_model.get("total_exercises", 0),
            "foods_count": self.nutrition_model.get("total_foods", 0),
            "muscle_groups": list(self.exercise_model.get("by_muscle", {}).keys()),
            "food_categories": self.nutrition_model.get("categories", []),
            "health_conditions": self.health_conditions_model.get("common_conditions", []),
        }


if __name__ == "__main__":
    from multi_dataset_loader import MultiDatasetLoader
    from dataset_paths import resolve_dataset_root
    
    # Example usage
    root = resolve_dataset_root()
    loader = MultiDatasetLoader(root)
    loader.load_all()
    
    engine = TrainingEngine(loader)
    engine.train()
    
    print("\n=== Training Summary ===")
    summary = engine.get_training_summary()
    print(json.dumps(summary, indent=2))
    
    # Example usage
    profile = {
        "goal": "muscle_gain",
        "fitness_level": "intermediate",
        "available_equipment": "dumbbell"
    }
    
    print("\n=== Recommended Exercises ===")
    exercises = engine.get_recommended_exercises(profile)
    for ex in exercises[:5]:
        print(f"  - {ex.get('exercise')} ({ex.get('muscle')}, {ex.get('difficulty')})")
    
    print("\n=== Health Restrictions Analysis ===")
    restrictions = engine.analyze_health_restrictions(["diabetes", "hypertension"])
    print(json.dumps(restrictions, indent=2))
