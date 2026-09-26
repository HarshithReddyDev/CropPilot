# AI Assistant API contract

Base: `/api/v1/assistant`. Auth: bearer JWT, or dev bypass (`_dev_user`) when
`DEV_AUTH_BYPASS=true`. Legacy `/api/v1/intel/*` is superseded, unchanged.

## POST /assistant/chat

Non-streaming turn. Loads last-6-turn history, runs the agent, persists both
turns, returns server `conversation_id` (client must adopt it for follow-ups).

Request:

```json
{
  "message": "Paddy price in Nalgonda?",
  "conversation_id": "00000000-0000-0000-0000-000000000000",
  "state": "Telangana",
  "commodity": "Paddy",
  "h3_index": null,
  "language": "en"
}
```

`message` max 4000 chars. `conversation_id` optional; unknown/other-user ids
start a fresh conversation (never 404, never leak).

Response `200 ChatResponse`:

```json
{
  "text": "…",
  "conversation_id": "…",
  "provider": {"name": "ollama", "model": "qwen3:8b"},
  "citations": [{"source": "scheme:PM-KISAN", "title": "PM-KISAN",
                 "snippet": "…", "score": 0.9}],
  "ui_actions": [{"action": "apply-market-filters",
                  "payload": {"commodity": "Paddy"}}],
  "tool_events": [{"tool": "market_latest", "status": "ok"}]
}
```

Errors: `400` empty/oversize message; `401` no token (prod); `503`
`assistant_unavailable` (no provider healthy — retryable); `500` never leaks
internals.

## POST /assistant/chat/stream (SSE)

Same semantics, `text/event-stream`. Event sequence:

```
event: provider   data: {"name":"ollama","model":"qwen3:8b"}
event: tool       data: {"tool":"market_latest","status":"started"}
event: tool       data: {"tool":"market_latest","status":"ok"}
event: delta      data: {"text":"…"}          # many
event: final      data: {<ChatResponse without text deltas>}
event: error      data: {"code":"…","message":"…"}   # instead of final on failure
```

Client: render `delta` incrementally; on `final`, adopt `conversation_id`,
render citations, execute `ui_actions`. `AbortController` cancels cleanly.

## GET /assistant/conversations → ConversationOut[]

```json
[{"id": "…", "title": "Paddy price…", "updated_at": "…"}]
```

Newest first, caller-owned only.

## GET /assistant/conversations/{id} → MessageOut[]

```json
[{"role": "user", "content": "…", "provider": null, "created_at": "…"}]
```

Other-user id → `404`. Roles `user|assistant` oldest first.

## POST /assistant/feedback → 204

```json
{"message_id": "…", "rating": "up", "comment": "…"}
```

`rating` must be `up|down` (`422` otherwise). Recorded as Prometheus
`assistant_feedback_total{rating}` + memory kv. `message_id` is opaque in v1
(not resolved to a row).

## GET /assistant/capabilities / GET /assistant/health

```json
// capabilities
{"llm": ["ollama"], "rag": true, "voice": false,
 "ui_actions": ["open-market", "follow-market", "apply-market-filters",
                "open-article", "play-audio"],
 "limits": {"max_tool_steps": 5, "request_timeout_s": 60,
            "max_message_chars": 4000}}
// health (model_ready distinguishes service-up from model-loaded;
// model_probe_ms is the /api/tags probe latency; negative results are
// never cached, positive cached 60s)
{"enabled": true, "configured_providers": ["ollama"],
 "model_ready": true, "model_probe_ms": 12.0, "model": "llama3.1:8b"}
```

`voice: false` until an ASR engine is configured.

Capabilities also carries a safe `openrouter` block (no keys, no usage):

```json
{"openrouter": {"enabled": true, "tiering": true, "fallback": "ollama",
 "tiers": [{"tier": 1, "model": "...:free", "enabled": true,
            "tool_calling": true}]}}
```

## GET /assistant/providers/usage (admin only)

Today's per-tier counters vs configured budgets (UTC date bucket).
Requires admin auth; farmer UI must not call this.

```json
{"enabled": true, "tiering": true, "ollama": {"model": "llama3.1:8b"},
 "tiers": [{"tier": 1, "model": "...:free", "requests": 3,
            "prompt_tokens": 120, "completion_tokens": 40, "total_tokens": 160,
            "configured_max_requests": 20, "configured_max_tokens": 100000,
            "status": "active"}]}
```

## WebSocket /ws/voice (top-level, not under /api/v1)

Query: `?lang=en&token=<JWT>` (token optional under dev bypass). Close codes:
`4401` unauthenticated, `4400` malformed first frame.

Client → server:

```json
{"type": "config", "language": "te", "persist_audio": false}
{"type": "audio", "data": "<base64 pcm16 16kHz mono ≤4096 chars>"}
{"type": "commit"}   // transcribe buffered audio, run turn
{"type": "stop"}     // barge-in: cancel current turn
```

Server → client:

```json
{"type": "ready", "asr": "disabled", "tts": "disabled"}
{"type": "interim", "text": "…"}        // optional, engine-dependent
{"type": "final", "text": "…"}          // transcript; then turn runs
{"type": "response", "text": "…",
 "citations": [], "ui_actions": []}     // then optional audio frames
{"type": "audio", "data": "<base64 wav>"}  // 3 KB frames, only if TTS active
{"type": "audio_end"}
{"type": "error", "code": "asr_unavailable", "message": "…"}
```

Error codes: `bad_config | empty_audio | voice_disabled | asr_unavailable |
tts_unavailable | persistence_disabled | turn_cancelled | internal_error`.
Audio errors never break the text path: `commit` with ASR disabled still runs
the turn when `text` is supplied alongside.

## Conversation lifecycle

1. Client sends message without `conversation_id` → server creates UUID,
   returns it; client stores and sends it on follow-ups.
2. History = last 6 turns, oldest first, injected into the agent prompt.
3. Turns are append-only; messages are never edited or deleted via API v1.
4. `GET /conversations` restores the sidebar; `GET /…/{id}` restores a thread.
5. Feedback is fire-and-forget (`204`).

## Postman quickstart

```
POST {{base}}/api/v1/assistant/chat
Authorization: Bearer {{token}}   # omit when DEV_AUTH_BYPASS=true
Content-Type: application/json
{"message": "MSP for wheat?", "state": "Telangana"}

GET {{base}}/api/v1/assistant/health
GET {{base}}/api/v1/assistant/capabilities
GET {{base}}/api/v1/assistant/conversations
```

WS: connect `ws://localhost:8000/ws/voice?lang=en`, send `config`, stream
`audio` frames, send `commit`, read `final` + `response`.
