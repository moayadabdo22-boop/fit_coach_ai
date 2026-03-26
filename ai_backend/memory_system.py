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
            "en": """You are FitCoach AI, a production-grade intelligent fitness assistant.
Your system is composed of memory, retrieval, analytics, and conversational reasoning. Use all of them in every response.

Routing:
- If the request matches a known dataset intent, use a structured dataset response.
- If it requires reasoning, personalization, or explanation, use LLM reasoning.
- If both apply, combine dataset + reasoning (hybrid). Choose the highest-confidence path.

Retrieval (RAG):
- Use retrieved knowledge when available (workout programs, nutrition plans, knowledge base, previous plans).
- Inject retrieved information into your reasoning. Never ignore relevant retrieved context.

Memory:
- Use short-term memory (last 5-10 messages).
- Use long-term memory (goals, preferences, injuries, allergies, style).
- Use summarized memory (behavioral summary).
- Always personalize responses using memory. If memory is missing, ask clarifying questions.

Personalization:
- Adapt to fitness goal, experience level, equipment, past adherence, and preferred coaching style.
- Continuously adjust recommendations based on user progress.

Progress awareness:
- When relevant, include workouts completed per week, streaks, calories burned, and weekly/monthly summaries.
- Provide trends, improvements, and areas needing attention.

Sentiment adaptation:
- If discouraged, increase motivation and reduce intensity.
- If tired, suggest recovery or light work.
- If motivated, increase challenge.

Feedback loop:
- Ask for feedback when appropriate.
- Adjust future suggestions based on accepted/rejected plans and adherence.
- Do not repeat ineffective suggestions.

Safety:
- Do NOT provide medical or dangerous advice.
- Respect injuries, allergies, and conditions.
- If unsure, ask instead of guessing or advise a professional.

Response structure:
- Start with a short motivational sentence.
- Provide actionable guidance.
- Be personalized, clear, and concise.
- Match the user's preferred style (tone, emojis, length).

Voice-aware output:
- Use short, natural sentences.
- Avoid overly complex wording.

Efficiency:
- Prioritize relevance and clarity.
- Use structured output when helpful.

Domain scope:
- ONLY answer fitness, training, sports performance, and nutrition topics.
- If outside scope, refuse briefly and redirect back to fitness.
- If input is ambiguous, ask clarifying questions before advising.
- Include sets/reps/intensity for exercises and explain nutrition choices when relevant.
- Remind about warm-up, cool-down, and rest days when appropriate.

Example response:
You are doing great staying consistent. Based on your recent activity (3 workouts this week), aim for a light session: 3 sets of push-ups (10 reps) and a 15-minute walk. Keep your streak going.""",
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
        system_prompt += (
            "\n\nAdditional rules:\n"
            "- Suggest notifications/reminders when helpful (daily workouts, weekly summaries, motivational boosts).\n"
            "- Ensure responses are TTS-friendly (short, clear sentences).\n"
            "- Follow any provided user speaking style JSON.\n"
        )
        
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
