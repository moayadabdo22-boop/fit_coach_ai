"""
Multi-Dataset Training System Integration

Initializes and integrates all components:
- MultiDatasetLoader: Loads all 50 datasets
- TrainingEngine: Learns patterns
- PersonalizationEngine: Profile-based matching
- EnhancedRecommendationEngine: Personalized recommendations
- DatasetContextBuilder: RAG integration

This file provides the complete pipeline for training and personalized recommendations.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

try:
    from .multi_dataset_loader import MultiDatasetLoader
    from .training_engine import TrainingEngine
    from .personalization_engine import PersonalizationEngine
    from .enhanced_recommendation_engine import EnhancedRecommendationEngine
    from .dataset_context_builder import DatasetContextBuilder
except ImportError:
    from multi_dataset_loader import MultiDatasetLoader
    from training_engine import TrainingEngine
    from personalization_engine import PersonalizationEngine
    from enhanced_recommendation_engine import EnhancedRecommendationEngine
    from dataset_context_builder import DatasetContextBuilder

logger = logging.getLogger(__name__)


class TrainingPipeline:
    """
    Complete training pipeline that orchestrates all components.
    """
    
    def __init__(self, dataset_root: Path | str, model_cache_path: Path | str | None = None):
        """
        Initialize the training pipeline.
        
        Args:
            dataset_root: Path to datasets folder
            model_cache_path: Optional path to cache trained models
        """
        self.dataset_root = Path(dataset_root)
        self.model_cache_path = Path(model_cache_path) if model_cache_path else None
        
        # Initialize components
        self.loader = MultiDatasetLoader(self.dataset_root)
        self.training_engine = TrainingEngine(self.loader)
        self.personalizer = PersonalizationEngine(self.training_engine)
        self.enhanced_recommender = EnhancedRecommendationEngine(
            self.training_engine,
            self.personalizer,
            None  # Will be set to original recommender if available
        )
        self.context_builder = DatasetContextBuilder(self.training_engine)
        
        self.trained = False
    
    def train(self) -> bool:
        """
        Train the model on all datasets.
        
        Returns:
            True if training successful, False otherwise
        """
        try:
            logger.info("Starting multi-dataset training pipeline...")
            
            # Load all datasets
            logger.info("Loading datasets...")
            self.loader.load_all()
            
            # Train models
            logger.info("Training models...")
            self.training_engine.train()
            
            # Save models if cache path provided
            if self.model_cache_path:
                self._save_models()
            
            self.trained = True
            logger.info("Training pipeline complete!")
            
            return True
        
        except Exception as e:
            logger.error(f"Training failed: {e}", exc_info=True)
            return False
    
    def load_cached_models(self) -> bool:
        """
        Load pre-trained models from cache.
        
        Returns:
            True if models loaded, False otherwise
        """
        if not self.model_cache_path:
            logger.warning("No model cache path configured")
            return False
        
        try:
            success = self.training_engine.load_model(self.model_cache_path / "training_model.pkl")
            if success:
                self.trained = True
                logger.info("Loaded cached models successfully")
            return success
        except Exception as e:
            logger.error(f"Failed to load cached models: {e}")
            return False
    
    def _save_models(self) -> None:
        """Save trained models to cache."""
        if not self.model_cache_path:
            return
        
        self.model_cache_path.mkdir(parents=True, exist_ok=True)
        self.training_engine.save_model(self.model_cache_path / "training_model.pkl")
        logger.info(f"Saved models to {self.model_cache_path}")
    
    def get_personalized_plan(self, profile: dict[str, Any]) -> dict[str, Any]:
        """
        Get a complete personalized plan for a user.
        
        Args:
            profile: User profile
            
        Returns:
            Complete personalized plan
        """
        if not self.trained:
            logger.warning("Model not trained, returning basic recommendations")
        
        return self.enhanced_recommender.generate_complete_plan(profile)
    
    def get_personalized_exercises(self, profile: dict[str, Any], 
                                  limit: int = 10) -> list[dict[str, Any]]:
        """Get personalized exercises."""
        return self.enhanced_recommender.get_personalized_exercises(profile, limit)
    
    def get_personalized_foods(self, profile: dict[str, Any],
                              limit: int = 20) -> list[dict[str, Any]]:
        """Get personalized foods."""
        return self.enhanced_recommender.get_personalized_foods(profile, limit)
    
    def build_rag_context(self, query: str,
                         profile: dict[str, Any] | None = None) -> str:
        """Build RAG context from datasets."""
        return self.context_builder.build_rag_prompt_context(query, profile)
    
    def get_summary(self) -> dict[str, Any]:
        """Get summary of trained models."""
        return {
            "trained": self.trained,
            "dataset_summary": {
                "total_datasets": len(self.loader.datasets),
                "dataset_names": list(self.loader.datasets.keys()),
                "total_records": sum(len(v) for v in self.loader.datasets.values()),
            },
            "training_summary": self.training_engine.get_training_summary(),
            "model_cache_path": str(self.model_cache_path) if self.model_cache_path else None,
        }


async def initialize_training_system(dataset_root: Path | str,
                                    model_cache_path: Path | str | None = None) -> TrainingPipeline:
    """
    Initialize the complete training system.
    
    Args:
        dataset_root: Path to datasets folder
        model_cache_path: Optional path for model caching
        
    Returns:
        Initialized TrainingPipeline
    """
    pipeline = TrainingPipeline(dataset_root, model_cache_path)
    
    # Try to load cached models first
    if model_cache_path and Path(model_cache_path).exists():
        if pipeline.load_cached_models():
            logger.info("Using cached models")
            return pipeline
    
    # Train if not cached
    if pipeline.train():
        return pipeline
    else:
        logger.error("Failed to initialize training system")
        raise RuntimeError("Training pipeline initialization failed")


# Example integration with CoachAgent
def integrate_with_coach_agent(coach_agent, pipeline: TrainingPipeline) -> None:
    """
    Integrate the training pipeline with CoachAgent.
    
    Args:
        coach_agent: CoachAgent instance
        pipeline: TrainingPipeline instance
    """
    # Add the enhanced recommender to the coach agent
    coach_agent.enhanced_recommender = pipeline.enhanced_recommender
    coach_agent.training_engine = pipeline.training_engine
    coach_agent.personalizer = pipeline.personalizer
    coach_agent.context_builder = pipeline.context_builder
    
    logger.info("Integrated training pipeline with CoachAgent")


if __name__ == "__main__":
    import json
    try:
        from .dataset_paths import resolve_dataset_root
    except ImportError:
        from dataset_paths import resolve_dataset_root
    
    # Example initialization
    dataset_root = resolve_dataset_root()
    model_cache_path = dataset_root.parent / "models" / "training_cache"
    
    pipeline = TrainingPipeline(dataset_root, model_cache_path)
    
    # Train the system
    if pipeline.train():
        print("\n=== Training Summary ===")
        summary = pipeline.get_summary()
        print(json.dumps(summary, indent=2))
        
        # Example user profile
        profile = {
            "id": "example_user",
            "weight": 85,
            "height": 180,
            "age": 30,
            "gender": "male",
            "goal": "fat_loss",
            "fitness_level": "intermediate",
            "chronic_diseases": "diabetes",
            "training_days_per_week": 4,
            "target_weight": 75,
            "target_timeline_weeks": 12,
        }
        
        # Get personalized plan
        print("\n=== Generating Personalized Plan ===")
        plan = pipeline.get_personalized_plan(profile)
        print(f"Plan ID: {plan['id']}")
        print(f"User ID: {plan['user_id']}")
        print(f"Recommendations: {len(plan.get('recommendations', {}).get('exercises', {}).get('recommended', []))} exercises")
        
        # Build RAG context
        print("\n=== Building RAG Context ===")
        query = "I have diabetes and want to lose weight. What's a good plan?"
        rag_context = pipeline.build_rag_context(query, profile)
        print(rag_context[:500] + "...")
