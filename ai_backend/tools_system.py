from typing import Any
from datetime import datetime, date
from dataclasses import dataclass
from enum import Enum
from data_catalog import DataCatalog
from progress_engine import ProgressEngine
from recommendation_engine import RecommendationEngine
from storage import get_local_store
from utils_logger import log_event, log_error


class ToolType(str, Enum):
    """Types of tools available to agents."""
    PROFILE = "profile"
    PROGRESS = "progress"
    PLAN = "plan"
    EXERCISE = "exercise"
    NUTRITION = "nutrition"


@dataclass
class ToolResult:
    """Result from a tool execution."""
    success: bool
    data: Any
    message: str
    tool_type: ToolType


class ToolRegistry:
    """Registry of available tools for agents."""
    
    def __init__(self):
        self.tools: dict[str, dict] = {}
        self._register_default_tools()
    
    def _register_default_tools(self) -> None:
        """Register default tool definitions."""
        # Profile tools
        self.register_tool(
            "get_user_profile",
            ToolType.PROFILE,
            {
                "description": "Get user's fitness profile and preferences",
                "parameters": {
                    "properties": {
                        "user_id": {"type": "string", "description": "User ID"},
                    },
                    "required": ["user_id"],
                },
            },
        )
        
        self.register_tool(
            "update_user_profile",
            ToolType.PROFILE,
            {
                "description": "Update user's fitness profile",
                "parameters": {
                    "properties": {
                        "user_id": {"type": "string"},
                        "goal": {"type": "string", "enum": ["muscle_gain", "fat_loss", "general_fitness", "endurance", "flexibility"]},
                        "fitness_level": {"type": "string", "enum": ["beginner", "intermediate", "advanced"]},
                        "target_calories": {"type": "integer"},
                    },
                    "required": ["user_id"],
                },
            },
        )
        
        # Progress tools
        self.register_tool(
            "get_user_progress",
            ToolType.PROGRESS,
            {
                "description": "Get user's fitness progress history",
                "parameters": {
                    "properties": {
                        "user_id": {"type": "string"},
                        "days": {"type": "integer", "description": "Number of days to retrieve (default 30)"},
                    },
                    "required": ["user_id"],
                },
            },
        )
        
        self.register_tool(
            "log_workout",
            ToolType.PROGRESS,
            {
                "description": "Log a completed workout",
                "parameters": {
                    "properties": {
                        "user_id": {"type": "string"},
                        "date": {"type": "string", "description": "Date in YYYY-MM-DD format"},
                        "workout_notes": {"type": "string"},
                    },
                    "required": ["user_id", "date"],
                },
            },
        )
        
        self.register_tool(
            "log_meals",
            ToolType.PROGRESS,
            {
                "description": "Log meals for the day",
                "parameters": {
                    "properties": {
                        "user_id": {"type": "string"},
                        "date": {"type": "string", "description": "Date in YYYY-MM-DD format"},
                        "meals_notes": {"type": "string"},
                    },
                    "required": ["user_id", "date"],
                },
            },
        )
        
        # Plan tools
        self.register_tool(
            "create_workout_plan",
            ToolType.PLAN,
            {
                "description": "Create a workout plan for the user",
                "parameters": {
                    "properties": {
                        "user_id": {"type": "string"},
                        "plan_name": {"type": "string"},
                        "duration_days": {"type": "integer"},
                        "focus": {"type": "string"},
                        "exercises": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["user_id", "plan_name", "duration_days"],
                },
            },
        )
        
        self.register_tool(
            "create_nutrition_plan",
            ToolType.NUTRITION,
            {
                "description": "Create a nutrition plan for the user",
                "parameters": {
                    "properties": {
                        "user_id": {"type": "string"},
                        "daily_calories": {"type": "integer"},
                        "macros": {"type": "object"},
                        "meals": {"type": "array"},
                    },
                    "required": ["user_id", "daily_calories"],
                },
            },
        )
        
        # Exercise tools
        self.register_tool(
            "search_exercises",
            ToolType.EXERCISE,
            {
                "description": "Search for exercises by name, muscle group, or difficulty",
                "parameters": {
                    "properties": {
                        "query": {"type": "string"},
                        "muscle_group": {"type": "string"},
                        "difficulty": {"type": "string", "enum": ["beginner", "intermediate", "advanced"]},
                        "limit": {"type": "integer", "description": "Max results to return"},
                    },
                    "required": ["query"],
                },
            },
        )
        
        log_event("TOOLS", None, {"action": "default_tools_registered", "count": len(self.tools)})
    
    def register_tool(self, name: str, tool_type: ToolType, definition: dict) -> None:
        """Register a new tool."""
        self.tools[name] = {
            "type": tool_type,
            "definition": definition,
        }
    
    def get_tool_definitions(self) -> list[dict]:
        """Get OpenAI-compatible tool definitions."""
        definitions = []
        for name, tool_info in self.tools.items():
            definitions.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": tool_info["definition"]["description"],
                    "parameters": tool_info["definition"]["parameters"],
                },
            })
        return definitions
    
    def get_tool(self, name: str) -> dict | None:
        """Get a specific tool definition."""
        return self.tools.get(name)


