"""
Integration Example for CoachAgent with Multi-Dataset Training

This file shows how to integrate the training pipeline with the existing CoachAgent.
You can adapt this to your specific needs.
"""

from typing import Iterator
from pathlib import Path

try:
    from .coach_agent import CoachAgent
    from .training_pipeline import TrainingPipeline
    from .dataset_paths import resolve_dataset_root
except ImportError:
    from coach_agent import CoachAgent
    from training_pipeline import TrainingPipeline
    from dataset_paths import resolve_dataset_root


class EnhancedCoachAgent(CoachAgent):
    """
    Enhanced CoachAgent that uses multi-dataset training for personalized recommendations.
    """
    
    def __init__(
        self,
        user_id: str | None = None,
        language: str = "en",
        supabase_client=None,
        exercises_path: str | None = None,
        catalog=None,
        recommender=None,
        enable_training_pipeline: bool = True,
    ):
        """Initialize with optional training pipeline."""
        
        # Initialize base coach agent
        super().__init__(
            user_id=user_id,
            language=language,
            supabase_client=supabase_client,
            exercises_path=exercises_path,
            catalog=catalog,
            recommender=recommender,
        )
        
        # Initialize training pipeline
        self.training_pipeline: TrainingPipeline | None = None
        self.training_enabled = enable_training_pipeline
        
        if enable_training_pipeline:
            self._init_training_pipeline()
    
    def _init_training_pipeline(self) -> None:
        """Initialize and train the multi-dataset pipeline."""
        try:
            dataset_root = resolve_dataset_root()
            model_cache_path = dataset_root.parent / "models" / "training_cache"
            
            self.training_pipeline = TrainingPipeline(dataset_root, model_cache_path)
            
            # Try to load cached models first (fast)
            if not self.training_pipeline.load_cached_models():
                # Train if no cache (slow but one-time)
                self.training_pipeline.train()
            
            print(f"✅ Training pipeline initialized for user {self.user_id}")
        
        except Exception as e:
            print(f"⚠️ Failed to initialize training pipeline: {e}")
            self.training_pipeline = None
            self.training_enabled = False
    
    async def process_message(
        self,
        user_message: str,
        stream: bool = False,
        user_profile: dict | None = None,
    ) -> str | Iterator[str]:
        """
        Enhanced process_message with training pipeline support.
        
        Args:
            user_message: User's input
            stream: Whether to stream the response
            user_profile: Optional user profile for personalization
            
        Returns:
            Response text or iterator of text chunks
        """
        
        # Use training pipeline for better context if available
        if self.training_pipeline and user_profile:
            # Get RAG context from training data
            rag_context = self.training_pipeline.build_rag_context(
                user_message,
                user_profile
            )
            
            # Enhance system prompt with RAG context
            # This will be used by the LLM for better responses
            enhanced_prompt = f"""You are an AI fitness coach with comprehensive knowledge.
            
Use this context from our training data to provide personalized advice:

{rag_context}

Remember to consider the user's personal health conditions and goals."""
            
            # Store original system prompt
            original_get_prompt = self.memory.get_system_prompt
            
            # Temporarily replace system prompt getter
            def get_enhanced_prompt(lang):
                base_prompt = original_get_prompt(lang)
                return base_prompt + "\n\n" + enhanced_prompt
            
            self.memory.get_system_prompt = get_enhanced_prompt
        
        # Call parent process_message
        response = await super().process_message(user_message, stream)
        
        # Restore original system prompt getter if we modified it
        if self.training_pipeline and user_profile:
            self.memory.get_system_prompt = original_get_prompt
        
        return response
    
    def get_personalized_plan(self, user_profile: dict) -> dict:
        """
        Get a complete personalized plan using training pipeline.
        
        Args:
            user_profile: User profile with fitness and health info
            
        Returns:
            Personalized plan combining workouts, nutrition, and health guidance
        """
        if not self.training_pipeline:
            # Fallback to default recommendations
            return self._get_fallback_plan(user_profile)
        
        return self.training_pipeline.get_personalized_plan(user_profile)
    
    def _get_fallback_plan(self, user_profile: dict) -> dict:
        """Fallback to original recommender if pipeline unavailable."""
        # Use original recommendation engine
        return self.recommender.generate_plan_options(user_profile)
    
    def get_exercise_recommendations(self, user_profile: dict, limit: int = 10) -> list:
        """Get personalized exercise recommendations."""
        if not self.training_pipeline:
            # Fallback
            return self.catalog.search_exercises(
                query=user_profile.get("goal", ""),
                limit=limit
            )
        
        return self.training_pipeline.get_personalized_exercises(user_profile, limit)
    
    def get_food_recommendations(self, user_profile: dict, limit: int = 20) -> list:
        """Get personalized food recommendations."""
        if not self.training_pipeline:
            # Fallback
            return self.catalog.foods[:limit]
        
        return self.training_pipeline.get_personalized_foods(user_profile, limit)


