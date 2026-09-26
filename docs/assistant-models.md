# CropPilot Assistant — Model & Provider Behavior

Verified against the live OpenRouter API documentation (September 2026).
Only behavior confirmed there is implemented; assumptions are marked as such.

## Endpoint

`POST https://openrouter.ai/api/v1/chat/completions` — OpenAI-compatible.
Required headers: `Authorization: Bearer <key>`. Recommended:
`HTTP-Referer: <app url>`, `X-Title: <app name>` (CropPilot sends both).

## Usage accounting (the fields tier budgets rely on)

Non-streaming responses **always** carry:

```json
"usage": {
  "prompt_tokens": 25,
  "completion_tokens": 10,
  "total_tokens": 35,
  "cost": 0.00014
}
```

`prompt_tokens` includes images/audio/tools. `completion_tokens` includes
reasoning tokens. Counts use the model's native tokenizer. The `cost`
field is present but **never used for routing** — only token counts drive
tier budgets (cost is informational; free entries report 0).

Streaming: usage is emitted **exactly once, in the final chunk before
`[DONE]`**. Unlike OpenAI's spec (empty `choices` array), OpenRouter's
usage chunk carries a non-empty `choices` array with a content-free delta
repeating the stream's `finish_reason` — treat it as an accounting frame,
not a second terminal event. Full usage details are always included in
streams; the old `stream_options: {"include_usage": true}` flag is
**deprecated and has no effect**, so CropPilot does not send it.

Alternative audit path (not used in the hot path): `GET /api/v1/generation`
returns token counts/cost for a past generation `id`.

## Free models

A `:free` suffix denotes a distinct catalog entry: zero pricing, its own
rate limits, endpoints, and sometimes a shorter context window than the
base model. **Never strip `:free`** — that resolves to the paid entry.

- Free quota (no credits purchased): 50 free-model requests/day total.
- With ≥10 credits purchased: 1000 free-model requests/day.
- Per-minute free-model cap also applies (~20/min observed).
- Counter resets at **UTC midnight**; `GET /api/v1/key` reports the same
  `FreeModelDailyRequests{limit, remaining, used}` counter the enforcement
  reads. CropPilot's daily budget bucket is therefore UTC too.
- Requesting a model with no `:free` entry: single-model lookup 404s,
  endpoints lookup returns `"endpoints": []`, inference fails — treat as
  unavailable model, never retry with the base slug (that would be paid).

`:free` alone does not prove "free" at runtime; pricing lives in the
models catalog. CropPilot's config-level rule (model id must end in
`:free`) is an application guard, and a 404/empty-endpoints response
disables the tier at runtime. Paid routing is never attempted silently.

## Tool calling

Supported per model; the models catalog reports it via `supported_parameters`
(which includes `"tools"` when supported). Capability is operator-declared
per tier (`..._TOOL_CALLING`) and enforced at routing: a market/tool turn
never goes to a tier without it. OpenRouter also offers its own
provider-level fallback per model — acceptable, but **CropPilot decides the
model tier**; nested fallbacks are bounded (one tier attempt each, then next
tier, then Ollama).

## Errors (verified shapes)

```json
{"error": {"code": 429, "message": "Rate limit exceeded: free-models-per-min.",
 "metadata": {"headers": {"X-RateLimit-Limit": "20", "X-RateLimit-Remaining": "0",
 "X-RateLimit-Reset": "1785658140000"},
 "limit_source": "openrouter_free_tier_per_minute",
 "remedy_hint": "Slow down requests to free models..."}}}
```

- **429** comes from OpenRouter platform limits (per-min/per-day, DDoS) or
  the upstream provider (then `metadata.provider_code` carries the original
  code and OpenRouter already retried other providers for that model).
- **`Retry-After` is not dependable** for free-tier 429s (only set when
  every attempted provider returned a retry hint). The reset instant is
  `X-RateLimit-Reset` (Unix **milliseconds**) inside the error metadata.
  CropPilot maps 429 → next tier, never waits out the window inline.
- **Successful responses carry no `X-RateLimit-*` headers** — polling
  responses for quota state is useless. Pre-call quota checks use
  `GET /api/v1/key` (diagnostics only, not the hot path).
- Insufficient credits → **402**. Unknown model → **404**. Auth → 401/403.

## What CropPilot implements from this

| Verified fact | Implementation |
|---|---|
| `usage{prompt_tokens, completion_tokens, total_tokens}` non-stream | parsed in `chat()`, reconciled to tier budget |
| usage in final stream chunk, `include_usage` deprecated | parsed in `stream()` via `on_usage`; flag not sent |
| `:free` = distinct entry; strip = paid | config rejects non-`:free` tier models; 404 disables tier |
| free quota 50/1000 per day, UTC reset | local budgets are app-level caps; UTC date bucket |
| 429 body + `X-RateLimit-Reset` ms, no reliable `Retry-After` | 429 → immediate next tier |
| 402 = credits exhausted | 402 → `QUOTA_EXHAUSTED` → next tier |
| success has no rate-limit headers | no response-header quota tracking |
| per-model `supported_parameters` | operator-declared `TOOL_CALLING` per tier |

Local application budgets are **not** provider quotas: ours cap spend
before the provider does; provider 429/402 moves tiers regardless of
local budget state.

## V1.3 voice/translation model registry

Verified against live model cards/package metadata (2026-09-26).
Gated = requires accepting the repo's HF terms with an account; the
runtime reports `ready: false` with that reason until weights land.

| Model | Role | License (model) | Languages (verified) | Status |
|---|---|---|---|---|
| `faster-whisper` + Whisper `base` | ASR | MIT (+ MIT weights) | 15 codes: en hi te ta bn mr gu kn ml pa as ne ur sa sd; brx doi kok ks mai mni or sat refused by adapter | LIVE (CPU int8) |
| `ai4bharat/indic-parler-tts` | TTS primary | Apache-2.0 | 21 official + ks/pa unofficial per card | GATED (401) — honest `tts_unavailable` |
| `espeak-ng` 1.52 data | TTS fallback | GPL-3.0-or-later | 14 verified voices (en hi mr bn pa gu kn ta te ml or as ne ur) | LIVE (explicit fallback) |
| `ai4bharat/indictrans2-*-dist-200M` | MT bridge | MIT checkpoints | 22 scheduled langs via Flores codes | GATED (401) — bridge refuses, direct reasoning default |
| `transformers`/`sentencepiece`/`soundfile` | runtime libs | Apache-2.0/BSD | — | installed |
| `parler_tts` lib + `torchaudio`/`librosa` | — | — | — | REMOVED: pulled CUDA-13 `libcudart` the image lacks, broke torch import; Parler uses transformers-native modeling instead |

No Piper voices enabled (GPL-3.0 software + per-voice model licenses
never verified — correctly left out). No paid API anywhere in the
voice stack. IndicConformer investigated: NeMo-based research
packaging, no maintained pip-installable runtime matching this
stack — faster-whisper (MIT, maintained) is the real FOSS ASR.
