"""
Enhanced Recommendation Engine with Multi-Dataset Training

Extends the basic recommendation system to use:
- Trained patterns from all 50 datasets
- Personalized profile analysis
- Performance tracking data
- Health restrictions awareness
"""

from __future__ import annotations

import logging
from typing import Any
from datetime import datetime

logger = logging.getLogger(__name__)


class EnhancedRecommendationEngine:
    """
    Enhanced recommendation system that integrates with trained models.
    Provides personalized exercise and nutrition recommendations.
    """
    
    def __init__(self, 
                 training_engine,
                 personalization_engine,
                 original_recommender):
        """
        Initialize enhanced recommendation engine.
        
        Args:
            training_engine: TrainingEngine with trained models
            personalization_engine: PersonalizationEngine for profile analysis
            original_recommender: Original RecommendationEngine for fallback
        """
        self.training_engine = training_engine
        self.personalizer = personalization_engine
        self.original = original_recommender
        self.recommendation_history = {}
    
    def get_personalized_exercises(self, 
                                  profile: dict[str, Any],
                                  limit: int = 10) -> list[dict[str, Any]]:
        """
        Get exercises personalized to user profile using trained data.
        
        Args:
            profile: User profile
            limit: Max recommendations
            
        Returns:
            List of personalized exercise recommendations
        """
        # Use training engine's personalized recommendations
        exercises = self.training_engine.get_recommended_exercises(profile, limit)
        
        if not exercises:
            logger.warning("No exercises from training engine, using fallback")
            # Fallback to original recommender
            if hasattr(self.original, 'catalog'):
                return self.original.catalog.search_exercises(
                    query=profile.get("goal", ""),
                    limit=limit
                )
            return []
        
        # Enhance with formatting and details
        enhanced = []
        for i, ex in enumerate(exercises):
            enhanced_ex = {
                "rank": i + 1,
                "exercise": ex.get("exercise"),
                "muscle_group": ex.get("muscle"),
                "difficulty": ex.get("difficulty"),
                "equipment": ex.get("equipment"),
                "type": ex.get("type"),
                "description": ex.get("description"),
                "reps": ex.get("reps", ""),
                "suitability_score": self._calculate_suitability_score(ex, profile),
                "why_recommended": self._explain_recommendation(ex, profile),
            }
            enhanced.append(enhanced_ex)
        
        return enhanced
    
    def get_personalized_foods(self,
                              profile: dict[str, Any],
                              limit: int = 20) -> list[dict[str, Any]]:
        """
        Get foods personalized to user profile using trained data.
        
        Args:
            profile: User profile
            limit: Max recommendations
            
        Returns:
            List of personalized food recommendations
        """
        # Use training engine's personalized recommendations
        foods = self.training_engine.get_recommended_foods(profile, limit)
        
        if not foods:
            logger.warning("No foods from training engine, using fallback")
            # Fallback to original recommender
            if hasattr(self.original, 'catalog'):
                return self.original.catalog.foods[:limit]
            return []
        
        # Enhance with formatting and nutritional details
        enhanced = []
        for i, food in enumerate(foods):
            enhanced_food = {
                "rank": i + 1,
                "name": food.get("name"),
                "category": food.get("category"),
                "calories": food.get("calories", 0),
                "protein_g": food.get("protein_g", 0),
                "carbs_g": food.get("carbs_g", 0),
                "fat_g": food.get("fat_g", 0),
                "fiber_g": food.get("fiber_g", 0),
                "meal_type": food.get("meal_type", "any"),
                "suitability_score": self._calculate_food_suitability(food, profile),
                "why_recommended": self._explain_food_recommendation(food, profile),
                "nutritional_benefits": self._extract_nutritional_benefits(food, profile),
            }
            enhanced.append(enhanced_food)
        
        return enhanced
    
    def generate_complete_plan(self,
                              profile: dict[str, Any],
                              include_workout: bool = True,
                              include_nutrition: bool = True) -> dict[str, Any]:
        """
        Generate a complete personalized plan combining workout and nutrition.
        
        Args:
            profile: User profile
            include_workout: Include exercise recommendations
            include_nutrition: Include diet recommendations
            
        Returns:
            Complete personalized plan
        """
        # Get profile analysis from personalizer
        plan = self.personalizer.generate_personalized_plan(profile)
        
        # Add detailed recommendations
        detailed_plan = {
            "id": plan["id"],
            "user_id": plan["user_id"],
            "created_at": plan["created_at"],
            "analysis": plan["analysis"],
            "personalization_notes": plan["personalization_notes"],
            "recommendations": plan["recommendations"],
        }
        
        if include_workout:
            detailed_plan["workout"] = self._generate_detailed_workout_plan(profile, plan)
        
        if include_nutrition:
            detailed_plan["nutrition"] = self._generate_detailed_nutrition_plan(profile, plan)
        
        # Add performance expectations
        detailed_plan["expectations"] = self._generate_expectations(profile, plan)
        
        # Store for history/tracking
        self._store_recommendation(profile.get("id"), detailed_plan)
        
        return detailed_plan
    
    def _generate_detailed_workout_plan(self, profile: dict[str, Any], 
                                       base_plan: dict[str, Any]) -> dict[str, Any]:
        """Generate detailed workout plan with specific exercises."""
        exercises = self.get_personalized_exercises(profile, limit=50)
        
        return {
            "weekly_schedule": self._build_weekly_schedule(profile, exercises),
            "recommended_exercises": exercises[:20],
            "frequency_per_week": base_plan["recommendations"]["exercises"]["frequency_per_week"],
            "session_duration_minutes": base_plan["recommendations"]["exercises"]["duration_minutes"],
            "rest_days": base_plan["recommendations"]["lifestyle"]["rest_days_per_week"],
            "progression_plan": self._create_progression_plan(profile, exercises),
            "safety_notes": self._generate_safety_notes(profile, exercises),
        }
    
    def _generate_detailed_nutrition_plan(self, profile: dict[str, Any],
                                         base_plan: dict[str, Any]) -> dict[str, Any]:
        """Generate detailed nutrition plan with specific foods."""
        foods = self.get_personalized_foods(profile, limit=50)
        
        return {
            "daily_targets": base_plan["recommendations"]["nutrition"],
            "recommended_foods": foods[:30],
            "sample_meal_plans": self._generate_sample_meals(profile, foods),
            "shopping_list": self._generate_shopping_list(foods[:30]),
            "meal_prep_tips": self._generate_meal_prep_tips(profile),
            "hydration_plan": {
                "daily_target_liters": base_plan["recommendations"]["lifestyle"]["water_intake_liters"],
                "timing_tips": self._generate_hydration_timing(profile),
            }
        }
    
    def _build_weekly_schedule(self, profile: dict[str, Any],
                              exercises: list[dict[str, Any]]) -> dict[str, Any]:
        """Build a detailed weekly workout schedule."""
        goal = (profile.get("goal") or "").lower()
        days_per_week = int(profile.get("training_days_per_week") or 3)
        
        # Determine workout split based on goal and frequency
        if goal == "muscle_gain":
            if days_per_week == 3:
                split = ["Full Body", "Rest", "Full Body", "Rest", "Full Body", "Rest", "Rest"]
            elif days_per_week == 4:
                split = ["Upper", "Lower", "Rest", "Upper", "Lower", "Rest", "Rest"]
            else:
                split = ["Chest", "Back", "Legs", "Shoulders", "Rest", "Arms/Core", "Rest"]
        elif goal == "fat_loss":
            split = ["Cardio", "Strength", "Cardio", "Rest", "Strength", "Cardio", "Rest"]
        else:
            split = ["Full Body"] * days_per_week + ["Rest"] * (7 - days_per_week)
        
        schedule = {}
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        for i, day in enumerate(days):
            focus = split[i]
            if focus == "Rest":
                schedule[day] = {
                    "focus": "Rest & Recovery",
                    "exercises": [],
                    "notes": "Focus on active recovery, stretching, and meal prep",
                }
            else:
                # Get relevant exercises for this focus
                relevant = [ex for ex in exercises if focus.lower() in ex.get("muscle_group", "").lower()]
                if not relevant:
                    relevant = exercises[:5]
                
                schedule[day] = {
                    "focus": focus,
                    "exercises": relevant[:4],
                    "notes": f"Complete as circuits or traditional sets depending on preference",
                }
        
        return schedule
    
    def _create_progression_plan(self, profile: dict[str, Any],
                                exercises: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Create a progression plan for increasing intensity over time."""
        return [
            {
                "week": "Weeks 1-2",
                "focus": "Learning form and establishing baseline",
                "intensity": "50-60% of max rep range",
                "tips": "Focus on perfect form, start with lighter weights",
            },
            {
                "week": "Weeks 3-4",
                "focus": "Building base strength/endurance",
                "intensity": "60-70% of max",
                "tips": "Increase weight by 5-10%, maintain form",
            },
            {
                "week": "Weeks 5-8",
                "focus": "Progressive increase",
                "intensity": "70-85% of max",
                "tips": "Increase volume gradually, monitor recovery",
            },
            {
                "week": "Week 9+",
                "focus": "Plateauing? Adjust variables",
                "intensity": "Variable",
                "tips": "Change exercises, rep ranges, or rest periods",
            },
        ]
    
    def _generate_sample_meals(self, profile: dict[str, Any],
                              foods: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Generate sample meal combinations."""
        return [
            {
                "meal_type": "Breakfast",
                "options": [
                    {
                        "name": f"Option 1: {foods[0]['name'] if foods else 'Eggs'} with {foods[1]['name'] if len(foods) > 1 else 'toast'}",
                        "approximate_macros": {"protein_g": 25, "carbs_g": 40, "fat_g": 15},
                    },
                    {
                        "name": f"Option 2: Oatmeal with {foods[2]['name'] if len(foods) > 2 else 'nuts'}",
                        "approximate_macros": {"protein_g": 15, "carbs_g": 50, "fat_g": 10},
                    },
                ]
            },
            {
                "meal_type": "Lunch",
                "options": [
                    {
                        "name": f"Option 1: {foods[3]['name'] if len(foods) > 3 else 'Chicken'} with rice and {foods[4]['name'] if len(foods) > 4 else 'vegetables'}",
                        "approximate_macros": {"protein_g": 35, "carbs_g": 45, "fat_g": 12},
                    },
                ]
            },
            {
                "meal_type": "Dinner",
                "options": [
                    {
                        "name": f"Option 1: {foods[5]['name'] if len(foods) > 5 else 'Fish'} with sweet potato and vegetables",
                        "approximate_macros": {"protein_g": 30, "carbs_g": 40, "fat_g": 10},
                    },
                ]
            },
            {
                "meal_type": "Snacks",
                "options": [
                    {
                        "name": f"Option 1: {foods[6]['name'] if len(foods) > 6 else 'Greek yogurt'} with berries",
                        "approximate_macros": {"protein_g": 15, "carbs_g": 20, "fat_g": 3},
                    },
                ]
            },
        ]
    
    def _generate_shopping_list(self, foods: list[dict[str, Any]]) -> list[str]:
        """Generate a shopping list from recommended foods."""
        return [f.get("name") for f in foods[:20] if f.get("name")]
    
    def _generate_meal_prep_tips(self, profile: dict[str, Any]) -> list[str]:
        """Generate meal prep tips based on profile."""
        return [
            "Prepare proteins in bulk: grill multiple chicken breasts or cook fish",
            "Cook grains (rice, oats) in large batches for the week",
            "Chop vegetables ahead of time and store in containers",
            "Prepare sauce/dressing separately to keep meals fresh",
            "Use 4-6 meal prep containers for realistic macro targeting",
            "Cook one new recipe per week to stay motivated",
        ]
    
    def _generate_hydration_timing(self, profile: dict[str, Any]) -> list[str]:
        """Generate hydration timing recommendations."""
        return [
            "Upon waking: 500ml to rehydrate after sleep",
            "Pre-workout: 250-500ml 2-3 hours before exercise",
            "During workout: 200-300ml every 15-20 minutes",
            "Post-workout: 150% of fluid lost in sweat over next 4-6 hours",
            "With meals: 250ml with breakfast, lunch, and dinner",
            "Before bed: Small amount (200ml) to avoid sleep disruption",
        ]
    
    def _generate_expectations(self, profile: dict[str, Any],
                              base_plan: dict[str, Any]) -> dict[str, Any]:
        """Generate realistic expectations for progress."""
        goal = (profile.get("goal") or "").lower()
        timeline_weeks = int(profile.get("target_timeline_weeks") or 12)
        
        expectations = {
            "timeline_weeks": timeline_weeks,
            "realistic_outcomes": [],
            "factors_affecting_results": [],
            "when_to_adjust_plan": [],
        }
        
        if "muscle" in goal or "gain" in goal:
            expectations["realistic_outcomes"] = [
                f"Week 1-2: Expect water weight gain (2-3kg), neuromuscular adaptation",
                f"Week 3-4: First visible muscle gains, strength increases",
                f"Week 8: Noticeable muscle definition in mirror and photos",
                f"Week 12: {self._estimate_muscle_gain(profile)}kg of muscle expected",
            ]
            expectations["factors_affecting_results"] = [
                "Sleep quality (aim for 7-9 hours)",
                "Protein intake (target: "
                f"{base_plan['recommendations']['nutrition']['macro_targets']['protein_g']}g/day)",
                "Progressive overload in workouts",
                "Stress management and recovery",
            ]
        elif "fat" in goal or "loss" in goal:
            expectations["realistic_outcomes"] = [
                "Week 1: Initial water weight loss (1-2kg)",
                f"Week 4: Noticeable fat loss, similar or increased strength",
                f"Week 8: Clear visual progress, clothes fit better",
                f"Week 12: {self._estimate_fat_loss(profile)}kg of fat loss expected",
            ]
            expectations["factors_affecting_results"] = [
                "Consistent calorie deficit",
                "Protein intake to preserve muscle",
                "Consistency with workouts (80%+ adherence)",
                "Sleep and stress (poor sleep increases hunger)",
            ]
        
        expectations["when_to_adjust_plan"] = [
            "No progress after 3 weeks: Review calorie intake and workout form",
            "Plateau after 6 weeks: Change exercises or increase intensity",
            "Injury or pain: Modify exercises immediately",
            "Life changes: Adjust plan based on time/energy availability",
        ]
        
        return expectations
    
    def _estimate_muscle_gain(self, profile: dict[str, Any]) -> float:
        """Estimate realistic muscle gain potential."""
        fitness_level = (profile.get("fitness_level") or "").lower()
        weeks = int(profile.get("target_timeline_weeks") or 12)
        
        if "beginner" in fitness_level:
            return round(weeks * 0.5, 1)  # 0.5kg per week for beginners
        elif "advanced" in fitness_level:
            return round(weeks * 0.15, 1)  # 0.15kg per week for advanced
        return round(weeks * 0.3, 1)  # 0.3kg per week intermediate
    
    def _estimate_fat_loss(self, profile: dict[str, Any]) -> float:
        """Estimate realistic fat loss potential."""
        weeks = int(profile.get("target_timeline_weeks") or 12)
        return round(weeks * 0.5, 1)  # 0.5kg per week is realistic
    
    def _calculate_suitability_score(self, exercise: dict[str, Any],
                                     profile: dict[str, Any]) -> float:
        """Calculate how suitable an exercise is for the user (0-1)."""
        score = 0.5  # Base score
        
        # Match difficulty
        user_level = (profile.get("fitness_level") or "").lower()
        ex_difficulty = (exercise.get("difficulty") or "").lower()
        
        if user_level == "beginner" and "beginner" in ex_difficulty:
            score += 0.2
        elif user_level == "intermediate" and "intermediate" in ex_difficulty:
            score += 0.2
        elif user_level == "advanced" and "advanced" in ex_difficulty:
            score += 0.2
        
        # Match equipment
        available_eq = (profile.get("available_equipment") or "").lower()
        ex_eq = (exercise.get("equipment") or "").lower()
        
        if available_eq and ex_eq in available_eq:
            score += 0.15
        elif not available_eq and "bodyweight" in ex_eq:
            score += 0.15
        
        # Match goal
        goal = (profile.get("goal") or "").lower()
        muscle = (exercise.get("muscle_group") or "").lower()
        
        if "muscle" in goal and muscle in ["chest", "back", "shoulders", "arms"]:
            score += 0.15
        elif "fat" in goal and muscle in ["full body", "cardio", "core", "legs"]:
            score += 0.15
        
        return min(1.0, score)
    
    def _explain_recommendation(self, exercise: dict[str, Any],
                               profile: dict[str, Any]) -> str:
        """Explain why an exercise was recommended."""
        goal = (profile.get("goal") or "").lower()
        muscle = (exercise.get("muscle_group") or "").lower()
        
        explanations = []
        
        if "muscle" in goal:
            explanations.append(f"Targets {muscle} for muscle building")
        elif "fat" in goal:
            explanations.append(f"Engages {muscle} muscles for calorie burn")
        
        if "intermediate" in (profile.get("fitness_level") or "").lower():
            explanations.append("Appropriate difficulty level")
        
        return " - ".join(explanations) if explanations else "Matches your fitness profile"
    
    def _calculate_food_suitability(self, food: dict[str, Any],
                                   profile: dict[str, Any]) -> float:
        """Calculate how suitable a food is for the user (0-1)."""
        score = 0.5
        
        goal = (profile.get("goal") or "").lower()
        calories = food.get("calories", 0)
        protein = food.get("protein_g", 0)
        
        # Score based on goal macros
        if "muscle" in goal and protein > 15:
            score += 0.25
        elif "fat" in goal and calories < 150:
            score += 0.25
        
        # Check for allergies
        allergies = (profile.get("allergies") or "").lower()
        if allergies and allergies in (food.get("name") or "").lower():
            score -= 0.5
        
        # Check dietary preferences
        preferences = (profile.get("dietary_preferences") or "").lower()
        food_name = (food.get("name") or "").lower()
        
        if preferences and preferences not in food_name:
            score += 0.15
        
        return max(0.0, min(1.0, score))
    
    def _explain_food_recommendation(self, food: dict[str, Any],
                                    profile: dict[str, Any]) -> str:
        """Explain why a food was recommended."""
        explanations = []
        
        goal = (profile.get("goal") or "").lower()
        protein = food.get("protein_g", 0)
        calories = food.get("calories", 0)
        fiber = food.get("fiber_g", 0)
        
        if "muscle" in goal and protein > 15:
            explanations.append(f"High protein ({protein}g) for muscle building")
        
        if "fat" in goal and calories < 150:
            explanations.append(f"Low calorie ({calories}kcal) for fat loss")
        
        if fiber > 5:
            explanations.append("High in fiber for satiety")
        
        return " - ".join(explanations) if explanations else "Fits your nutritional goals"
    
    def _extract_nutritional_benefits(self, food: dict[str, Any],
                                     profile: dict[str, Any]) -> list[str]:
        """Extract nutritional benefits of a food."""
        benefits = []
        
        protein = food.get("protein_g", 0)
        carbs = food.get("carbs_g", 0)
        fat = food.get("fat_g", 0)
        fiber = food.get("fiber_g", 0)
        
        if protein > 15:
            benefits.append(f"Excellent protein source ({protein}g per serving)")
        if carbs > 20:
            benefits.append(f"Good carb source ({carbs}g) for energy")
        if fiber > 5:
            benefits.append(f"High fiber ({fiber}g) for digestion")
        if fat > 0 and fat < 10:
            benefits.append("Healthy fats in balanced amount")
        
        return benefits if benefits else ["Wholesome nutrition"]
    
    def _generate_safety_notes(self, profile: dict[str, Any],
                              exercises: list[dict[str, Any]]) -> list[str]:
        """Generate safety notes for exercises."""
        notes = []
        
        injuries = (profile.get("injuries") or "").split(",")
        injuries = [i.strip() for i in injuries if i.strip()]
        
        if injuries:
            notes.append(f"Important: You have history of {', '.join(injuries)} - modify exercises as needed")
        
        if (profile.get("fitness_level") or "").lower() == "beginner":
            notes.append("Learn proper form from videos or trainer before attempting")
        
        notes.append("Stop immediately if you feel sharp pain (not muscle soreness)")
        notes.append("Warm up for 5-10 minutes before starting exercises")
        notes.append("Cool down and stretch for 5-10 minutes after finishing")
        
        return notes
    
    def _store_recommendation(self, user_id: str, plan: dict[str, Any]) -> None:
        """Store recommendation in history for tracking."""
        if not user_id:
            return
        
        if user_id not in self.recommendation_history:
            self.recommendation_history[user_id] = []
        
        self.recommendation_history[user_id].append({
            "created_at": datetime.now().isoformat(),
            "plan_id": plan.get("id"),
        })


if __name__ == "__main__":
    from training_engine import TrainingEngine
    from personalization_engine import PersonalizationEngine
    from multi_dataset_loader import MultiDatasetLoader
    from dataset_paths import resolve_dataset_root
    import json
    
    # Example usage
    root = resolve_dataset_root()
    loader = MultiDatasetLoader(root)
    loader.load_all()
    
    training_engine = TrainingEngine(loader)
    training_engine.train()
    
    personalizer = PersonalizationEngine(training_engine)
    
    enhanced = EnhancedRecommendationEngine(
        training_engine, 
        personalizer,
        None  # original recommender
    )
    
    # Example user profile
    profile = {
        "id": "user_123",
        "weight": 85,
        "height": 180,
        "age": 30,
        "gender": "male",
        "goal": "fat_loss",
        "fitness_level": "intermediate",
        "chronic_diseases": "diabetes",
        "allergies": "peanut",
        "available_equipment": "dumbbell,kettlebell",
        "training_days_per_week": 4,
        "target_weight": 75,
        "target_timeline_weeks": 12,
    }
    
    # Generate complete personalized plan
    plan = enhanced.generate_complete_plan(profile)
    
    print("\n=== Complete Personalized Plan ===")
    print(json.dumps(plan, indent=2, default=str)[:2000] + "...\n[Plan continues...]")
