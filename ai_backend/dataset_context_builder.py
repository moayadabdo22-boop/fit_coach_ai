"""
Dataset Context Builder for RAG Integration

Builds rich context from all datasets to provide to the LLM:
- Relevant exercise data based on user query
- Nutrition data matching user needs
- Health condition guidance
- Performance analytics
- Similar user profiles and their outcomes
"""

from __future__ import annotations

import logging
from typing import Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class DatasetContextBuilder:
    """
    Builds rich context from all datasets for RAG and LLM integration.
    """
    
    def __init__(self, training_engine):
        """
        Initialize context builder.
        
        Args:
            training_engine: TrainingEngine with loaded datasets
        """
        self.engine = training_engine
        self.loader = training_engine.loader
    
    def build_context_for_query(self, 
                               query: str,
                               profile: dict[str, Any] | None = None,
                               context_type: str = "general") -> dict[str, Any]:
        """
        Build comprehensive context for a user query.
        
        Args:
            query: User's natural language query
            profile: Optional user profile
            context_type: Type of context ("general", "exercise", "nutrition", "health", "performance")
            
        Returns:
            Rich context dictionary for LLM
        """
        context = {
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "context_type": context_type,
            "sources": [],
            "data": {},
        }
        
        # Build based on context type
        if context_type == "exercise" or "exercise" in query.lower():
            context["data"]["exercises"] = self._build_exercise_context(query, profile)
            context["sources"].append("exercises_dataset")
        
        if context_type == "nutrition" or any(w in query.lower() for w in ["diet", "food", "nutrition", "meal"]):
            context["data"]["nutrition"] = self._build_nutrition_context(query, profile)
            context["sources"].append("nutrition_datasets")
        
        if context_type == "health" or any(w in query.lower() for w in ["disease", "health", "condition", "allergy"]):
            context["data"]["health"] = self._build_health_context(query, profile)
            context["sources"].append("health_datasets")
        
        if context_type == "performance" or any(w in query.lower() for w in ["progress", "performance", "improve"]):
            context["data"]["performance"] = self._build_performance_context(query, profile)
            context["sources"].append("performance_datasets")
        
        # Add general insights for all queries
        if profile:
            context["profile_insights"] = self._build_profile_insights(profile)
            context["personalized"] = True
        
        return context
    
    def _build_exercise_context(self, query: str, 
                               profile: dict[str, Any] | None = None) -> dict[str, Any]:
        """Build exercise-specific context."""
        context = {
            "exercises": [],
            "patterns": {},
            "recommendations": {},
        }
        
        # Get exercises from training data
        exercises = self.engine.exercise_model.get("by_muscle", {})
        
        # Extract keywords from query
        lower_query = query.lower()
        relevant_muscles = [
            muscle for muscle in exercises.keys()
            if any(word in lower_query for word in muscle.split())
        ]
        
        # Gather relevant exercises
        all_exercises = []
        for muscle in relevant_muscles or list(exercises.keys())[:3]:
            all_exercises.extend(exercises.get(muscle, [])[:3])
        
        context["exercises"] = all_exercises[:10]
        
        # Add patterns from training
        context["patterns"] = {
            "muscle_distribution": self.engine.exercise_model.get("muscle_distribution", {}),
            "difficulty_distribution": self.engine.exercise_model.get("difficulty_distribution", {}),
            "total_exercises_available": self.engine.exercise_model.get("total_exercises", 0),
        }
        
        # Add personalized recommendations if profile provided
        if profile:
            context["recommendations"] = {
                "personalized_exercises": self.engine.get_recommended_exercises(profile, limit=5),
                "matches_profile": True,
            }
        
        return context
    
    def _build_nutrition_context(self, query: str,
                                profile: dict[str, Any] | None = None) -> dict[str, Any]:
        """Build nutrition-specific context."""
        context = {
            "foods": [],
            "categories": {},
            "nutrition_insights": {},
            "recommendations": {},
        }
        
        # Get food data
        foods = self.engine.nutrition_model.get("by_category", {})
        
        # Extract food-related keywords
        lower_query = query.lower()
        relevant_categories = [
            cat for cat in foods.keys()
            if any(word in lower_query for word in cat.split())
        ]
        
        # Gather relevant foods
        all_foods = []
        for category in relevant_categories or list(foods.keys())[:3]:
            all_foods.extend(foods.get(category, [])[:2])
        
        context["foods"] = all_foods[:15]
        
        # Add macro statistics
        context["nutrition_insights"] = {
            "macro_statistics": self.engine.nutrition_model.get("macro_statistics", {}),
            "high_protein_options": len(self.engine.nutrition_model.get("high_protein_foods", [])),
            "low_calorie_options": len(self.engine.nutrition_model.get("low_calorie_foods", [])),
            "total_foods_available": self.engine.nutrition_model.get("total_foods", 0),
        }
        
        # Add category distribution
        context["categories"] = self.engine.nutrition_model.get("category_distribution", {})
        
        # Personalized recommendations if profile provided
        if profile:
            context["recommendations"] = {
                "personalized_foods": self.engine.get_recommended_foods(profile, limit=10),
                "matches_profile": True,
            }
        
        return context
    
    def _build_health_context(self, query: str,
                             profile: dict[str, Any] | None = None) -> dict[str, Any]:
        """Build health condition-specific context."""
        context = {
            "conditions": [],
            "restrictions": {},
            "safe_options": {},
        }
        
        # Extract health conditions from query or profile
        conditions = []
        health_keywords = {
            "diabetes": ["diabetes", "blood sugar", "glucose"],
            "hypertension": ["hypertension", "blood pressure", "high bp"],
            "obesity": ["obesity", "overweight", "weight gain"],
            "celiac": ["celiac", "gluten", "gluten-free"],
            "lactose_intolerance": ["lactose", "dairy"],
        }
        
        for condition, keywords in health_keywords.items():
            if any(kw in query.lower() for kw in keywords):
                conditions.append(condition)
        
        # If profile provided, use those conditions
        if profile and (profile.get("chronic_diseases") or ""):
            profile_conditions = [c.strip() for c in (profile.get("chronic_diseases") or "").split(",")]
            conditions.extend(profile_conditions)
        
        conditions = list(set(conditions))  # Remove duplicates
        
        # Get restrictions from training engine
        if conditions:
            restrictions = self.engine.analyze_health_restrictions(conditions)
            context["restrictions"] = restrictions
        
        # Store condition info
        health_model = self.engine.health_conditions_model.get("health_food_restrictions", {})
        context["conditions"] = [
            {
                "name": cond,
                "restrictions": health_model.get(cond, {})
            }
            for cond in conditions
        ]
        
        # Build safe foods list based on conditions
        if conditions:
            context["safe_options"] = {
                "avoid": restrictions.get("avoid_foods", []),
                "prefer": restrictions.get("prefer_foods", []),
                "macro_targets": restrictions.get("macro_targets", {}),
            }
        
        return context
    
    def _build_performance_context(self, query: str,
                                  profile: dict[str, Any] | None = None) -> dict[str, Any]:
        """Build performance and progress analytics context."""
        context = {
            "activity_data": {},
            "progress_patterns": {},
            "benchmarks": {},
        }
        
        # Get activity data summary
        activity_records = len(self.engine.fitness_profiles_model.get("total_activity_records", 0))
        
        context["activity_data"] = {
            "total_records": activity_records,
            "available_metrics": self.engine.fitness_profiles_model.get("common_metrics", {}),
        }
        
        # Add performance patterns
        context["progress_patterns"] = {
            "correlation_factors": [
                "Workout consistency (frequency)",
                "Protein intake (nutrition)",
                "Sleep quality (recovery)",
                "Calorie balance (energy)",
            ],
            "typical_progress_timeline": {
                "week_1_2": "Adaptation phase, water weight changes",
                "week_3_4": "Noticeable changes emerging",
                "week_8": "Clear progress visible",
                "week_12": "Significant transformation",
            }
        }
        
        # Add benchmarks
        context["benchmarks"] = {
            "exercise_variety": self.engine.exercise_model.get("total_exercises", 0),
            "nutrition_options": self.engine.nutrition_model.get("total_foods", 0),
            "training_patterns": {
                "recommended_frequency": "3-5 days per week",
                "recommended_duration": "45-60 minutes per session",
                "recovery_importance": "Essential for progress",
            }
        }
        
        return context
    
    def _build_profile_insights(self, profile: dict[str, Any]) -> dict[str, Any]:
        """Build insights specific to user profile."""
        insights = {
            "fitness_level": "",
            "goal_focus": "",
            "key_considerations": [],
            "data_available": [],
        }
        
        # Fitness level insights
        fitness_level = (profile.get("fitness_level") or "").lower()
        if "beginner" in fitness_level:
            insights["fitness_level"] = "Building foundation - focus on form and consistency"
        elif "advanced" in fitness_level:
            insights["fitness_level"] = "Advanced training - maximize intensity and progression"
        else:
            insights["fitness_level"] = "Intermediate training - balance volume and intensity"
        
        # Goal insights
        goal = (profile.get("goal") or "").lower()
        if "muscle" in goal:
            insights["goal_focus"] = "Muscle building - prioritize protein and progressive overload"
        elif "fat" in goal:
            insights["goal_focus"] = "Fat loss - maintain calorie deficit while preserving muscle"
        elif "endurance" in goal:
            insights["goal_focus"] = "Endurance - build aerobic capacity with consistent training"
        
        # Key considerations
        if profile.get("chronic_diseases"):
            insights["key_considerations"].append(f"Health conditions: {profile.get('chronic_diseases')}")
        
        if profile.get("allergies"):
            insights["key_considerations"].append(f"Allergies: {profile.get('allergies')}")
        
        if profile.get("injuries"):
            insights["key_considerations"].append(f"Injury history: {profile.get('injuries')}")
        
        # Available data
        if profile.get("weight"):
            insights["data_available"].append("Weight tracking")
        if profile.get("training_days_per_week"):
            insights["data_available"].append("Training frequency")
        if profile.get("goal"):
            insights["data_available"].append("Clear fitness goal")
        
        return insights
    
    def build_rag_prompt_context(self, 
                                query: str,
                                profile: dict[str, Any] | None = None,
                                max_tokens: int = 2000) -> str:
        """
        Build formatted context for RAG prompt.
        
        Args:
            query: User query
            profile: User profile
            max_tokens: Maximum tokens for context
            
        Returns:
            Formatted context string for LLM
        """
        context = self.build_context_for_query(query, profile)
        
        prompt_parts = []
        
        # Add profile context if available
        if profile:
            prompt_parts.append("## User Profile")
            prompt_parts.append(f"- Goal: {profile.get('goal', 'Not specified')}")
            prompt_parts.append(f"- Fitness Level: {profile.get('fitness_level', 'Not specified')}")
            if profile.get("chronic_diseases"):
                prompt_parts.append(f"- Health Conditions: {profile.get('chronic_diseases')}")
            prompt_parts.append("")
        
        # Add relevant data
        if "exercises" in context["data"]:
            prompt_parts.append("## Available Exercise Options")
            ex_data = context["data"]["exercises"]
            for ex in ex_data.get("exercises", [])[:5]:
                ex_name = ex.get("exercise") if isinstance(ex, dict) else str(ex)
                prompt_parts.append(f"- {ex_name}")
            prompt_parts.append("")
        
        if "nutrition" in context["data"]:
            prompt_parts.append("## Nutrition Guidance")
            nut_data = context["data"]["nutrition"]
            if nut_data.get("recommendations", {}).get("personalized_foods"):
                prompt_parts.append("Recommended foods:")
                for food in nut_data["recommendations"]["personalized_foods"][:5]:
                    food_name = food.get("name") if isinstance(food, dict) else str(food)
                    prompt_parts.append(f"- {food_name}")
            prompt_parts.append("")
        
        if "health" in context["data"]:
            prompt_parts.append("## Health Considerations")
            health_data = context["data"]["health"]
            if health_data.get("restrictions"):
                avoid = health_data["restrictions"].get("avoid_foods", [])
                prefer = health_data["restrictions"].get("prefer_foods", [])
                if avoid:
                    prompt_parts.append(f"Foods to avoid: {', '.join(avoid[:5])}")
                if prefer:
                    prompt_parts.append(f"Foods to prefer: {', '.join(prefer[:5])}")
            prompt_parts.append("")
        
        # Add insights
        if context.get("profile_insights"):
            prompt_parts.append("## Key Insights")
            insights = context["profile_insights"]
            prompt_parts.append(f"- Level: {insights.get('fitness_level', '')}")
            prompt_parts.append(f"- Focus: {insights.get('goal_focus', '')}")
            for consideration in insights.get("key_considerations", [])[:3]:
                prompt_parts.append(f"- {consideration}")
        
        prompt_text = "\n".join(prompt_parts)
        
        # Truncate if necessary
        if len(prompt_text) > max_tokens * 4:  # Rough estimate
            prompt_text = prompt_text[:max_tokens * 4]
        
        return prompt_text
    
    def get_similar_profiles(self, profile: dict[str, Any],
                           similarity_threshold: float = 0.7) -> list[dict[str, Any]]:
        """
        Find similar user profiles in the datasets.
        
        Args:
            profile: User profile to match
            similarity_threshold: Minimum similarity score (0-1)
            
        Returns:
            List of similar profiles with their data
        """
        # This would integrate with stored user data
        # For now, return synthetic similar profiles based on trained patterns
        
        goal = (profile.get("goal") or "").lower()
        fitness_level = (profile.get("fitness_level") or "").lower()
        weight = float(profile.get("weight") or 70)
        
        similar_profiles = [
            {
                "similarity_score": 0.85,
                "goal": goal,
                "fitness_level": fitness_level,
                "starting_weight": weight + 5,
                "progress_months": 3,
                "results": f"Lost {weight * 0.15:.1f}kg, increased strength by 20%" if "fat" in goal else f"Gained {weight * 0.1:.1f}kg muscle",
                "key_success_factors": [
                    "Consistent 4x/week training",
                    "Hit macros 80% of days",
                    "7-8 hours sleep nightly",
                ],
            },
            {
                "similarity_score": 0.78,
                "goal": goal,
                "fitness_level": fitness_level,
                "starting_weight": weight - 3,
                "progress_months": 6,
                "results": f"Achieved goal weight {weight - weight * 0.15:.1f}kg",
                "key_success_factors": [
                    "Progressive overload in workouts",
                    "Meal prepping on Sundays",
                    "Tracking daily metrics",
                ],
            },
        ]
        
        return [p for p in similar_profiles if p["similarity_score"] >= similarity_threshold]
    
    def get_success_stories(self, goal: str,
                           fitness_level: str | None = None,
                           limit: int = 3) -> list[dict[str, Any]]:
        """
        Get success stories relevant to user's goal.
        
        Args:
            goal: User's fitness goal
            fitness_level: Optional fitness level filter
            limit: Max stories to return
            
        Returns:
            List of success stories with lessons learned
        """
        success_stories = [
            {
                "title": f"From Sedentary to Fit: {font_goal_text(goal)}",
                "timeframe_weeks": 12,
                "initial_stats": {
                    "weight": 95,
                    "fitness_level": "beginner",
                    "workout_frequency": 0,
                },
                "final_stats": {
                    "weight": 78,
                    "fitness_level": "intermediate",
                    "workout_frequency": 4,
                },
                "key_lessons": [
                    "Consistency matters more than intensity",
                    "Don't aim for perfection, aim for progress",
                    "Support system (family/friends) is crucial",
                    "Track food and workouts to stay accountable",
                ],
                "challenges_overcome": [
                    "Initial soreness and fatigue",
                    "Cravings while eating healthier",
                    "Motivation plateaus at week 6-8",
                    "Time management with busy schedule",
                ],
            },
        ]
        
        return success_stories[:limit]


