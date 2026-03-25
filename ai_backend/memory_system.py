from typing import Optional
import json
from datetime import datetime
from collections import deque
from nlp_utils import repair_mojibake
from utils_logger import log_event


class Message:
    """Represents a single message in conversation."""
    
    def __init__(self, role: str, content: str, metadata: dict | None = None):
        self.role = role  # 'user' or 'assistant'
        self.content = repair_mojibake(content or "")
        self.timestamp = datetime.now().isoformat()
        self.metadata = metadata or {}
    
    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }
    
    def to_llm_dict(self) -> dict:
        """Convert to format expected by LLM."""
        return {
            "role": self.role,
            "content": self.content,
        }


class ShortTermMemory:
    """Stores recent messages in memory (last N messages)."""
    
    def __init__(self, max_size: int = 10):
        self.max_size = max_size
        self.messages: deque = deque(maxlen=max_size)
    
    def add_message(self, role: str, content: str, metadata: dict | None = None) -> None:
        """Add a message to short-term memory."""
        msg = Message(role, content, metadata)
        self.messages.append(msg)
        log_event("SHORT_TERM_MEMORY", None, {
            "action": "message_added",
            "total_messages": len(self.messages),
        })
    
    def get_history(self, limit: int | None = None) -> list[dict]:
        """Get message history for LLM context."""
        history = list(self.messages)
        if limit:
            history = history[-limit:]
        return [msg.to_llm_dict() for msg in history]
    
    def get_full_history(self) -> list[dict]:
        """Get full message history including metadata."""
        return [msg.to_dict() for msg in self.messages]
    
    def clear(self) -> None:
        """Clear short-term memory."""
        self.messages.clear()
    
    def is_empty(self) -> bool:
        """Check if memory is empty."""
        return len(self.messages) == 0


class LongTermMemory:
    """Stores user preferences and patterns for long-term context."""
    
    def __init__(self, user_id: str | None = None):
        self.user_id = user_id
        self.profile = {}
        self.preferences = {}
        self.patterns = {}
        self.goals = {}
    
    def update_profile(self, profile_data: dict) -> None:
        """Update user profile information."""
        self.profile.update(profile_data)
        log_event("LONG_TERM_MEMORY", self.user_id, {
            "action": "profile_updated",
            "keys": list(profile_data.keys()),
        })
    
    def update_preferences(self, preferences_data: dict) -> None:
        """Update user preferences."""
        self.preferences.update(preferences_data)
        log_event("LONG_TERM_MEMORY", self.user_id, {
            "action": "preferences_updated",
            "keys": list(preferences_data.keys()),
        })
    
    def update_patterns(self, pattern_key: str, pattern_value: any) -> None:
        """Track user behavior patterns."""
        self.patterns[pattern_key] = pattern_value
        log_event("LONG_TERM_MEMORY", self.user_id, {
            "action": "pattern_tracked",
            "pattern": pattern_key,
        })
    
    def update_goals(self, goals_data: dict) -> None:
        """Update user fitness goals."""
        self.goals.update(goals_data)
        log_event("LONG_TERM_MEMORY", self.user_id, {
            "action": "goals_updated",
            "keys": list(goals_data.keys()),
        })
    
    def get_context_summary(self) -> str:
        """Get a summary of user context for LLM."""
        lines = []
        
        if self.profile:
            lines.append("User Profile:")
            for key, value in self.profile.items():
                lines.append(f"  - {key}: {value}")
        
        if self.goals:
            lines.append("\nFitness Goals:")
            for key, value in self.goals.items():
                lines.append(f"  - {key}: {value}")
        
        if self.preferences:
            lines.append("\nPreferences:")
            for key, value in self.preferences.items():
                lines.append(f"  - {key}: {value}")
        
        if self.patterns:
            lines.append("\nBehavior Patterns:")
            for key, value in self.patterns.items():
                lines.append(f"  - {key}: {value}")
        
        return "\n".join(lines) if lines else ""


