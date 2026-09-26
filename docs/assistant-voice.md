# CropPilot Voice Assistant (V1.3)

One assistant, every page. The global header microphone routes any page
into the single assistant voice session; the same conversation, tools,
RAG, citations, and semantic actions as text — plus speech in and out.

## Flow

```
header mic (any page)
  -> /ai-assistant?voice=1  (or in-page start-voice event)
  -> WS /ws/voice  (existing protocol, unchanged wire format)
  -> ASR (faster-whisper, local)
  -> transcript + page context (route/page/filters/language)
  -> LangGraph agent (tools, RAG, deterministic commands)
  -> text answer (+ ui_actions, + citations)
  -> TTS (indic-parler, else espeak-ng, else text-only)
  -> browser playback
```

## Protocol (`/ws/voice`, top-level, not under `/api/v1`)

Client → server: `config{lang, route?, page?, page_filters?}` →
`audio{data, sample_rate}` frames → `commit` (transcribe + answer +
speak) → `stop` (barge-in: cancel in-flight TTS). Server → client:
`ready{asr, tts}` → `final{text}` → `response{text, citations,
ui_actions}` → `audio{data}` frames → `audio_end`. Errors:
`asr_unavailable`, `tts_unavailable`, `no_speech`, `bad_audio`,
`utterance_too_long` (60 s cap), `persistence_disabled`,
`assistant_failed`, `voice_disabled`.

Page context uses the same allow-list as REST `_page_context`
(known routes, scalar filter values ≤128 chars). Citations now ride
the voice `response` frame too.

## Engines (all FOSS, all optional, all lazy)

| Role | Primary | Fallback | Status |
|---|---|---|---|
| ASR | faster-whisper (`ASSISTANT_ASR_MODEL`, default `base`) | none (honest `asr_unavailable`) | LIVE: 15 Whisper-supported codes (en hi te ta bn mr gu kn ml pa as ne ur sa sd); 8 registry codes refused by adapter, never hallucinated |
| TTS | Indic Parler-TTS (`ASSISTANT_TTS_MODEL`) | espeak-ng (`ASSISTANT_TTS_FALLBACK`) | Parler weights GATED (401, HF acceptance required) → `tts_unavailable`; espeak-ng LIVE for 14 codes (en hi mr bn pa gu kn ta te ml or as ne ur) |
| MT | IndicTrans2 dist-200M per direction | direct multilingual reasoning (no bridge) | weights GATED → bridge refuses honestly; direct reasoning is the default path |

- No engine loads at import or on health probes. ASR/TTS/MT models
  load on first real use; `readiness()` reports installed /
  initialized / ready without inference.
- Device `auto` = CUDA when torch sees a GPU, else CPU. This box is
  CPU-only (torch 2.5.1+cu124, `cuda: False`).
- GPU budget: ASR + LLM + TTS are never co-resident by design —
  sequential use, per-call loads, no shared GPU pool.
- `ASSISTANT_PERSIST_AUDIO=false` enforced: no audio files, no audio
  columns, no audio in logs/traces. Verified clean (`/tmp`, `/app`).

## Measured (this CPU-only box)

- faster-whisper `base`, int8: English espeak speech → correct
  transcript ("Show tomato prices in Haldondorf", 1.8 s) → market tools
  → real AGMARKNET answer. Robotic Hindi speech mis-transcribes
  (documented; engine honestly reports low-confidence output rather
  than refusing — callers should mind the VAD/language gate).
- espeak-ng synthesis: 104 KB WAV for one sentence, single call.
- Voice E2E (English): mic-equivalent PCM → WS → ASR → market tools →
  answer + canonical `apply-market-filters`. One live finding fixed:
  unresolvable district args ("Haldondorf") are now stripped from the
  deep-link payload so voice-driven navigation never lands on an
  empty view.
- TTS for unsupported codes raises `tts_unavailable`; the turn still
  returns text (voice input → text response, clearly indicated).

## Setup (optional voice stack)

```sh
# inside the api container (or image build):
pip install faster-whisper huggingface_hub transformers sentencepiece soundfile
apt-get install espeak-ng
# ASR weights download on first transcription (~150 MB for base).
# IndicTrans2 + Parler weights require accepting each repo's HF terms
# with an account, then: huggingface-cli download ai4bharat/indic-parler-tts
```

Core assistant works without any of this. `GET
/api/v1/assistant/capabilities` reports the real matrix; the frontend
voice button degrades to text chat with an honest notice.

## Licenses

- faster-whisper: MIT (Systran). Whisper weights: MIT.
- espeak-ng: GPL-3.0-or-later (binary + data). Acceptable as an
  explicit system fallback; not bundled into source.
- Indic Parler-TTS model: Apache-2.0. `parler_tts` library: Apache-2.0.
- IndicTrans2 checkpoints: MIT. `transformers`/`sentencepiece`:
  Apache-2.0. `soundfile`: BSD.
- Removed during V1.3: `parler_tts` + `torchaudio` + `librosa` pulled
  a CUDA-13 `libcudart` the image lacks and broke `torch` import —
  uninstalled; Parler modeling prefers transformers-native
  (`ParlerTTSForConditionalGeneration`) when weights land.
