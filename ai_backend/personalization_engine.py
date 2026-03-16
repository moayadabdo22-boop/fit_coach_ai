"""
Personalization Engine for AI Coach

Matches user profiles to training data for maximum personalization:
- Profile analysis (weight, height, health conditions, goals)
- Dataset pattern matching
- Personalized plan generation
- Performance tracking integration
"""

from __future__ import annotations

from typing import Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class PersonalizationEngine:
    """
    Personalizes recommendations based on user profile and training data.
    """
    
    def __init__(self, training_engine):
        """
        Initialize with trained model.
        
        Args:
            training_engine: TrainingEngine instance with trained models
        """
        self.engine = training_engine
    
    def analyze_user_profile(self, profile: dict[str, Any]) -> dict[str, Any]:
        """
        Analyze user profile for personalization.
        
        Args:
            profile: User profile dictionary
            
        Returns:
            Analysis results with recommendations
        """
        analysis = {
            "user_id": profile.get("id") or profile.get("user_id"),
            "profile_analysis": self._analyze_physical_metrics(profile),
            "health_profile": self._analyze_health_status(profile),
            "goal_analysis": self._analyze_goals(profile),
            "fitness_level": self._assess_fitness_level(profile),
            "personalization_factors": self._extract_personalization_factors(profile),
        }
        
        return analysis
    
    def _analyze_physical_metrics(self, profile: dict[str, Any]) -> dict[str, Any]:
        """Analyze physical metrics (height, weight, etc.)."""
        weight_kg = float(profile.get("weight") or profile.get("weight_kg") or 70)
        height_cm = float(profile.get("height") or profile.get("height_cm") or 170)
        age = int(profile.get("age") or 30)
        gender = (profile.get("gender") or "").lower()
        
        # Calculate BMI
        bmi = weight_kg / ((height_cm / 100) ** 2)
        bmi_category = self._categorize_bmi(bmi)
        
        # Estimate daily calorie needs
        tdee = self._estimate_tdee(weight_kg, height_cm, age, gender, profile.get("activity_level"))
        
        return {
            "weight_kg": weight_kg,
            "height_cm": height_cm,
            "age": age,
            "gender": gender,
            "bmi": round(bmi, 1),
            "bmi_category": bmi_category,
            "estimated_tdee": tdee,
            "fitness_assessment": self._assess_current_fitness(profile),
        }
    
    def _categorize_bmi(self, bmi: float) -> str:
        """Categorize BMI value."""
        if bmi < 18.5:
            return "underweight"
        elif bmi < 25:
            return "normal"
        elif bmi < 30:
            return "overweight"
        elif bmi < 35:
            return "obese_class_1"
        else:
            return "obese_class_2"
    
    def _estimate_tdee(self, weight_kg: float, height_cm: float, age: int, 
                       gender: str, activity_level: str | None) -> int:
        """Estimate Total Daily Energy Expenditure using Mifflin-St Jeor equation."""
        # Base metabolic rate
        if gender == "male" or gender == "m":
            bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
        else:
            bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161
        
        # Activity multiplier
        activity_map = {
            "sedentary": 1.2,
            "light": 1.375,
            "moderate": 1.55,
            "active": 1.725,
            "very_active": 1.9,
        }
        
        multiplier = activity_map.get((activity_level or "").lower(), 1.55)
        
        return int(bmr * multiplier)
    
    def _assess_current_fitness(self, profile: dict[str, Any]) -> dict[str, Any]:
        """Assess current fitness level from available data."""
        # Check for progress data
        progress_data = profile.get("progress_history", [])
        
        assessment = {
            "has_baseline": bool(profile.get("baseline_fitness")),
            "tracking_duration_days": 0,
            "workout_frequency": profile.get("training_days_per_week") or 3,
        }
        
        if progress_data:
            assessment["tracking_duration_days"] = len(progress_data)
            assessment["consistency_score"] = self._calculate_consistency(progress_data)
        
        return assessment
    
    def _calculate_consistency(self, progress_history: list[dict[str, Any]]) -> float:
        """Calculate workout consistency score (0-1)."""
        if not progress_history:
            return 0.0
        
        completed = sum(1 for p in progress_history if p.get("completed"))
        return min(1.0, completed / len(progress_history))
    
    def _analyze_health_status(self, profile: dict[str, Any]) -> dict[str, Any]:
        """Analyze health conditions and restrictions."""
        chronic_diseases = (profile.get("chronic_diseases") or "").split(",")
        chronic_diseases = [d.strip() for d in chronic_diseases if d.strip()]
        
        allergies = (profile.get("allergies") or "").split(",")
        allergies = [a.strip() for a in allergies if a.strip()]
        
        dietary_preferences = (profile.get("dietary_preferences") or "").split(",")
        dietary_preferences = [d.strip() for d in dietary_preferences if d.strip()]
        
        # Use training engine to get restrictions
        restrictions = {}
        if chronic_diseases:
            restrictions = self.engine.analyze_health_restrictions(chronic_diseases)
        
        return {
            "chronic_diseases": chronic_diseases,
            "allergies": allergies,
            "dietary_preferences": dietary_preferences,
            "food_restrictions": restrictions.get("avoid_foods", []),
            "preferred_foods": restrictions.get("prefer_foods", []),
            "macro_targets": restrictions.get("macro_targets", {}),
            "has_restrictions": bool(chronic_diseases or allergies),
        }
    
    def _analyze_goals(self, profile: dict[str, Any]) -> dict[str, Any]:
        """Analyze user goals and targets."""
        goal = (profile.get("goal") or "").strip().lower()
        target_weight = float(profile.get("target_weight") or 0)
        timeline_weeks = int(profile.get("target_timeline_weeks") or 12)
        
        current_weight = float(profile.get("weight") or 70)
        weight_change = target_weight - current_weight if target_weight else 0
        weekly_change = weight_change / timeline_weeks if timeline_weeks else 0
        
        return {
            "primary_goal": self._normalize_goal(goal),
            "target_weight_kg": target_weight if target_weight else None,
            "current_weight_kg": current_weight,
            "weight_change_kg": weight_change if weight_change else None,
            "timeline_weeks": timeline_weeks,
            "weekly_target_change_kg": round(weekly_change, 2) if weekly_change else None,
            "specific_objectives": (profile.get("specific_objectives") or "").split(","),
        }
    
    def _normalize_goal(self, goal: str) -> str:
        """Normalize goal names."""
        if "muscle" in goal or "gain" in goal or "bulk" in goal:
            return "muscle_gain"
        elif "fat" in goal or "loss" in goal or "cut" in goal or "weight" in goal:
            return "fat_loss"
        elif "endurance" in goal or "cardio" in goal:
            return "endurance"
        return "general_fitness"
    
    def _assess_fitness_level(self, profile: dict[str, Any]) -> str:
        """Assess fitness level."""
        level = (profile.get("fitness_level") or "").strip().lower()
        
        if "beginner" in level or "novice" in level:
            return "beginner"
        elif "advanced" in level or "expert" in level:
            return "advanced"
        return "intermediate"
    
    def _extract_personalization_factors(self, profile: dict[str, Any]) -> dict[str, Any]:
        """Extract key factors for personalization."""
        return {
            "available_equipment": (profile.get("available_equipment") or "").split(","),
            "preferred_workout_type": (profile.get("workout_preference") or "").lower(),
            "sessions_per_week": int(profile.get("training_days_per_week") or 3),
            "session_duration_minutes": int(profile.get("session_duration") or 45),
            "injury_history": (profile.get("injuries") or "").split(","),
            "timezone": profile.get("timezone", "UTC"),
            "language": profile.get("language", "en"),
        }
    
    def generate_personalized_plan(self, 
                                   profile: dict[str, Any],
                                   plan_type: str = "weekly") -> dict[str, Any]:
        """
        Generate personalized plan based on profile analysis.
        
        Args:
            profile: User profile
            plan_type: "weekly", "biweekly", "monthly"
            
        Returns:
            Personalized plan tailored to user
        """
        analysis = self.analyze_user_profile(profile)
        
        plan = {
            "id": f"{profile.get('id')}-{datetime.now().isoformat()}",
            "user_id": profile.get("id") or profile.get("user_id"),
            "plan_type": plan_type,
            "created_at": datetime.now().isoformat(),
            "analysis": analysis,
            "recommendations": self._generate_recommendations(profile, analysis),
            "personalization_notes": self._generate_personalization_notes(profile, analysis),
        }
        
        return plan
    
    def _generate_recommendations(self, profile: dict[str, Any], 
                                  analysis: dict[str, Any]) -> dict[str, Any]:
        """Generate specific recommendations based on analysis."""
        goal = analysis["goal_analysis"]["primary_goal"]
        fitness_level = analysis["fitness_level"]
        
        # Get exercise recommendations from training engine
        exercise_profile = {
            "goal": goal,
            "fitness_level": fitness_level,
            "available_equipment": profile.get("available_equipment", ""),
        }
        
        exercises = self.engine.get_recommended_exercises(exercise_profile, limit=20)
        
        # Get food recommendations from training engine
        food_profile = {
            "goal": goal,
            "calorie_target": analysis["profile_analysis"].get("estimated_tdee"),
            "allergies": profile.get("allergies", ""),
            "dietary_preferences": profile.get("dietary_preferences", ""),
        }
        
        foods = self.engine.get_recommended_foods(food_profile, limit=30)
        
        # Calculate macro targets
        macro_targets = self._calculate_macro_targets(profile, analysis)
        
        return {
            "exercises": {
                "recommended": exercises[:10],
                "total_available": len(exercises),
                "frequency_per_week": analysis["personalization_factors"]["sessions_per_week"],
                "duration_minutes": analysis["personalization_factors"]["session_duration_minutes"],
            },
            "nutrition": {
                "recommended_foods": foods[:20],
                "total_available": len(foods),
                "calorie_target": analysis["profile_analysis"].get("estimated_tdee"),
                "macro_targets": macro_targets,
                "meal_frequency": self._recommend_meal_frequency(profile),
            },
            "lifestyle": {
                "sleep_target_hours": self._recommend_sleep(analysis),
                "water_intake_liters": self._recommend_hydration(analysis["profile_analysis"]["weight_kg"]),
                "rest_days_per_week": 7 - analysis["personalization_factors"]["sessions_per_week"],
            },
            "monitoring": {
                "track_metrics": self._recommend_metrics(goal, analysis),
                "check_in_frequency": "weekly",
                "monthly_goals": self._generate_monthly_goals(goal, analysis),
            }
        }
    
    def _calculate_macro_targets(self, profile: dict[str, Any], 
                                analysis: dict[str, Any]) -> dict[str, float]:
        """Calculate personalized macro targets."""
        goal = analysis["goal_analysis"]["primary_goal"]
        tdee = analysis["profile_analysis"]["estimated_tdee"]
        weight_kg = analysis["profile_analysis"]["weight_kg"]
        
        # Adjust macros based on goal
        if goal == "muscle_gain":
            protein_per_kg = 2.2
            carb_ratio = 0.40
            fat_ratio = 0.25
        elif goal == "fat_loss":
            protein_per_kg = 2.5
            carb_ratio = 0.35
            fat_ratio = 0.30
        else:  # general_fitness or endurance
            protein_per_kg = 1.8
            carb_ratio = 0.45
            fat_ratio = 0.25
        
        # Calculate in grams
        protein_g = weight_kg * protein_per_kg
        fat_g = (tdee * fat_ratio) / 9
        carbs_g = (tdee * carb_ratio) / 4
        
        return {
            "protein_g": round(protein_g, 1),
            "carbs_g": round(carbs_g, 1),
            "fat_g": round(fat_g, 1),
            "fiber_g": 25 if analysis["profile_analysis"]["gender"] == "female" else 38,
        }
    
    def _recommend_meal_frequency(self, profile: dict[str, Any]) -> int:
        """Recommend meal frequency based on profile."""
        # More frequent meals for muscle gain, fewer for fat loss
        goal = (profile.get("goal") or "").lower()
        
        if "muscle" in goal or "gain" in goal:
            return 5
        elif "fat" in goal or "loss" in goal:
            return 3
        return 4
    
    def _recommend_sleep(self, analysis: dict[str, Any]) -> int:
        """Recommend sleep duration."""
        goal = analysis["goal_analysis"]["primary_goal"]
        
        if goal == "muscle_gain":
            return 8
        elif goal == "fat_loss":
            return 7
        return 7
    
    def _recommend_hydration(self, weight_kg: float) -> float:
        """Calculate recommended daily water intake."""
        # General rule: 35ml per kg of body weight
        return round(weight_kg * 35 / 1000, 1)
    
    def _recommend_metrics(self, goal: str, analysis: dict[str, Any]) -> dict[str, list[str]]:
        """Recommend which metrics to track based on goal."""
        metrics = {
            "weekly": ["weight", "energy_level", "workout_compliance"],
            "monthly": ["body_measurements", "progress_photos"],
            "biweekly": ["performance_metrics"],
        }
        
        # Add goal-specific metrics
        if goal == "muscle_gain":
            metrics["weekly"].extend(["strength_gains", "recovery"])
        elif goal == "fat_loss":
            metrics["weekly"].extend(["calorie_adherence", "activity_level"])
        else:
            metrics["weekly"].extend(["endurance_improvements"])
        
        return metrics
    
    def _generate_monthly_goals(self, goal: str, analysis: dict[str, Any]) -> list[dict[str, Any]]:
        """Generate monthly objectives."""
        weight_change = analysis["goal_analysis"]["weekly_target_change_kg"]
        
        return [
            {
                "month": "Month 1",
                "focus": "Establish routine and baseline",
                "targets": {
                    "consistency": "80%+ workout adherence",
                    "nutrition": "Hit macros 5 days/week minimum",
                    "weight_change_kg": weight_change * 4 if weight_change else 0,
                }
            },
            {
                "month": "Month 2-3",
                "focus": "Progressive improvement",
                "targets": {
                    "consistency": "90%+ workout adherence",
                    "nutrition": "Hit macros 6 days/week minimum",
                    "weight_change_kg": weight_change * 8 if weight_change else 0,
                }
            },
        ]
    
    def _generate_personalization_notes(self, profile: dict[str, Any], 
                                       analysis: dict[str, Any]) -> list[str]:
        """Generate personalization notes explaining the recommendations."""
        notes = []
        
        # Physical metrics notes
        bmi_cat = analysis["profile_analysis"]["bmi_category"]
        if bmi_cat != "normal":
            notes.append(f"Your BMI ({analysis['profile_analysis']['bmi']}) is in the {bmi_cat} range - this plan accounts for this.")
        
        # Health condition notes
        if analysis["health_profile"]["has_restrictions"]:
            diseases = analysis["health_profile"]["chronic_diseases"]
            notes.append(f"Plan avoids foods problematic for your conditions: {', '.join(diseases)}")
        
        # Goal-specific notes
        goal = analysis["goal_analysis"]["primary_goal"]
        if goal == "muscle_gain":
            notes.append("High protein approach selected for muscle building")
        elif goal == "fat_loss":
            notes.append("Moderate calorie deficit with high protein to preserve muscle")
        
        # Fitness level notes
        level = analysis["fitness_level"]
        if level == "beginner":
            notes.append("Beginner-friendly exercises selected - focus on form and consistency")
        elif level == "advanced":
            notes.append("Advanced training selected with higher intensity and volume")
        
        # Equipment notes
        equipment = analysis["personalization_factors"]["available_equipment"]
        if equipment:
            notes.append(f"Plan uses available equipment: {', '.join([e for e in equipment if e])}")
        
        return notes


if __name__ == "__main__":
    from training_engine import TrainingEngine
    from multi_dataset_loader import MultiDatasetLoader
    from dataset_paths import resolve_dataset_root
    import json
    
    # Example usage
    root = resolve_dataset_root()
    loader = MultiDatasetLoader(root)
    loader.load_all()
    
    engine = TrainingEngine(loader)
    engine.train()
    
    personalizer = PersonalizationEngine(engine)
    
    # Example user profile
    profile = {
        "id": "user_123",
        "weight": 85,
        "weight_kg": 85,
        "height": 180,
        "height_cm": 180,
        "age": 30,
        "gender": "male",
        "goal": "fat_loss",
        "fitness_level": "intermediate",
        "chronic_diseases": "diabetes",
        "allergies": "peanut",
        "dietary_preferences": "no beef",
        "available_equipment": "dumbbell,kettlebell",
        "training_days_per_week": 4,
        "target_weight": 75,
        "target_timeline_weeks": 12,
    }
    
    # Generate personalized plan
    plan = personalizer.generate_personalized_plan(profile)
    
    print("\n=== Personalized Plan ===")
    print(json.dumps(plan, indent=2, default=str)[:1000] + "...")
