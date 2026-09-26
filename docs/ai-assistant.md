# CropPilot AI Assistant

Single bounded LangGraph agent. Local-first LLM (Ollama Qwen3-8B), optional
free-tier cloud fallback (Gemini → OpenRouter → Groq → Ollama). Text chat via
SSE, voice via WebSocket, memory in Postgres, metrics in Prometheus.

Legacy `/api/v1/intel/*` routes still exist but are superseded by
`/api/v1/assistant/*`. Nothing under `agents/` (OpenAI stubs) is used by the
assistant; do not extend it.

## Architecture

```
frontend/app/ai-assistant/page ──SSE──▶ POST /api/v1/assistant/chat[/stream]
frontend/components/ai/voice-input ──WS──▶ /ws/voice?lang=&token=
        │                                        │
        ▼                                        ▼
AssistantService.chat/stream ──▶ LangGraph assistant_graph ──▶ LLM router
  history (postgres)               prepare → agent ⇄ tools → finalize
  ui_actions validated               │        │
  citations attached                 │        ▼ ToolRegistry (16 tools)
                                     ▼ provider order + cooldown
                               market_* / weather_* / schemes_* /
                               disease_log_summary / crop_profit
```

Key files (`backend/`):

| Area | File |
|---|---|
| Agent graph | `services/assistant/agent.py` (`assistant_graph`) |
| Providers + router | `services/assistant/providers.py`, `router.py` |
| Tool registry + defs | `services/assistant/tools_registry.py`, `tools_definitions.py`, `tools_{market,weather,schemes,disease}.py` |
| RAG retrieval | `services/assistant/retrieval.py` (vector → relational fallback → rerank) |
| UI actions | `services/assistant/ui_actions.py` (allow-list, validated) |
| Service facade | `services/assistant/service.py` |
| Memory | `services/assistant/memory.py`, `models/assistant.py`, migration `0008` |
| Voice | `services/assistant/voice.py`, `api/v1/endpoints/voice.py` (WS `/ws/voice`) |
| Metrics | `telemetry/assistant_metrics.py` |
| REST | `api/v1/endpoints/assistant.py`, `schemas/assistant.py` |
| Prompts | `services/assistant/prompts.py` (`SYSTEM_PROMPT` v1) |
| Eval set | `tests/eval/golden.json`, `tests/test_assistant.py` (33 tests) |

## Provider setup

No key = provider skipped silently. At least one provider must be up or the
assistant reports unavailable (never a raw traceback).

| Provider | Setup |
|---|---|
| Ollama (default local) | `docker compose up ollama`; `ollama pull qwen3:8b`. Compose already sets `OLLAMA_BASE_URL=http://ollama:11434`. |
| Gemini free tier | `GEMINI_API_KEY=…` (AI Studio). Default model `gemini-2.0-flash`. |
| OpenRouter free tier | `OPENROUTER_API_KEY=…`. Default model `qwen/qwen3-8b:free`. |
| Groq free tier | `GROQ_API_KEY=…`. Default model `llama-3.3-70b-versatile`. |

Order: `ASSISTANT_PROVIDER_ORDER` (default `gemini,openrouter,groq,ollama`).
Router skips providers lacking capability, cools down failures for
`ASSISTANT_COOLDOWN_SECONDS` (default 300s). `ASSISTANT_LLM_MODE=local_first`
prefers Ollama when healthy. `GET /api/v1/assistant/health` shows live status.

## Tools matrix

| Tool | Source | Auth |
|---|---|---|
| `market_latest/history/compare/overview` | `MarketService`, Telangana default | none (public mandi data) |
| `weather_current/forecast` | `WeatherService` + H3 | none |
| `schemes_list` | `SchemeService` | none |
| `scheme_search` | pgvector `government_schemes` → relational fallback | none |
| `disease_log_summary` | `DiseaseService.get_disease_log` | user-owned log only |
| `crop_profit` | pure arithmetic | none |

Adding a tool: write `async def` in `tools_<domain>.py`, add a Pydantic input
model (`extra="forbid"`), register a `ToolDefinition` with capability string
and audit event in `tools_definitions.py`. Unknown tools and schema violations
are rejected by `ToolRegistry.execute` before any handler runs.