class MemorySystem:
    """Complete memory system combining short and long-term memory."""
    
    def __init__(self, user_id: str | None = None, max_short_term: int = 10):
        self.user_id = user_id
        self.short_term = ShortTermMemory(max_short_term)
        self.long_term = LongTermMemory(user_id)
    
    def add_user_message(self, content: str, metadata: dict | None = None) -> None:
        """Add user message to short-term memory."""
        self.short_term.add_message("user", content, metadata)
    
    def add_assistant_message(self, content: str, metadata: dict | None = None) -> None:
        """Add assistant message to short-term memory."""
        self.short_term.add_message("assistant", content, metadata)
    
    def get_conversation_history(self) -> list[dict]:
        """Get conversation history for LLM."""
        return self.short_term.get_history()
    
    def get_system_prompt(self, language: str = "en") -> str:
        """
        Get a system prompt that includes user context and memory.
        
        Args:
            language: User's language
            
        Returns:
            System prompt with context
        """
        base_prompts = {
            "en": """You are FitCoach AI, a smart and interactive personal fitness assistant.
You are friendly, encouraging, and motivating. Adapt to the user's mood.
You ONLY answer fitness, training, sports performance, and nutrition topics.
If input is ambiguous, ask clarifying questions before advising.
Do NOT hallucinate medical advice.
Always start with a short motivational sentence, then provide actionable guidance.
Include sets/reps/intensity for exercises and explain nutrition choices when relevant.
Remind about warm-up, cool-down, and rest days when appropriate.
Always personalize responses based on user profile, preferences, goals, and past conversations.""",
            "ar_fusha": """??? ???? ????? ??? (FitCoach AI) ???? ?????? ??????? ?? ???? ????????.
??? ??? ?? ????? ??????? ???????? ???????? ??????? ???????.
??? ??? ????? ??? ????? ???? ????? ??????? ??? ???????.
?? ?????? ????? ???? ??? ??? ??????.
???? ?????? ????? ??????? ????? ?? ???? ????? ?????.
???? ?????????/?????????/????? ???????? ????? ???????? ??????? ??? ??????.
???? ???????? ???????? ????? ?????? ??? ??????.
???? ???????? ????? ??? ????? ?????? ?????????? ???????? ?????????? ???????.""",
            "ar_jordanian": """??? FitCoach AI? ???? ???? ??? ????? ?????? ??????? ???? ????????.
???? ?? ?? ????? ??????? ???????? ???????? ??????? ???????.
??? ????? ?? ????? ???? ??? ?? ???? ?????.
?? ???? ????? ???? ??? ?? ?????.
???? ?????? ????? ??????? ????? ????? ????? ?????.
???? ???????/???????/??? ??????? ????? ???????? ??????? ??? ??????.
???? ???????? ???????? ????? ?????? ??? ??????.
???? ?????? ??? ????? ?????? ?????????? ???????? ?????????? ???????.""",
        }
        system_prompt = base_prompts.get(language, base_prompts["en"])
        
        # Add user context if available
        context_summary = self.long_term.get_context_summary()
        if context_summary:
            system_prompt += f"\n\nUser Context:\n{context_summary}"

        style_profile = None
        for key in ("speaking_style", "response_style", "style", "chat_style", "json_style", "tone_profile"):
            value = self.long_term.profile.get(key)
            if isinstance(value, dict):
                style_profile = value
                break
            if isinstance(value, str) and value.strip().startswith("{"):
                try:
                    style_profile = json.loads(value)
                    break
                except Exception:
                    continue
        prefs = self.long_term.preferences or {}
        if not style_profile and isinstance(prefs, dict):
            for key in ("speaking_style", "response_style", "style", "chat_style", "json_style", "tone_profile"):
                value = prefs.get(key)
                if isinstance(value, dict):
                    style_profile = value
                    break
                if isinstance(value, str) and value.strip().startswith("{"):
                    try:
                        style_profile = json.loads(value)
                        break
                    except Exception:
                        continue
        if style_profile:
            try:
                system_prompt += "\n\nUser speaking style JSON (follow it):\n" + json.dumps(
                    style_profile, ensure_ascii=False
                )
            except Exception:
                pass
        
        return repair_mojibake(system_prompt)
    
    def clear_short_term(self) -> None:
        """Clear short-term conversation history."""
        self.short_term.clear()
        log_event("MEMORY", self.user_id, {"action": "short_term_cleared"})
