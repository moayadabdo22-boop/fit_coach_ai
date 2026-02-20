import logging
import json
from typing import Any

logger = logging.getLogger(__name__)


def log_event(event_type: str, user_id: str | None, data: dict[str, Any]) -> None:
    """Log structured events for monitoring and analysis."""
    log_data = {
        "event_type": event_type,
        "user_id": user_id,
        "data": data,
    }
    logger.info(json.dumps(log_data))


def log_error(error_type: str, user_id: str | None, error: Exception, context: dict[str, Any] | None = None) -> None:
    """Log errors with context for debugging."""
    log_data = {
        "error_type": error_type,
        "user_id": user_id,
        "message": str(error),
        "context": context or {},
    }
    logger.error(json.dumps(log_data), exc_info=True)


def log_agent_action(agent_name: str, action: str, user_id: str | None, details: dict[str, Any]) -> None:
    """Log agent actions for tracing."""
    log_data = {
        "agent": agent_name,
        "action": action,
        "user_id": user_id,
        "details": details,
    }
    logger.debug(json.dumps(log_data))