## RAG and re-ingestion

Collection `government_schemes` (pgvector, BGE-M3 1024-d). Retrieval
(`retrieval.py`): vector search → relational fallback on vector failure →
deterministic rerank (keyword overlap, then vector score). Every match carries
a `Citation{source,title,snippet,score}` shown in the UI sources panel.

Re-ingest after scheme data changes:

```python
from rag.pipeline import rag_pipeline
await rag_pipeline.initialize()
await rag_pipeline.ingest_scheme({...})   # single
# or: python scripts/ingest_schemes.py      # bulk, when present
```

`ASSISTANT_RAG_TOP_K` (12) / `ASSISTANT_RAG_RERANK_K` (5) tune recall/latency.

## Voice stack

Default both engines `disabled`: text answers flow, audio reports unavailable.
WS protocol (`/ws/voice`): client `config → audio* → commit → response (+audio
frames)`, `stop` = barge-in cancel, server `ready/final/response/audio/
audio_end/interim/error`. 60s buffer cap, 3 KB frames.

- ASR: `ASSISTANT_ASR_ENGINE=faster-whisper` (+ `faster-whisper` package and
  model download) for local Indic transcription. Gaps: `indic-conformer`
  engine name is accepted as config but has no adapter yet — requests fail
  closed with `asr_unavailable`, they never fall back silently.
- TTS: `ASSISTANT_TTS_ENGINE=indic-f5` needs the F5 model weights; same
  fail-closed behavior until wired.
- `ASSISTANT_PERSIST_AUDIO=false` default: audio is never written to disk;
  requesting persistence returns a `persistence_disabled` error, never a
  silent write.

## Evaluation

`tests/eval/golden.json`: 20 questions with expected tool + expected UI action.
Smoke-test: `pytest tests/test_assistant.py` (34 tests, ~80% of
`services/assistant`). Live-stack validated 2026-09-24: 16 tools, real DB
prices via SSE + POST, RAG citations, memory roundtrip, WS voice fail-closed.
Commodity names must match AGMARKNET exactly (`Paddy(Common)`, not `Paddy`) —
exact ILIKE returns zero rows otherwise. `bcrypt<4.1` is pinned: passlib 1.7.4
breaks on bcrypt 5 (register 500).

## Cost and performance

Local-first = ₹0 marginal cost. Cloud fallback only on local outage, and only
for providers with keys configured. Budgets enforced in code: max 5 tool steps
(10 hard), 60s provider timeout, 4000-char input cap, history truncated to
last 6 turns. Monitor `assistant_chat_total{provider,status}`,
`assistant_tool_calls{tool,status}`, `assistant_rag_fallback{reason}`,
`assistant_voice_latency_seconds` in Prometheus/Grafana. Measured on CPU-only
box (llama3.1:8b + bge-m3 resident): ~50s per tool-answer turn; cold model
load can exceed the 60s timeout (honest timeout + 300s cooldown follow).
Production local model is llama3.1:8b (qwen3:8b hallucinated tool calls in
testing); tool use is enforced via required tool_choice on factual intents.

## Cost and performance

Local-first = ₹0 marginal cost. Cloud fallback only on local outage, and only
for providers with keys configured. Budgets enforced in code: max 5 tool steps
(10 hard), 60s provider timeout, 4000-char input cap, history truncated to
last 6 turns. Monitor `assistant_chat_total{provider,status}`,
`assistant_tool_calls{tool,status}`, `assistant_rag_fallback{reason}`,
`assistant_voice_latency_seconds` in Prometheus/Grafana.

## Privacy

Chat turns persist in Postgres (`assistant_conversations/messages`) so
conversations survive reload; feedback ratings persist as memory kv. Audio is
ephemeral by default (see voice). No PII leaves the box on local providers;
cloud fallback sends the prompt (with history) to the configured provider —
operators enabling keys accept that provider's terms.

## V1.1 validation (2026-09-24, live stack)

