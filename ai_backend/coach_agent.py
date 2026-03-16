from typing import Iterator
import json
from memory_system import MemorySystem
from domain_router import DomainRouter
from moderation_layer import ModerationLayer
from llm_client import LLMClient
from tools_system import ToolExecutor
from ai_engine import AIEngine
from data_catalog import DataCatalog
from dataset_paths import resolve_dataset_root, resolve_derived_root
from rag_context import RagContextBuilder
from recommendation_engine import RecommendationEngine
from utils_logger import log_event, log_agent_action


class CoachAgent:
    """Main coach agent - orchestrates all components."""
    
    def __init__(
        self,
        user_id: str | None = None,
        language: str = "en",
        supabase_client=None,
        exercises_path: str | None = None,
        catalog: DataCatalog | None = None,
        recommender: RecommendationEngine | None = None,
    ):
        self.user_id = user_id
        self.language = language
        self.supabase = supabase_client
        
        # Initialize components
        self.memory = MemorySystem(user_id, max_short_term=10)
        self.domain_router = DomainRouter(threshold=0.35)
        self.moderation = ModerationLayer()
        self.llm = LLMClient()
        self.catalog = catalog or DataCatalog(resolve_dataset_root(), resolve_derived_root())
        self.recommender = recommender or RecommendationEngine(self.catalog)
        self.tools = ToolExecutor(supabase_client, catalog=self.catalog, recommender=self.recommender)
        data_path = exercises_path
        if not data_path:
            derived_path = resolve_derived_root() / "exercises.json"
            data_path = str(derived_path) if derived_path.exists() else "./ai_backend/exercises.json"
        self.ai_engine = AIEngine(data_path)
        self.rag_builder = RagContextBuilder(self.catalog)
    
    async def process_message(
        self,
        user_message: str,
        stream: bool = False,
    ) -> str | Iterator[str]:
        """
        Process a user message and generate a response.
        
        Args:
            user_message: The user's input
            stream: Whether to stream the response
            
        Returns:
            Response text or iterator of text chunks
        """
        log_agent_action("CoachAgent", "process_message", self.user_id, {
            "message_length": len(user_message),
            "stream": stream,
        })
        
        # Step 1: Domain check
        is_in_domain, confidence = self.domain_router.is_in_domain(
            user_message,
            self.language,
        )
        
        if not is_in_domain:
            out_of_domain_response = self.domain_router.get_out_of_domain_response(
                self.language
            )
            self.memory.add_user_message(user_message)
            self.memory.add_assistant_message(out_of_domain_response)
            return out_of_domain_response
        
        # Step 2: Add to memory
        self.memory.add_user_message(user_message)
        
        # Step 3: Content moderation on input
        filtered_input, has_bad_words = self.moderation.filter_content(
            user_message,
            self.language,
        )
        
        if has_bad_words:
            warning = self.moderation.get_safe_fallback(self.language)
            self.memory.add_assistant_message(warning)
            return warning
        
        # Step 4: Build context for LLM
        system_prompt = self.memory.get_system_prompt(self.language)
        conversation_history = self.memory.get_conversation_history()
        
        # Step 5: Get relevant exercises from RAG if needed
        rag_context = self._get_rag_context(user_message)
        
        # Step 6: Call LLM with tools
        if stream:
            response_text = self._stream_response(
                system_prompt,
                conversation_history,
                rag_context,
            )
        else:
            response_text = await self._get_response(
                system_prompt,
                conversation_history,
                rag_context,
            )
        
        # Step 7: Apply content moderation to response
        filtered_response, _ = self.moderation.filter_content(
            response_text if isinstance(response_text, str) else response_text,
            self.language,
        )
        
        # Step 8: Store in memory
        self.memory.add_assistant_message(filtered_response)
        
        # Step 9: Log the interaction
        log_agent_action("CoachAgent", "response_generated", self.user_id, {
            "response_length": len(filtered_response),
            "used_rag": bool(rag_context),
        })
        
        return filtered_response if stream is False else iter([filtered_response])
    
    def _get_rag_context(self, user_message: str, top_k: int = 3) -> str:
        """
        Get relevant exercise/nutrition context using RAG.

        Args:
            user_message: User query
            top_k: Number of relevant items to retrieve

        Returns:
            Context string to include in LLM prompt
        """
        try:
            return self.rag_builder.build(user_message, top_k=top_k)
        except Exception as e:
            log_agent_action("CoachAgent", "rag_error", self.user_id, {"error": str(e)})
            return ""


    async def _get_response(
        self,
        system_prompt: str,
        conversation_history: list[dict],
        rag_context: str,
    ) -> str:
        """
        Get response from LLM (non-streaming).
        
        Args:
            system_prompt: System instructions
            conversation_history: Previous messages
            rag_context: RAG knowledge base context
            
        Returns:
            LLM response
        """
        messages = [
            {"role": "system", "content": system_prompt},
        ]
        
        # Add RAG context if available
        if rag_context:
            messages.append({
                "role": "system",
                "content": f"Knowledge Base Context:\n{rag_context}",
            })
        
        # Add conversation history
        messages.extend(conversation_history)
        
        # Get tools for tool calling
        tools = self.tools.registry.get_tool_definitions()
        
        # Call LLM
        response = await self._call_llm_with_tools(messages, tools)
        
        return response
    
    def _stream_response(
        self,
        system_prompt: str,
        conversation_history: list[dict],
        rag_context: str,
    ) -> Iterator[str]:
        """
        Stream response from LLM.
        
        Args:
            system_prompt: System instructions
            conversation_history: Previous messages
            rag_context: RAG context
            
        Yields:
            Text chunks as they arrive
        """
        messages = [
            {"role": "system", "content": system_prompt},
        ]
        
        if rag_context:
            messages.append({
                "role": "system",
                "content": f"Knowledge Base Context:\n{rag_context}",
            })
        
        messages.extend(conversation_history)
        
        # Stream from LLM
        for chunk in self.llm.chat_completion_stream(
            messages,
            temperature=0.7,
            max_tokens=1024,
        ):
            yield chunk
    
    async def _call_llm_with_tools(
        self,
        messages: list[dict],
        tools: list[dict],
    ) -> str:
        """
        Call LLM and handle tool calling if needed.
        
        Args:
            messages: Message history
            tools: Available tools
            
        Returns:
            Final response after tool execution if needed
        """
        # For now, return direct response
        # Tool calling implementation would go here
        response = self.llm.chat_completion(
            messages,
            temperature=0.7,
            max_tokens=1024,
            tools=tools if tools else None,
        )
        
        # If response is a string, return it
        if isinstance(response, str):
            return response
        
        # If response contains tool calls, execute them
        # This would be enhanced in production
        if hasattr(response, 'tool_calls') and response.tool_calls:
            return self._handle_tool_calls(response.tool_calls, messages)
        
        return str(response)
    
    def _handle_tool_calls(self, tool_calls: list, messages: list[dict]) -> str:
        """Handle tool calling from LLM."""
        # This is a placeholder - production implementation would
        # execute tools and call LLM again with results
        log_agent_action("CoachAgent", "tool_calls_detected", self.user_id, {
            "count": len(tool_calls),
        })
        
        return "I'd like to help with that, but this requires additional processing."
    
    def get_conversation_history(self) -> list[dict]:
        """Get full conversation history."""
        return self.memory.short_term.get_full_history()
    
    def clear_conversation(self) -> None:
        """Clear conversation history."""
        self.memory.clear_short_term()
        log_agent_action("CoachAgent", "conversation_cleared", self.user_id, {})
