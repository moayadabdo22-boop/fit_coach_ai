"""
Specialized agents for specific fitness coaching tasks.
Each agent extends the base CoachAgent capabilities.
"""

from typing import Optional, List, Dict, Any
from datetime import date
from coach_agent import CoachAgent
from llm_client import LLMClient
from tools_system import ToolExecutor
from utils_logger import log_agent_action
import json


class WorkoutPlannerAgent(CoachAgent):
    """Specialized agent for creating and managing workout plans."""
    
    async def generate_workout_plan(
        self,
        duration_days: int = 28,
        frequency_per_week: int = 4,
    ) -> Dict[str, Any]:
        """
        Generate a personalized workout plan.
        
        Args:
            duration_days: Plan duration in days
            frequency_per_week: Workouts per week
            
        Returns:
            Plan dictionary with exercises, schedule, and notes
        """
        log_agent_action("WorkoutPlannerAgent", "generate_plan", self.user_id, {
            "duration": duration_days,
            "frequency": frequency_per_week,
        })
        
        # Get user context
        profile_summary = self.memory.long_term.get_context_summary()
        
        # Build prompt for plan generation
        prompt = f"""Based on the user profile:
{profile_summary}

Generate a detailed {duration_days}-day workout plan with {frequency_per_week} sessions per week.

Include:
1. Weekly structure and split
2. Daily exercises with sets/reps
3. Progression cues
4. Recovery notes
5. Equipment needed
6. Muscle group focus per day

Format as JSON."""
        
        # Get LLM to generate plan
        system_prompt = self.memory.get_system_prompt(self.language)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]
        
        response = self.llm.chat_completion(messages, max_tokens=2000)
        
        # Parse JSON response
        try:
            plan = json.loads(response)
        except:
            plan = {"raw_plan": response}
        
        log_agent_action("WorkoutPlannerAgent", "plan_generated", self.user_id, {
            "plan_days": duration_days,
        })
        
        return plan
    
    async def get_daily_workout(self, target_date: date) -> Dict[str, Any]:
        """Get the workout for a specific day."""
        # This would retrieve from database in production
        return {
            "date": target_date.isoformat(),
            "exercises": [],
            "notes": "",
        }
    
    async def evaluate_workout_difficulty(
        self,
        exercises: List[str],
    ) -> Dict[str, Any]:
        """Evaluate difficulty level of workout."""
        prompt = f"""Evaluate the difficulty level of this workout: {', '.join(exercises)}

Consider:
- Exercise complexity
- Intensity level
- Recovery time needed
- Suitable for: beginner/intermediate/advanced

Provide difficulty score 1-10."""
        
        messages = [
            {"role": "system", "content": self.memory.get_system_prompt(self.language)},
            {"role": "user", "content": prompt},
        ]
        
        response = self.llm.chat_completion(messages)
        return {"evaluation": response}