# Example usage
async def example_usage():
    """Demonstrate the enhanced coach agent."""
    
    # User profile
    user_profile = {
        "id": "user_123",
        "name": "أحمد",  # Arabic name example
        "weight": 90,
        "height": 180,
        "age": 32,
        "gender": "male",
        "goal": "fat_loss",
        "fitness_level": "intermediate",
        "chronic_diseases": "diabetes,hypertension",
        "allergies": "shellfish,tree nuts",
        "dietary_preferences": "halal",
        "available_equipment": "dumbbell,kettlebell",
        "training_days_per_week": 4,
        "target_weight": 75,
        "target_timeline_weeks": 16,
    }
    
    # Initialize enhanced coach agent
    coach = EnhancedCoachAgent(
        user_id=user_profile["id"],
        language="en",
        enable_training_pipeline=True,
    )
    
    # Example: Get personalized plan
    print("\n🏋️ Generating Personalized Plan...")
    plan = coach.get_personalized_plan(user_profile)
    print(f"   Plan ID: {plan.get('id')}")
    print(f"   Exercises: {len(plan.get('recommendations', {}).get('exercises', {}).get('recommended', []))}")
    print(f"   Foods: {len(plan.get('recommendations', {}).get('nutrition', {}).get('recommended_foods', []))}")
    
    # Example: Get exercise recommendations
    print("\n🏃 Top Exercise Recommendations:")
    exercises = coach.get_exercise_recommendations(user_profile, limit=5)
    for i, ex in enumerate(exercises[:5], 1):
        ex_name = ex.get("exercise") if isinstance(ex, dict) else str(ex)
        print(f"   {i}. {ex_name}")
    
    # Example: Get food recommendations
    print("\n🥗 Top Food Recommendations:")
    foods = coach.get_food_recommendations(user_profile, limit=5)
    for i, food in enumerate(foods[:5], 1):
        food_name = food.get("name") if isinstance(food, dict) else str(food)
        print(f"   {i}. {food_name}")
    
    # Example: Process message with training context
    print("\n💬 Processing User Message with Training Context...")
    user_message = "أنا مصاب بالسكري وضغط الدم. كيف أفقد وزني بأمان؟"  # Arabic: "I have diabetes and blood pressure. How can I lose weight safely?"
    
    response = await coach.process_message(
        user_message,
        stream=False,
        user_profile=user_profile,
    )
    
    print(f"   User: {user_message}")
    print(f"   Coach: {str(response)[:200]}...")


# Integration with FastAPI
async def setup_fastapi_integration(app):
    """Setup enhanced CoachAgent in FastAPI app."""
    
    # Initialize agent at startup
    coach_agent = None
    
    @app.on_event("startup")
    async def startup():
        nonlocal coach_agent
        coach_agent = EnhancedCoachAgent(
            enable_training_pipeline=True,
        )
    
    @app.post("/api/chat")
    async def chat(
        user_id: str,
        message: str,
        profile: dict | None = None,
    ):
        """Chat endpoint with multi-dataset training support."""
        if not coach_agent:
            return {"error": "Coach agent not initialized"}
        
        # Process message with training context
        response = await coach_agent.process_message(
            message,
            stream=False,
            user_profile=profile,
        )
        
        return {
            "user_id": user_id,
            "message": message,
            "response": response,
        }
    
    @app.get("/api/personalized-plan/{user_id}")
    async def personalized_plan(user_id: str, profile: dict | None = None):
        """Get personalized plan endpoint."""
        if not coach_agent or not profile:
            return {"error": "Coach agent not available or profile missing"}
        
        plan = coach_agent.get_personalized_plan(profile)
        return plan
    
    @app.get("/api/exercise-recommendations/{user_id}")
    async def exercise_recommendations(user_id: str, limit: int = 10):
        """Get exercise recommendations."""
        if not coach_agent:
            return {"error": "Coach agent not initialized"}
        
        # In real app, load profile from database
        profile = {"goal": "general_fitness"}
        
        exercises = coach_agent.get_exercise_recommendations(profile, limit)
        return {
            "user_id": user_id,
            "count": len(exercises),
            "exercises": exercises,
        }
    
    return app


# CLI example
def cli_example():
    """Command-line interface example."""
    import asyncio
    
    print("🤖 AI Fitness Coach with Multi-Dataset Training")
    print("=" * 50)
    
    # Create coach
    coach = EnhancedCoachAgent(
        user_id="cli_user",
        enable_training_pipeline=True,
    )
    
    # User profile
    profile = {
        "goal": "muscle_gain",
        "fitness_level": "intermediate",
        "weight": 80,
        "height": 180,
        "age": 28,
        "gender": "male",
    }
    
    # Get recommendations
    plan = coach.get_personalized_plan(profile)
    
    print("\n✅ Personalized Plan Generated:")
    print(f"   ID: {plan.get('id')}")
    print(f"   Exercises: {len(plan.get('recommendations', {}).get('exercises', {}).get('recommended', []))}")
    
    # Interactive chat loop
    print("\n💬 Chat Mode (type 'quit' to exit):")
    while True:
        try:
            user_input = input("\nYou: ").strip()
            if user_input.lower() in ["quit", "exit", "q"]:
                break
            
            # Process message
            response = asyncio.run(coach.process_message(
                user_input,
                stream=False,
                user_profile=profile,
            ))
            
            print(f"Coach: {response}")
        
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    import asyncio
    
    # Run example
    asyncio.run(example_usage())