- RAG dedup: 116 embedding rows → 5 canonical (class D, same-chunk dupes from
  restart re-ingest). Fix: deterministic uuid5 row ids + content_sha skip +
  partial UNIQUE (collection_id, chunk_key, embedding_model). Re-ingest
  idempotent; PMFBY retrieval top with citations. Tests:
  `test_rag_idempotency.py` 7/7.
- Cold/warm: cold turn 73s, warm 53–59s on CPU-only box. Bottleneck is CPU
  inference with 16 tool specs, not wiring. `ASSISTANT_REQUEST_TIMEOUT=120`
  (gitignored .env), `OLLAMA_KEEP_ALIVE=30m`. `/assistant/health` reports
  `model_ready`/`model_probe_ms` with 60s TTL cache. Tests:
  `test_provider_startup_readiness.py` 6/6.
- Provider fallback: Ollama down → honest unavailable text + `provider: none`;
  no cloud keys configured, so cloud legs untested live (abstraction verified
  by unit tests only).
- Golden eval: static 20/20, live 7/7
  (`backend/evaluation/results/assistant-v1.1.json`). Injection doc retrieved
  as data only; no sql/exec/shell tool exists. Commodity naming caveat: use
  `Paddy(Common)`, exact ILIKE `Paddy` matches 0 rows.
- Playwright: BLOCKED — browsers install but workers die instantly
  (remote-debugging-pipe spawn fails on this win32 box, 3 attempts). E2E
  verified at API level instead (chat/SSE/memory/RAG/WS/tools/metrics).
- Voice: ASR/TTS remain Disabled (fail-closed, faster-whisper not installed
  by design). WS handshake → ready(disabled) → commit → honest
  `asr_unavailable` verified. Persist-audio request correctly rejected;
  filesystem clean. Actual voice language support: none (text-only).
- Full suite: 47/47 pass (assistant 34 + rag 7 + readiness 6).

## V1.2 validation (2026-09-24, live stack)

- Latency: per-family tool-spec filtering on step 0 (16→2-10 specs) +
  smalltalk fast path (zero tools). Warm factual 45.2s vs 53–59s baseline
  (~15-20%). Greeting fast path 3.8s warm. Overlap-retry node re-fires forced
  tool_choice once when step 0 returns no calls. `OLLAMA_KEEP_ALIVE` is now a
  real Setting (was an inert .env key); OllamaProvider sends `keep_alive`.
  Tests: +7 Phase B (`test_assistant.py` family/fast-path/retry/keep-alive).
- Playwright: UNBLOCKED — V1.1 "spawn failure" was a version mismatch
  (1.63.0 wants headless-shell-1243; installed via `npx playwright install
  chromium`). Real E2E `frontend/e2e/assistant-v1-2.spec.ts`: 10/10 pass live
  (~7 min, CPU-bound turns). Three real bugs found by the suite and fixed:
  (1) `markdown-renderer.tsx` never passed `content` children to
  `<ReactMarkdown/>` — all assistant bubbles rendered empty; prior text
  assertions matched user echoes vacuously. Now asserts scope to last group
  and require tool-data markers. (2) `ui_actions` was never emitted —
  `execute_tools` now deterministically stashes `apply-market-filters`
  (from executed market-tool args) on success; TEST5 navigates to
  `/markets?state=&commodity=` and asserts filter state. (3) Thread history
  lived only in memory — added localStorage persistence so reload (TEST10)
  genuinely passes. Outage test asserts the real error string.
- Voice: ASR/TTS still Disabled fail-closed (faster-whisper not installed by
  design; no Indic adapters vendored; 8GB VRAM). No audio files on disk
  (`/tmp`, `/app` clean); `ASSISTANT_PERSIST_AUDIO=false` enforced.
- Golden eval: static 20/20 + live 7/7 re-run post-V1.2, fresh timestamp
  (`backend/evaluation/results/assistant-v1.2.json`, copy of the live run).
  Security grep clean: no eval/exec/subprocess/shell/pickle in assistant
  backend.
- Full suite: 56/56 host pass; 10/10 Playwright live; typecheck clean except
  pre-existing litert-worker gpu error (fixed this phase, see below).

