"""Single bounded LangGraph agent.

START -> prepare_input -> agent -> conditional:
  direct answer -> finalize -> END
  tool call     -> validate -> execute -> agent (bounded loop)
  rag query     -> retrieve -> rerank -> agent (Phase 3 fills retrieval)
  ui action     -> validate -> emit -> finalize (Phase 4 fills validation)

Hard loop cap HARD_MAX_TOOL_STEPS applies regardless of configuration.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

import re
import structlog
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from opentelemetry import trace
from typing_extensions import TypedDict

from core.config import settings
from services.assistant.prompts import SYSTEM_PROMPT
from services.assistant.router import router
from services.assistant.tools_registry import tool_registry
from services.assistant.types import (
    ChatMessage,
    RequestRequirements,
    ToolEvent,
    UIAction,
)

logger = structlog.get_logger(__name__)
tracer = trace.get_tracer(__name__)

HARD_MAX_TOOL_STEPS = 10


class AgentState(TypedDict):
    messages: Annotated[list[dict[str, Any]], add_messages]
    steps: int
    tool_events: list[dict[str, Any]]
    citations: list[dict[str, Any]]
    ui_actions: list[dict[str, Any]]
    language: str
    route: str
    provider_name: str
    provider_model: str
    # Set by the overlap-retry node: step 0 answered directly despite a
    # forced tool call, so the next agent pass forces tools again (once).
    overlap_retried: bool


def _max_steps() -> int:
    return max(1, min(settings.ASSISTANT_MAX_TOOL_STEPS, HARD_MAX_TOOL_STEPS))


def _msg_dict(m: Any) -> dict[str, Any]:
    """Normalize a LangGraph message (dict or langchain Message) to a dict."""
    if isinstance(m, dict):
        return m
    role = {
        "human": "user", "ai": "assistant", "tool": "tool", "system": "system",
    }.get(str(getattr(m, "type", "user")), "user")
    d: dict[str, Any] = {"role": role, "content": getattr(m, "content", "") or ""}
    calls = getattr(m, "tool_calls", None) or []
    norm = []
    for c in calls:
        if isinstance(c, dict):
            norm.append({
                "id": c.get("id", ""),
                "name": c.get("name", ""),
                "arguments": c.get("args", c.get("arguments", {})) or {},
            })
        else:
            norm.append(c)
    if norm:
        d["tool_calls"] = norm
    tool_call_id = getattr(m, "tool_call_id", None)
    if tool_call_id:
        d["tool_call_id"] = tool_call_id
    if getattr(m, "name", None):
        d["name"] = m.name  # type: ignore[attr-defined]
    return d


def _to_provider_messages(messages: list[dict[str, Any]]) -> list[ChatMessage]:
    out: list[ChatMessage] = []
    for m in (_msg_dict(x) for x in messages):
        role = m.get("role", "user")
        if role == "human":
            role = "user"
        elif role == "ai":
            role = "assistant"
        out.append(
            ChatMessage(
                role=role,
                content=m.get("content", ""),
                tool_calls=m.get("tool_calls", []),
                tool_call_id=m.get("tool_call_id"),
                name=m.get("name"),
            )
        )
    return out


def prepare_input(state: AgentState) -> dict[str, Any]:
    # Emits counters only, never messages. run_agent prepends the system
    # prompt once: re-emitting it here makes add_messages dedup the
    # identical user turn and leaves order as [user, system], which
    # confuses tool-calling models into narrating phantom API calls.
    return {"steps": 0, "tool_events": [], "citations": [], "ui_actions": []}


# Step-0 tool forcing: small local models answer factual questions from
# weights (hallucinated prices) instead of calling tools. When the user
# turn looks factual, force a tool call on the first step. Greetings and
# help requests stay free-form. Keywords cover en/hi/te + transliteration.
_FACTUAL_RE = re.compile(
    r"price|rate|bhav|bhaav|dam|mandi|market|bazaar|weather|mausam|varsham|"
    r"rain|varsha|scheme|yojana|pathakam|msp|support price|crop|pant|panta|"
    r"అమ్మకం|ధర|మార్కెట్|विक्रय|भाव|मंडी|मौसम|योजना|फसल|"
    r"MSP|MSP\)|quintal|quintol|arrival|arrivals|forecast|advisory|disease|"
    r"rog|రోగ|रोग|pest|profit|labh|లాభ|लाभ|subsidy|loan|insurance|bima|"
    r"बीमा|benefit|kisan|rythu|రైతు|रैत|eligib|sow|sowing|harvest|irrigat|fertili|variety|grade|"
    r"pmfby|pm-kisan|pmkisan",
    re.IGNORECASE,
)
_SMALLTALK_RE = re.compile(
    r"^(hi|hii+|hello|hey|namaste|namaskaram|vanakkam|thanks|thank you|"
    r"bye|good (morning|afternoon|evening)|who are you|what can you do|help)\b",
    re.IGNORECASE,
)


def _looks_factual(text: str) -> bool:
    text = (text or "").strip()
    if not text or _SMALLTALK_RE.search(text):
        return False
    return bool(_FACTUAL_RE.search(text))


def _is_smalltalk(text: str) -> bool:
    return bool(_SMALLTALK_RE.search((text or "").strip()))


# Per-family routing for dynamic tool filtering (Phase B latency work).
# Step 0 offers only families matching the user turn; follow-up steps
# offer everything (the model is already engaged and may need any tool).
#
# Scheme tools are gated on explicit scheme intent (_SCHEME_RE): a query
# matching no family at all ("Best practices for wheat cultivation") gets
# every family EXCEPT schemes. A crop name alone must never route to
# scheme tools — the model would otherwise call schemes_list for general
# knowledge and report "no relevant schemes".
_SCHEME_RE = re.compile(
    r"scheme|yojana|yojna|pathakam|subsidy|pension|pmfby|pm-kisan|pmkisan|"
    r"kisan|rythu|రైతు|रैत|bandhu|kalia|mgnrega|bima|बीमा|eligib|loan|credit|"
    r"sarkari|fasal|kcc|insurance|योजना",
    re.IGNORECASE,
)
_FAMILY_RES: dict[str, re.Pattern[str]] = {
    "market": re.compile(
        r"price|rate|bhav|bhaav|dam|mandi|market|bazaar|msp|quintal|quintol|"
        r"arrival|variety|grade|crop|pant|panta|sow|sowing|harvest|ధర|మార్కెట్|भाव|मंडी",
        re.IGNORECASE,
    ),
    "weather": re.compile(
        r"weather|mausam|varsham|rain|varsha|forecast|मौसम|irrigat",
        re.IGNORECASE,
    ),
    "schemes": _SCHEME_RE,
    "disease": re.compile(
        r"disease|rog|రోగ|रोग|pest|advisory|blast|blight|mildew|wilt|"
        r"rot|fung|virus|insect|treatment|symptom|spray|pesticide",
        re.IGNORECASE,
    ),
    "planning": re.compile(
        r"profit|labh|లాభ|लाभ|cost|fertili", re.IGNORECASE,
    ),
}


def _families_for(text: str) -> set[str]:
    text = text or ""
    hit = {fam for fam, rx in _FAMILY_RES.items() if rx.search(text)}
    if not hit:
        # No family matched: offer everything except schemes (scheme tools
        # require explicit scheme intent; see _SCHEME_RE). Never zero tools.
        hit = set(_FAMILY_RES) - {"schemes"}
    return hit


_NAV_RE = re.compile(
    r"\b(open|navigate|go to)\b.*\b(page|app|screen|dashboard)\b",
    re.IGNORECASE,
)


def classify_intent(text: str) -> str:
    """Route a user turn to one intent category.

    GENERAL_AGRICULTURAL_KNOWLEDGE | GOVERNMENT_SCHEME | MARKET |
    WEATHER | DISEASE | PROFIT | UI_NAVIGATION | OTHER.
    """
    t = (text or "").strip()
    if not t or _is_smalltalk(t):
        return "OTHER"
    if _NAV_RE.search(t):
        return "UI_NAVIGATION"
    if _SCHEME_RE.search(t):
        return "GOVERNMENT_SCHEME"
    hit = {fam for fam, rx in _FAMILY_RES.items() if rx.search(t)}
    if "market" in hit:
        return "MARKET"
    if "weather" in hit:
        return "WEATHER"
    if "disease" in hit:
        return "DISEASE"
    if "planning" in hit:
        return "PROFIT"
    return "GENERAL_AGRICULTURAL_KNOWLEDGE"


async def agent_node(state: AgentState) -> dict[str, Any]:
    provider_messages = _to_provider_messages(state["messages"])
    # Gate on the last user turn (never the system prompt, which contains
    # tooling vocabulary that would false-positive the heuristic).
    last_user = next((m.content for m in reversed(provider_messages) if m.role == "user"), "")
    step = state.get("steps", 0)
    fast_path = _is_smalltalk(last_user)
    general_path = not fast_path and classify_intent(last_user) == "GENERAL_AGRICULTURAL_KNOWLEDGE"
    if fast_path or general_path:
        # Greetings/smalltalk and general knowledge: no tools offered at
        # all. Smaller prompt = faster prefill on CPU; nothing factual can
        # be hallucinated, and the model cannot misuse unrelated tools
        # (e.g. calling schemes_list for "wheat cultivation" advice).
        specs: list[dict[str, Any]] = []
        families: set[str] = set()
    elif step == 0:
        families = _families_for(last_user)
        specs = tool_registry.specs_for(families)
    else:
        families = set(_FAMILY_RES)
        specs = tool_registry.specs()
    requirements = RequestRequirements(function_calling=bool(specs))
    # Force a tool call on step 0 for factual questions. run_agent always
    # offers specs, so specs non-empty here means tools are available.
    # The overlap retry re-forces when step 0 answered directly despite
    # forcing (small models sometimes ignore tool_choice).
    factual = _looks_factual(last_user)
    force = (
        "required"
        if (specs and step == 0 and (factual or state.get("overlap_retried")))
        else None
    )
    with tracer.start_as_current_span("assistant.agent") as span:
        span.set_attribute("assistant.steps", step)
        span.set_attribute("assistant.tools_offered", len(specs))
        span.set_attribute("assistant.tool_families", ",".join(sorted(families)))
        span.set_attribute("assistant.fast_path", fast_path)
        span.set_attribute("assistant.general_path", general_path)
        span.set_attribute("assistant.overlap_retry", bool(state.get("overlap_retried")))
        result = await router.chat(provider_messages, tools=specs or None, requirements=requirements, tool_choice=force)
    message: dict[str, Any] = {"role": "assistant", "content": result.message.content}
    if result.message.tool_calls:
        # langchain AIMessage shape (args, not arguments).
        message["tool_calls"] = [
            {"name": t.name, "args": t.arguments, "id": t.id, "type": "tool_call"}
            for t in result.message.tool_calls
        ]
    return {
        "messages": [message],
        "provider_name": result.provider,
        "provider_model": result.model,
    }


def decide_route(state: AgentState) -> Literal["tools", "finalize", "retry"]:
    last = _msg_dict(state["messages"][-1])
    calls = last.get("tool_calls") or []
    # UI actions and RAG travel as tools; execution node sorts them out.
    if calls and state.get("steps", 0) < _max_steps():
        return "tools"
    if calls:
        logger.warning("assistant_max_steps", steps=state.get("steps"))
        return "finalize"
    # Overlap force-gate: step 0 looked factual (force was attempted) but
    # the model answered directly with no tool call. Retry the agent pass
    # once with tools re-forced instead of accepting a possibly
    # hallucinated answer. One retry only, then accept the answer.
    # Skipped for general knowledge: no tools were offered, so there is
    # nothing to force on retry.
    if state.get("steps", 0) == 0 and not state.get("overlap_retried"):
        flat = [_msg_dict(m) for m in state["messages"]]
        last_user = next((m.get("content", "") for m in reversed(flat) if m.get("role") == "user"), "")
        if _looks_factual(last_user) and classify_intent(last_user) != "GENERAL_AGRICULTURAL_KNOWLEDGE":
            logger.info("assistant_overlap_retry")
            return "retry"
    return "finalize"


def mark_retry(state: AgentState) -> dict[str, Any]:
    return {"overlap_retried": True}


# Tools whose successful calls deterministically drive a markets-page action.
# The action mirrors the exact arguments the tool executed with, so the UI
# can deep-link to the same data. No LLM involvement: emission is a pure
# function of (tool name, args, success).
_MARKET_ACTION_TOOLS = frozenset({"market_latest", "market_history", "market_compare"})
_MARKET_FILTER_KEYS = ("state", "district", "market", "commodity", "variety", "grade")


def _market_ui_action(
    name: str, args: dict[str, Any], output: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    if name not in _MARKET_ACTION_TOOLS or not isinstance(args, dict):
        return None
    payload = {k: v for k, v in args.items() if k in _MARKET_FILTER_KEYS and isinstance(v, str) and v.strip()}
    if not payload:
        return None
    # Prefer the tool's resolved canonical values: raw model args
    # ("paddy", state "Nalgonda") would land the markets page on empty
    # exact filters, while resolved values show the same data the tool
    # read. Scope (state/district/market) overrides first, then commodity.
    # Dropped filters (unresolvable raw values) are removed from the
    # payload so the deep-link never points at a guaranteed-empty view.
    scope = (output or {}).get("resolved_scope") if isinstance(output, dict) else None
    if isinstance(scope, dict):
        for key in ("state", "district", "market"):
            value = scope.get(key)
            if isinstance(value, str) and value.strip():
                payload[key] = value
    dropped = (output or {}).get("dropped_filters") if isinstance(output, dict) else None
    if isinstance(dropped, list):
        dropped_kinds = set()
        for entry in dropped:
            if isinstance(entry, str) and "=" in entry:
                dropped_kinds.add(entry.split("=", 1)[0])
        for key in list(payload):
            if key in dropped_kinds and key not in (scope or {}):
                del payload[key]
    resolved = (output or {}).get("resolved_commodity") if isinstance(output, dict) else None
    if isinstance(resolved, list) and resolved:
        payload["commodity"] = str(resolved[0])
    elif isinstance(resolved, str) and resolved.strip():
        payload["commodity"] = resolved
    return {"action": "apply-market-filters", "payload": payload}


def _tool_citations(output: Any) -> list[dict[str, Any]]:
    """Citations embedded in a tool result (RAG search). Never raises."""
    if not isinstance(output, dict):
        return []
    cites = output.get("citations")
    if not isinstance(cites, list):
        return []
    return [c for c in cites if isinstance(c, dict) and (c.get("title") or c.get("source"))]


async def execute_tools(state: AgentState, context: dict[str, Any]) -> dict[str, Any]:
    last = _msg_dict(state["messages"][-1])
    followups: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []
    actions: list[dict[str, Any]] = list(state.get("ui_actions", []))
    cites: list[dict[str, Any]] = list(state.get("citations", []))
    for call in last.get("tool_calls") or []:
        name = str(call.get("name") or "")
        # agent_node emits langchain-shaped calls ("args"); providers and
        # tests may use OpenAI-shaped calls ("arguments"). Accept both.
        args = call.get("arguments", call.get("args")) or {}
        output, event = await tool_registry.execute(name, args, context)
        events.append(event.model_dump())
        if event.status == "succeeded":
            derived = _market_ui_action(
                name, args if isinstance(args, dict) else {},
                output if isinstance(output, dict) else None,
            )
            if derived is not None:
                actions.append(derived)
            for cite in _tool_citations(output):
                key = (str(cite.get("source") or ""), str(cite.get("title") or ""))
                if key not in {(str(c.get("source") or ""), str(c.get("title") or "")) for c in cites}:
                    cites.append(cite)
        followups.append(
            {
                "role": "tool",
                "content": _truncate(str(output)),
                "tool_call_id": call.get("id", ""),
                "name": name,
            }
        )
    return {
        "messages": followups,
        "tool_events": state.get("tool_events", []) + events,
        "citations": cites[:12],
        "ui_actions": actions,
        "steps": state.get("steps", 0) + 1,
    }


def _truncate(text: str, limit: int = 4000) -> str:
    return text if len(text) <= limit else text[:limit] + "...[truncated]"


def finalize(state: AgentState) -> dict[str, Any]:
    return {}


def build_agent_graph(context: dict[str, Any]):
    """Compile the graph bound to a request context (user, conversation)."""

    async def _execute(state: AgentState) -> dict[str, Any]:
        return await execute_tools(state, context)

    graph = StateGraph(AgentState)
    graph.add_node("prepare_input", prepare_input)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", _execute)
    graph.add_node("mark_retry", mark_retry)
    graph.add_node("finalize", finalize)
    graph.set_entry_point("prepare_input")
    graph.add_edge("prepare_input", "agent")
    graph.add_conditional_edges("agent", decide_route, {"tools": "tools", "finalize": "finalize", "retry": "mark_retry"})
    graph.add_edge("mark_retry", "agent")
    graph.add_edge("tools", "agent")
    graph.add_edge("finalize", END)
    return graph.compile()


async def run_agent(
    user_message: str,
    context: dict[str, Any],
    language: str = "en",
    history: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Run one bounded turn. Returns text, events, citations, ui actions, provider."""
    app = build_agent_graph(context)
    messages: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(
        {"role": h["role"], "content": h["content"]}
        for h in (history or [])
        if h.get("role") in ("user", "assistant") and h.get("content")
    )
    messages.append({"role": "user", "content": user_message})
    initial: dict[str, Any] = {
        "messages": messages,
        "language": language,
        "route": "",
    }
    final = await app.ainvoke(initial)  # type: ignore[arg-type]
    flat = [_msg_dict(m) for m in final["messages"]]
    texts = [m.get("content", "") for m in flat if m.get("role") == "assistant" and m.get("content")]
    provider_name = final.get("provider_name", "")
    provider_model = final.get("provider_model", "")
    return {
        "text": texts[-1] if texts else "",
        "tool_events": [ToolEvent(**e) for e in final.get("tool_events", [])],
        "citations": final.get("citations", []),
        "ui_actions": [UIAction(**a) for a in final.get("ui_actions", [])],
        "provider": {"name": provider_name, "model": provider_model},
    }
