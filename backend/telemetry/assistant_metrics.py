"""Assistant Prometheus metrics (§26): requests, tools, RAG, providers, voice, feedback."""

from prometheus_client import Counter, Histogram

CHAT_TOTAL = Counter(
    "croppilot_assistant_chat_total",
    "Assistant chat turns by provider and status.",
    ["provider", "status"],
)
TOOL_CALLS = Counter(
    "croppilot_assistant_tool_calls_total",
    "Assistant tool executions by tool and status.",
    ["tool", "status"],
)
RAG_FALLBACK = Counter(
    "croppilot_assistant_rag_fallback_total",
    "RAG vector failures served from the relational catalog.",
    ["reason"],
)
PROVIDER_COOLDOWN = Counter(
    "croppilot_assistant_provider_cooldown_total",
    "Provider failures that triggered cooldown.",
    ["provider"],
)
STT_ERRORS = Counter(
    "croppilot_assistant_stt_errors_total",
    "Speech-to-text failures by engine.",
    ["engine"],
)
TTS_ERRORS = Counter(
    "croppilot_assistant_tts_errors_total",
    "Text-to-speech failures by engine.",
    ["engine"],
)
FEEDBACK = Counter(
    "croppilot_assistant_feedback_total",
    "User feedback on assistant answers by rating.",
    ["rating"],
)
# OpenRouter tier routing (§46). Labels are bounded: provider is a fixed
# set, tier is 1/2/3/single/local — never raw model ids (cardinality).
PROVIDER_REQUESTS = Counter(
    "croppilot_assistant_provider_requests_total",
    "Assistant provider attempts by provider, tier and outcome.",
    ["provider", "tier", "status"],
)
PROVIDER_TOKENS = Counter(
    "croppilot_assistant_provider_tokens_total",
    "Provider-reported tokens by provider, tier and kind.",
    ["provider", "tier", "kind"],
)
TIER_SHIFTS = Counter(
    "croppilot_assistant_provider_tier_shifts_total",
    "OpenRouter tier moves by origin, destination and reason.",
    ["from_tier", "to_tier", "reason"],
)
REQUEST_LATENCY = Histogram(
    "croppilot_assistant_request_latency_seconds",
    "Assistant provider round-trip latency by provider and tier.",
    ["provider", "tier"],
)
