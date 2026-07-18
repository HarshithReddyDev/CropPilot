from typing import Annotated, Literal, TypedDict

from langchain_core.messages import AnyMessage
from langchain_community.chat_models import ChatOllama
from langgraph.graph import END, StateGraph, MessagesState
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages

from agents.tools import agents_tools
from core.config import settings

llm = ChatOllama(
    model=settings.OLLAMA_MODEL,
    base_url=settings.OLLAMA_BASE_URL,
    temperature=0.3,
)
llm_with_tools = llm.bind_tools(agents_tools)
tool_node = ToolNode(agents_tools)


class CropilotState(MessagesState):
    sources: list[dict]


def should_continue(state: CropilotState) -> Literal["tools", "__end__"]:
    messages = state["messages"]
    last_message = messages[-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return "__end__"


def call_model(state: CropilotState) -> dict:
    messages = state["messages"]
    system_message = {
        "role": "system",
        "content": (
            "You are CropPilot AI, an expert agricultural assistant for Indian farmers. "
            "You provide advice on: crop management, disease detection, weather, "
            "market prices, government schemes, and farm planning.\n\n"
            "Guidelines:\n"
            "- Be concise and practical in your advice\n"
            "- Use the available tools to gather real-time data\n"
            "- Always cite your sources when providing market prices\n"
            "- Consider the farmer's location when recommending schemes\n"
            "- Provide actionable next steps\n"
            "- If you don't know something, use a tool rather than guessing"
        ),
    }
    response = llm_with_tools.invoke([system_message] + messages)
    return {"messages": [response]}


cropilot_workflow = StateGraph(CropilotState)
cropilot_workflow.add_node("agent", call_model)
cropilot_workflow.add_node("tools", tool_node)
cropilot_workflow.set_entry_point("agent")
cropilot_workflow.add_conditional_edges("agent", should_continue)
cropilot_workflow.add_edge("tools", "agent")
cropilot_agent = cropilot_workflow.compile()


class IntelState(TypedDict):
    incident_id: str
    messages: Annotated[list, add_messages]


def intel_should_continue(state: IntelState) -> Literal["tools", "__end__"]:
    messages = state["messages"]
    last_message = messages[-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return "__end__"


def intel_call_model(state: IntelState) -> dict:
    messages = state["messages"]
    system_message = {
        "role": "system",
        "content": (
            "You are the Intel Engine for CropPilot. Your job is to analyze a disease incident "
            "and provide comprehensive intelligence including:\n"
            "1. Current market prices for the affected crop\n"
            "2. Relevant government schemes that could help\n"
            "3. Weather conditions and forecast\n"
            "4. Treatment recommendations\n\n"
            "Be thorough and data-driven. Always use tools to gather real information."
        ),
    }
    response = llm_with_tools.invoke([system_message] + messages)
    return {"messages": [response]}


intel_workflow = StateGraph(IntelState)
intel_workflow.add_node("agent", intel_call_model)
intel_workflow.add_node("tools", tool_node)
intel_workflow.set_entry_point("agent")
intel_workflow.add_conditional_edges("agent", intel_should_continue)
intel_workflow.add_edge("tools", "agent")
intel_agent = intel_workflow.compile()