class NutritionPlannerAgent(CoachAgent):
    """Specialized agent for nutrition planning."""
    
    async def generate_nutrition_plan(
        self,
        daily_calories: int,
        macro_split: Optional[Dict[str, int]] = None,
    ) -> Dict[str, Any]:
        """
        Generate personalized nutrition plan.
        
        Args:
            daily_calories: Daily calorie target
            macro_split: Protein/carbs/fat distribution
            
        Returns:
            Plan with daily meals and macros
        """
        log_agent_action("NutritionPlannerAgent", "generate_plan", self.user_id, {
            "calories": daily_calories,
        })
        
        profile_summary = self.memory.long_term.get_context_summary()
        
        # Default macro split (40P/40C/20F)
        if not macro_split:
            macro_split = {
                "protein_percent": 40,
                "carbs_percent": 40,
                "fat_percent": 20,
            }
        
        prompt = f"""Based on user profile:
{profile_summary}

Generate a healthy nutrition plan for {daily_calories} calories/day with this macro split:
- Protein: {macro_split.get('protein_percent', 40)}%
- Carbs: {macro_split.get('carbs_percent', 40)}%
- Fat: {macro_split.get('fat_percent', 20)}%

Include:
1. 5 diverse daily meals
2. Shopping list
3. Meal prep tips
4. Hydration recommendations
5. Special considerations (allergies, preferences)

Format as JSON with meals list."""
        
        messages = [
            {"role": "system", "content": self.memory.get_system_prompt(self.language)},
            {"role": "user", "content": prompt},
        ]
        
        response = self.llm.chat_completion(messages, max_tokens=2000)
        
        try:
            plan = json.loads(response)
        except:
            plan = {"raw_plan": response}
        
        return plan
    
    async def analyze_meal_adherence(
        self,
        logged_meals: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Analyze how well user is following nutrition plan."""
        prompt = f"""Analyze meal adherence for: {json.dumps(logged_meals)}

Evaluate:
- Macro balance
- Calorie consistency  
- Meal timing
- Hydration
- Overall adherence score

Provide suggestions for improvement."""
        
        messages = [
            {"role": "system", "content": self.memory.get_system_prompt(self.language)},
            {"role": "user", "content": prompt},
        ]
        
        response = self.llm.chat_completion(messages)
        return {"analysis": response}


class ProgressAnalyzerAgent(CoachAgent):
    """Specialized agent for analyzing user progress."""
    
    async def analyze_progress(
        self,
        days: int = 30,
    ) -> Dict[str, Any]:
        """
        Analyze user progress over time period.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Progress analysis and recommendations
        """
        log_agent_action("ProgressAnalyzerAgent", "analyze", self.user_id, {
            "days": days,
        })
        
        # Get progress data (would fetch from DB in production)
        progress_data = {
            "workouts_completed": 0,
            "consistency_score": 0.0,
            "meals_logged": 0,
            "weight_change": 0,
            "strength_gains": [],
        }
        
        profile_summary = self.memory.long_term.get_context_summary()
        
        prompt = f"""Analyze this progress over the last {days} days:

User Profile:
{profile_summary}

Progress Data:
{json.dumps(progress_data)}

Provide:
1. Overall progress assessment
2. Achievements and wins
3. Areas for improvement
4. Next steps and adjustments
5. Motivation and encouragement

Keep it personalized and actionable."""
        
        messages = [
            {"role": "system", "content": self.memory.get_system_prompt(self.language)},
            {"role": "user", "content": prompt},
        ]
        
        response = self.llm.chat_completion(messages)
        return {
            "analysis": response,
            "analyzed_days": days,
            "timestamp": date.today().isoformat(),
        }
    
    async def identify_patterns(self) -> Dict[str, Any]:
        """Identify behavior patterns from conversation history."""
        history = self.memory.short_term.get_full_history()
        
        patterns = {
            "common_topics": [],
            "goals_mentioned": [],
            "constraints": [],
            "preferences": [],
        }
        
        # Analyze conversation history for patterns
        prompt = f"""Analyze these messages to identify user patterns:

{json.dumps([m.get('content', '')[:100] for m in history[-10:]])}

Identify:
1. Most common fitness interests
2. Goals mentioned repeatedly
3. Constraints/limitations (injuries, schedule)
4. Preferences (equipment, workout style)

Format as structured data."""
        
        messages = [
            {"role": "system", "content": self.memory.get_system_prompt(self.language)},
            {"role": "user", "content": prompt},
        ]
        
        response = self.llm.chat_completion(messages)
        try:
            patterns = json.loads(response)
        except:
            pass
        
        return {"patterns": patterns}


class AgentOrchestrator:
    """Coordinates multiple specialized agents."""
    
    def __init__(self, user_id: Optional[str] = None, language: str = "en"):
        self.user_id = user_id
        self.language = language
        
        self.main_agent = CoachAgent(user_id, language)
        self.workout_agent = WorkoutPlannerAgent(user_id, language)
        self.nutrition_agent = NutritionPlannerAgent(user_id, language)
        self.progress_agent = ProgressAnalyzerAgent(user_id, language)
    
    async def route_request(self, message: str) -> tuple[str, str]:
        """
        Route request to appropriate agent.
        
        Args:
            message: User message
            
        Returns:
            Tuple of (response, agent_used)
        """
        message_lower = message.lower()
        
        # Route to specialized agents based on keywords
        if any(word in message_lower for word in 
               ["workout", "plan", "training program", "routine", "تمرين", "برنامج"]):
            log_agent_action("Orchestrator", "route_to_workout", self.user_id, {})
            # Delegate to workout agent - but keep main agent for interaction
            response = await self.main_agent.process_message(message)
            return response, "workout_planner"
        
        elif any(word in message_lower for word in 
                 ["meal", "nutrition", "diet", "calories", "recipe", "تغذية", "وجبة"]):
            log_agent_action("Orchestrator", "route_to_nutrition", self.user_id, {})
            response = await self.main_agent.process_message(message)
            return response, "nutrition_planner"
        
        elif any(word in message_lower for word in 
                 ["progress", "track", "improvement", "result", "gain", "تقدم", "نتيجة"]):
            log_agent_action("Orchestrator", "route_to_progress", self.user_id, {})
            response = await self.main_agent.process_message(message)
            return response, "progress_analyzer"
        
        else:
            log_agent_action("Orchestrator", "route_to_main", self.user_id, {})
            response = await self.main_agent.process_message(message)
            return response, "main"