## Local performance + hardening (2026-09-25/26)

- Tailwind crash fixed: `tailwind.config.ts` is ESM but called `require()`
  at line 91 → `ReferenceError: require is not defined` broke route
  compilation. Fix: ESM `import animate/typography`. Dev server stable
  across all routes since.
- `npm run build` now passes (was blocked by pre-existing
  `navigator.gpu` type error in `workers/litert-worker.ts`; fixed with a
  feature-detect cast, no behavior change). Bundle: shared 103 kB;
  heaviest first-loads are dashboard 314 kB and ai-assistant 234 kB
  (recharts/markdown); /markets 217 kB with recharts split into a
  deferred chunk (`next/dynamic`, ssr:false) so filters + table paint first.
- Dev measurements (post-compile): `/` 170 ms, `/markets` 181 ms,
  `/ai-assistant` 484 ms, `/dashboard` 653 ms. Prod `next start`: 5–50 ms
  HTML shell on all routes (route content hydrates client-side).
- Docker decision: dev stays Option A (`docker compose up -d` backend +
  host `npm run dev`, ready ~2 s, hot reload). No frontend Dockerfile:
  measured dev/prod both healthy; containerizing adds build complexity
  without solving any observed problem. Prod path is `npm run build` +
  `npm run start`.
- Disease routing widened: blast/blight/mildew/wilt/rot/fung/virus/insect/
  treatment/symptom/spray/pesticide now hit the disease family
  (`paddy blast treatment` → 1 spec, was 16). Unknown queries still fall
  back to all families (safe, never zero tools).
- Assistant page aborts in-flight SSE on unmount; voice input already tore
  down mic tracks + WS on unmount. No leaks added.
- Backend/DB unchanged in behavior: httpx singleton + pooled engine
  retained; hottest market query is an index-only scan (69 ms / 525k rows).
  Ollama on this box is 100% CPU, keep-alive 30 m live, timeout 120 s live.
- Playwright this phase: 4 fast tests + TEST-3 Hello pass live. One TEST-3
  timeout root-caused to Docker Desktop daemon being down (backend
  unreachable), not the app; full 12-test suite last green in V1.2.
- Backend suites this phase: 80/80 (assistant + tiers 24 + rag + readiness).

## Live OpenRouter integration (2026-09-26, real key, minimal quota)

- Found live: `OPENROUTER_API_KEY` set in container, but no model
  configured → OpenRouter silently inert (baseline capabilities: only
  Ollama). Two real bugs fixed to make tiers work:
  1. Tiering never ran without the legacy `OPENROUTER_MODEL`: the router
     order derives from registered providers, and nothing registered the
     `openrouter` leg in tier-only mode. Fix: register the leg from Tier
     1 (union capabilities across tiers) when key + tiers exist.
  2. The example default `qwen/qwen3-8b:free` is delisted (live 404 →
     tier correctly disabled itself). Verified against the live catalog
     (17 `:free` entries, 2026-09-26) and tested T1
     `qwen/qwen3.8-27b:free` / T2 `google/gemma-4-26b-a4b-it:free` / T3
     `liquid/lfm-2.5-2.6b:free` (all tools-capable, zero-priced).
- Live behavior: T1+T2 returned 429 `upstream_provider_shared_pool`
  (shared free-pool capacity, NOT our quota) → automatic shift T1→T2→T3
  → T3 answered. Quota spent: ~72k free-tier tokens over ~20 T3
  requests; failures reconcile to 0 tokens.
- Measured (T3): hello 3.8s; paddy market turn 4.6s (real table:
  Choppadandi 2282 / Alampur 2300 / Jangaon 2229.63 / Dammapet 2500 /
  Kagaznagar 2484.2, 2026-09-21); tomato history turn 4.3s with canonical
  UI action; PMFBY RAG 10–12s with 5 real citations. Ollama warm baseline
  for the same turns is ~45–59s.
- State resolution added after a live miss: the (fallback) model put
  district "Nalgonda" in `state` → tools now resolve state canonically
  and reinterpret a district-valued state ("Nalgonda" → Telangana +
  district). Scheme search gained a marked `national-fallback` scope when
  the requested state has no KB coverage, plus state resolution and
  "leave state empty" tool guidance.
