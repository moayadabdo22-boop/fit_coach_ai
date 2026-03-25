from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from .deps import get_user_id
from coach_agent_integration import EnhancedCoachAgent


router = APIRouter(prefix="/api/v1", tags=["ai"])

_agent: EnhancedCoachAgent | None = None


def _get_agent(user_id: str, language: str) -> EnhancedCoachAgent:
    global _agent
    if _agent is None:
        enable_training = os.getenv("ENABLE_TRAINING_PIPELINE", "true").lower() == "true"
        _agent = EnhancedCoachAgent(user_id=user_id, language=language, enable_training_pipeline=enable_training)
    return _agent


class ChatRequest(BaseModel):
    message: str
    language: str = "en"
    profile: dict[str, Any] | None = None


@router.post("/coach/chat")
async def coach_chat(payload: ChatRequest, user_id: str = Depends(get_user_id)) -> dict[str, Any]:
    agent = _get_agent(user_id, payload.language)
    reply = await agent.process_message(payload.message, stream=False, user_profile=payload.profile)
    return {"reply": reply, "user_id": user_id}

