"""Semantic UI action registry (§16).

The agent may emit UI actions alongside text. Only actions listed here
reach the client; unknown or malformed actions are dropped by
validate_ui_actions() before the response leaves the backend.
"""

from __future__ import annotations

from services.assistant.types import UIAction

# action name -> (required payload keys, optional payload keys)
ACTION_SPECS: dict[str, tuple[frozenset[str], frozenset[str]]] = {
    "open-market": (frozenset({"commodity"}), frozenset({"state", "district", "market"})),
    "follow-market": (frozenset({"commodity"}), frozenset({"state", "district", "market"})),
    "apply-market-filters": (
        frozenset(),
        frozenset({"state", "district", "market", "commodity", "variety", "grade", "days"}),
    ),
    "open-article": (frozenset({"article_id"}), frozenset({"title"})),
    "play-audio": (frozenset({"audio_id"}), frozenset()),
    # V1.3 read-aloud: frontend determines eligible readable content
    # (bounded, structured); the backend never scrapes DOM.
    "page.read_aloud": (frozenset({"section"}), frozenset()),
    # V1.3 page-aware actions. Pages are allow-listed route names (never
    # URLs); language codes must exist in the canonical registry.
    "navigation.open_page": (frozenset({"page"}), frozenset()),
    "assistant.set_language": (frozenset({"language"}), frozenset()),
}

#: Pages the assistant may navigate to. Route names only — the frontend
#: maps these to its own routes; arbitrary URLs are never allowed.
ALLOWED_PAGES = frozenset({
    "dashboard",
    "markets",
    "weather",
    "disease-detection",
    "schemes",
    "analytics",
    "maps",
    "ai-assistant",
})


def allowed_actions() -> list[str]:
    return sorted(ACTION_SPECS)


def _valid_values(name: str, payload: dict) -> bool:
    """Value-level checks for actions whose payloads are closed sets."""
    if name == "navigation.open_page":
        return payload.get("page") in ALLOWED_PAGES
    if name == "assistant.set_language":
        from services.assistant.languages import get_language

        code = payload.get("language")
        return isinstance(code, str) and get_language(code) is not None
    return True


def validate_ui_actions(raw: list[dict]) -> list[UIAction]:
    """Keep only well-formed, allow-listed actions. Never raises."""
    valid: list[UIAction] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        name = item.get("action")
        payload = item.get("payload")
        spec = ACTION_SPECS.get(name) if isinstance(name, str) else None
        if spec is None or not isinstance(payload, dict):
            continue
        assert isinstance(name, str)
        required, optional = spec
        if not required.issubset(payload):
            continue
        if any(not isinstance(v, (str, int, float, bool)) for v in payload.values()):
            continue
        if not _valid_values(name, payload):
            continue
        clean = {k: v for k, v in payload.items() if k in required or k in optional}
        valid.append(UIAction(action=name, payload=clean))
    return valid