- Env reverted after the test (tiering off, Ollama primary). To repeat:
  set the three TIER_N_MODEL ids above + `TIERING_ENABLED=true`, restart
  api. Known note: capabilities health pings cost one tiny inference per
  call — a `/models/.../endpoints` check would be cheaper (follow-up).

## V1.3 multilingual + voice foundation (2026-09-26)

- 23-locale canonical registry (`services/assistant/languages.py`);
  capabilities exposes the full matrix + honest voice status
  (ASR/TTS false — faster-whisper not installed, fail-closed).
- Same-route i18n (no next-intl, no `/te/...` prefixes): persisted
  locale store, en/te/hi catalogs, `t()` with English fallback,
  `check-i18n.mjs` parity validation, header+sidebar switcher,
  header/sidebar/assistant shell localized, canonical values never
  translated for backend use. Playwright `e2e/i18n.spec.ts` 2/2.
- Deterministic `assistant.set_language` / `navigation.open_page`
  commands fire even with all LLM providers down (verified live with
  cold Ollama); backend + frontend double validation.
- Page-aware context (`route/page/page_filters`, allow-listed) flows
  into every chat turn (assistant page sends route + UI language;
  voice frames carry route/page/filters); global header mic routes any
  page into the single assistant voice session (`?voice=1` /
  start-voice event).
- Full i18n migration (2026-09-26 completion): every route localized
  (landing, dashboard + 12 widgets, markets + 5 components, weather +
  5 components, disease + 6 components, schemes + 3, analytics + 8,
  maps + 4, assistant full chrome, auth, palette, error/loading/404,
  theme toggle). RTL via logical properties in shell + chat + tables.
  Playwright `e2e/i18n.spec.ts` 2/2; `check-i18n.mjs` parity green.
- Real voice (2026-09-26): faster-whisper ASR live (15 codes),
  espeak-ng TTS fallback live (14 codes), indic-parler + IndicTrans2
  weights gated (honest unavailable). English voice E2E verified live
  (speech → tools → real data → canonical action). Details:
  `docs/assistant-voice.md`, `docs/i18n.md`.
- Full docs: `docs/i18n.md`. Remaining honest gaps: 19 locale catalogs
  (en/te/hi shipped; generator + bridge ready, weights gated),
  indic-parler + IndicTrans2 weights (need HF-terms acceptance),
  robotic-espeak quality for TTS until Parler lands.

## Live bug investigation fixes (2026-09-25/26)

