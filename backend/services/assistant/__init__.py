"""CropPilot AI Assistant package.

Single bounded LangGraph agent, provider-agnostic. Local-first: works
with Ollama alone, no API key required. Optional free-tier cloud
providers accelerate when configured.
"""

from services.assistant.service import AssistantService, assistant_service
from services.assistant.tools_registry import tool_registry

__all__ = ["AssistantService", "assistant_service", "tool_registry"]