class ToolExecutor:
    """Executes tools and manages their results."""
    
    def __init__(self, supabase_client=None, store=None, catalog: DataCatalog | None = None, recommender: RecommendationEngine | None = None):
        self.registry = ToolRegistry()
        self.supabase = supabase_client
        self.store = store or get_local_store()
        self.catalog = catalog
        self.recommender = recommender
        self.progress_engine = ProgressEngine()
    
    async def execute(
        self,
        tool_name: str,
        tool_args: dict[str, Any],
        user_id: str | None = None,
    ) -> ToolResult:
        """
        Execute a tool with given arguments.
        
        Args:
            tool_name: Name of the tool to execute
            tool_args: Arguments for the tool
            user_id: User ID for logging
            
        Returns:
            ToolResult with success status and data
        """
        tool = self.registry.get_tool(tool_name)
        if not tool:
            return ToolResult(
                success=False,
                data=None,
                message=f"Tool '{tool_name}' not found",
                tool_type=None,
            )
        
        try:
            log_event("TOOL_EXECUTION", user_id, {
                "tool": tool_name,
                "args": str(tool_args)[:200],
            })
            
            # Route to appropriate handler based on tool name
            if tool_name == "get_user_profile":
                return await self._get_user_profile(tool_args, user_id)
            elif tool_name == "update_user_profile":
                return await self._update_user_profile(tool_args, user_id)
            elif tool_name == "get_user_progress":
                return await self._get_user_progress(tool_args, user_id)
            elif tool_name == "log_workout":
                return await self._log_workout(tool_args, user_id)
            elif tool_name == "log_meals":
                return await self._log_meals(tool_args, user_id)
            elif tool_name == "create_workout_plan":
                return await self._create_workout_plan(tool_args, user_id)
            elif tool_name == "create_nutrition_plan":
                return await self._create_nutrition_plan(tool_args, user_id)
            elif tool_name == "search_exercises":
                return await self._search_exercises(tool_args, user_id)
            else:
                return ToolResult(
                    success=False,
                    data=None,
                    message=f"Tool '{tool_name}' is not implemented",
                    tool_type=tool["type"],
                )
        
        except Exception as e:
            log_error("TOOL_EXECUTION_ERROR", user_id, e, {"tool": tool_name})
            return ToolResult(
                success=False,
                data=None,
                message=f"Error executing tool: {str(e)}",
                tool_type=tool["type"],
            )
    
    async def _get_user_profile(self, args: dict, user_id: str | None) -> ToolResult:
        """Retrieve user profile from database."""
        profile = self.store.get_profile(args.get("user_id") or user_id) or {}
        return ToolResult(
            success=True,
            data=profile,
            message="User profile retrieved from local store",
            tool_type=ToolType.PROFILE,
        )
    
    async def _update_user_profile(self, args: dict, user_id: str | None) -> ToolResult:
        """Update user profile in database."""
        uid = args.get("user_id") or user_id
        if not uid:
            return ToolResult(False, None, "Missing user_id", ToolType.PROFILE)
        profile = {k: v for k, v in args.items() if k != "user_id"}
        updated = self.store.upsert_profile(uid, profile)
        return ToolResult(
            success=True,
            data=updated,
            message="User profile updated in local store",
            tool_type=ToolType.PROFILE,
        )
    
    async def _get_user_progress(self, args: dict, user_id: str | None) -> ToolResult:
        """Retrieve user progress history."""
        uid = args.get("user_id") or user_id
        if not uid:
            return ToolResult(False, None, "Missing user_id", ToolType.PROGRESS)
        days = args.get("days", 30)
        tracking = self.store.get_tracking(uid, days=days)
        summary = self.progress_engine.analyze(tracking)
        return ToolResult(
            success=True,
            data={
                "user_id": uid,
                "days": days,
                "tracking": tracking,
                "summary": summary.__dict__,
            },
            message="User progress retrieved from local store",
            tool_type=ToolType.PROGRESS,
        )
    
    async def _log_workout(self, args: dict, user_id: str | None) -> ToolResult:
        """Log a completed workout."""
        uid = args.get("user_id") or user_id
        if not uid:
            return ToolResult(False, None, "Missing user_id", ToolType.PROGRESS)
        entry = {
            "date": args.get("date"),
            "workout_notes": args.get("workout_notes"),
            "workouts_completed": 1,
        }
        self.store.log_tracking(uid, entry)
        return ToolResult(
            success=True,
            data={"logged": True, "date": args.get("date")},
            message="Workout logged in local store",
            tool_type=ToolType.PROGRESS,
        )
    
    async def _log_meals(self, args: dict, user_id: str | None) -> ToolResult:
        """Log meals for a day."""
        uid = args.get("user_id") or user_id
        if not uid:
            return ToolResult(False, None, "Missing user_id", ToolType.PROGRESS)
        entry = {
            "date": args.get("date"),
            "meals_notes": args.get("meals_notes"),
        }
        self.store.log_tracking(uid, entry)
        return ToolResult(
            success=True,
            data={"logged": True, "date": args.get("date")},
            message="Meals logged in local store",
            tool_type=ToolType.PROGRESS,
        )

    async def _create_workout_plan(self, args: dict, user_id: str | None) -> ToolResult:
        uid = args.get("user_id") or user_id
        if not uid:
            return ToolResult(False, None, "Missing user_id", ToolType.PLAN)
        if not self.recommender:
            return ToolResult(False, None, "Recommendation engine unavailable", ToolType.PLAN)
        profile = self.store.get_profile(uid) or {}
        profile.update({k: v for k, v in args.items() if k != "user_id"})
        plan = self.recommender.workout.generate_plan_options(profile, count=1)[0]
        self.store.add_plan(uid, "workout", plan)
        return ToolResult(True, plan, "Workout plan created", ToolType.PLAN)

    async def _create_nutrition_plan(self, args: dict, user_id: str | None) -> ToolResult:
        uid = args.get("user_id") or user_id
        if not uid:
            return ToolResult(False, None, "Missing user_id", ToolType.PLAN)
        if not self.recommender:
            return ToolResult(False, None, "Recommendation engine unavailable", ToolType.PLAN)
        profile = self.store.get_profile(uid) or {}
        profile.update({k: v for k, v in args.items() if k != "user_id"})
        plan = self.recommender.nutrition.generate_plan_options(profile, count=1)[0]
        self.store.add_plan(uid, "nutrition", plan)
        return ToolResult(True, plan, "Nutrition plan created", ToolType.PLAN)
    
    async def _search_exercises(self, args: dict, user_id: str | None) -> ToolResult:
        """Search for exercises."""
        if self.catalog:
            results = self.catalog.search_exercises(
                args.get("query", ""),
                muscle=args.get("muscle_group"),
                difficulty=args.get("difficulty"),
                limit=args.get("limit", 5),
            )
        else:
            results = []
        return ToolResult(
            success=True,
            data={
                "exercises": results,
            },
            message="Exercises found in catalog",
            tool_type=ToolType.EXERCISE,
        )