BUG 1 — market query failed in live UI ("Show me the latest paddy price
in Telangana" → "couldn't find ... using AGMARKNET API").
- Actual root cause: entity resolution mismatch. The model passes natural
  language (`commodity="paddy"`) but the DB holds canonical AGMARKNET
  spellings (`Paddy(Common)`, 491 Telangana rows, latest 2026-09-21) and
  repository filters are exact case-insensitive matches — so the tool
  succeeded with 0 rows and the model reported a failure. Same class of
  gap for markets: no market is named exactly "Nalgonda" (Miryalguda,
  Nakrekal, Venkateswarnagar), so `market="Nalgonda"` would also miss.
- Fix (assistant tool layer only, `tools_market.py`; repository and
  /markets semantics untouched): resolve requested district/market/
  commodity against real metadata before querying (exact → base-name
  before "(" → substring). Unresolvable filters are dropped and disclosed
  (`dropped_filters`) instead of forcing empty; multiple canonical
  commodities merge as labeled rows, never averages; history pins the most
  current lineage and discloses `other_lineages`; a market string matching
  a district exactly ("Nalgonda") is treated as district. Results carry
  `resolved_commodity` (+`resolved_scope`), and the UI deep-link prefers
  the resolved canonical so /markets lands on the same data.
- Prompt (v2): a zero-row tool result is an empty result, never an API
  failure — say "no matching latest reported price was found".
- Live result: "The latest paddy price in Telangana is ₹2282 per quintal
  at Choppadandi APMC, Karimnagar district" — the exact DB row
  (Choppadandi 2282.0, 2026-09-21); /markets API agrees (same date,
  Kagaznagar 2484.2 / Dammapet 2500 / Jangaon 2229.63). UI action now
  carries `Paddy(Common)`.

BUG 2 — general knowledge misrouted ("Best practices for wheat
cultivation" → "couldn't find any relevant schemes...").
- Actual root cause: no intent separation. The query matched no tool
  family, fell back to all 16 tools, and the model voluntarily called
  `schemes_list` for a non-scheme question.
- Fix (`agent.py`): `classify_intent` (GENERAL_AGRICULTURAL_KNOWLEDGE |
  GOVERNMENT_SCHEME | MARKET | WEATHER | DISEASE | PROFIT | UI_NAVIGATION
  | OTHER); scheme tools require explicit scheme intent (names included:
  PMFBY, PM-KISAN, KALIA, Rythu Bandhu, MGNREGA...); unmatched queries get
  all families except schemes; general knowledge offers zero tools and
  skips the overlap retry (nothing to force), so the model answers
  directly from general knowledge as the prompt already allows.
- Also fixed while here: `execute_tools` never propagated RAG citations
  into the turn result (structured citations were always empty) — tool
  `citations` now accumulate deduped (cap 12); and scheme tool
  descriptions steer named-scheme questions to `scheme_search`.
- Live results: wheat cultivation → zero tools, plain-text best-practices
  answer; "What government schemes are available?" → `schemes_list`;
  "Explain PMFBY" → `scheme_search` with 5 real citations (PMFBY top).
- Tests: STEP-11 intent cases, `_resolve_names` units, resolved-override
  UI-action tests, citations accumulation test (49 assistant tests pass).

## OpenRouter free-tier rotation (tier manager)

Deterministic Tier 1 → Tier 2 → Tier 3 → Ollama. Two mechanisms:
**budget shifting** (exhausted local budget skips the tier before any
request) and **failure failover** (429/timeout/5xx → next tier; 404-model
disables the tier; auth aborts the OpenRouter leg; invalid request never
retries elsewhere). Full behavior contract: `docs/assistant-models.md`.

- Config: `ASSISTANT_OPENROUTER_TIERING_ENABLED` + `ASSISTANT_OPENROUTER_TIER_{1,2,3}_{MODEL,MAX_REQUESTS,MAX_TOKENS,TOOL_CALLING,MAX_CONTEXT}`
  (`.env.example`). Empty model disables the tier; non-`:free` models are
  rejected at load — paid routing is never silent. Disabled by default:
  local-only mode (`ASSISTANT_PROVIDER_ORDER=ollama`, no keys) is unaffected.
- Budgets are LOCAL caps, not provider quotas. Per-day UTC bucket in
  `assistant_provider_usage` (migration `0009`, unique
  `(usage_date, provider, model)`); counters only, no prompts/secrets.
- Reservation: one atomic `UPDATE ... WHERE` (request + token reserve,
  default 2000 completion tokens) — concurrent racers cannot overbook;
  contention fails closed to the next tier. Actual provider `usage`
  reconciles afterwards (chat JSON + terminal stream chunk); failures
  release the reservation without counting tokens.
- Capability gate per tier: tool turns skip non-tool tiers; vision and
  structured-output tiers don't exist yet (any such requirement skips all
  OpenRouter tiers to Ollama/cloud). Family tool filtering is unchanged.
- Observability: `provider.tier_shift{from,to,reason}` logs +
  `..._tier_shifts_total`, `..._provider_requests_total{provider,tier,status}`,
  `..._provider_tokens_total{provider,tier,kind}` (bounded labels, never raw
  model ids), latency histogram. Capabilities exposes safe tier config;
  `GET /assistant/providers/usage` (admin only) shows used vs configured.
- Live-validated 2026-09-25 with a fake key: Tier 1 401 → reservation
  released (1 request, 0 tokens in DB) → Ollama answered. No quota spent.
  Tests: `tests/test_openrouter_tiers.py` 24/24 (incl 8-way concurrent
  reservation — accepted ≤ budget, never negative).