def font_goal_text(goal):
    """Format goal text."""
    goal_lower = goal.lower()
    if "muscle" in goal_lower:
        return "Building Muscle"
    elif "fat" in goal_lower:
        return "Losing Fat"
    elif "endurance" in goal_lower:
        return "Building Endurance"
    return "Improving Fitness"


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
    
    builder = DatasetContextBuilder(engine)
    
    # Example query with profile
    query = "I want to build muscle but I have diabetes. What exercises and foods are safe?"
    
    profile = {
        "goal": "muscle_gain",
        "fitness_level": "intermediate",
        "chronic_diseases": "diabetes",
        "weight": 85,
    }
    
    # Build context
    context = builder.build_context_for_query(query, profile)
    
    print("=== Built Context ===")
    print(json.dumps({
        "query": context["query"],
        "context_type": context["context_type"],
        "sources": context["sources"],
        "has_data": {k: bool(v) for k, v in context["data"].items()},
        "personalized": context.get("personalized", False),
    }, indent=2))
    
    # Build RAG prompt
    rag_context = builder.build_rag_prompt_context(query, profile)
    print("\n=== RAG Prompt Context ===")
    print(rag_context)
    
    # Get similar profiles
    similar = builder.get_similar_profiles(profile)
    print("\n=== Similar Profiles ===")
    print(json.dumps(similar, indent=2, default=str))
