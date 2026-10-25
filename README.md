# Mini Voice Bot: NLP & Partitioned RAG System

A voice-to-action pipeline that transcribes audio with OpenAI Whisper and translates foreign spoken language into English text using a multi-agent pipeline, validates input and output safety using `llm-guard`, categorizes user intent across multi-label domains, and retrieves structured troubleshooting solutions from playbook markdown files (`pbs/`) preserving full semantic context.

---

## Architecture Overview

1. **Audio Preprocessing & Augmentation (`annotation/`)**:
   - Cleans background noise and normalizes audio via `clean_audio.py`.
   - Applies audio data augmentation via `augment.py` before inference.
2. **Multi-Agent Speech Pipeline (`agents/`, run via `annotation/transcribe.py`)**:
   Independent agents communicate through a lightweight `MessageBus` (`agents/base.py`); each agent handles one task and sends its result to the next by name. The final result lands in a `sink`.
   - **Agent 1 – `SpeechToTextAgent` (`stt`)**: Uses OpenAI Whisper (`base`) to detect the spoken language and transcribe the audio in its original language (`task="transcribe"`, no translation).
   - **Agent 2 – `TranslationAgent` (`translator`)**: Translates the transcript into English with Helsinki-NLP MarianMT models (`opus-mt-{lang}-en`, downloaded on first use per language). English text passes through unchanged.
   - The English text is then handed to the NLP/RAG stage below. New agents can be added by subclassing `Agent` and registering them on the bus.
3. **Input Guardrails (`llm_guard.scan_prompt`)**:
   - Runs PII anonymization (via `Vault`), toxicity filtering, and prompt injection screening with false-positive filtering for translated conversational speech.
4. **Intent Classification (`nlp_rag.py`)**:
   - Multi-label Zero-Shot Transformer classifier (`transformers.pipeline`) with an intelligent stem-aware keyword fallback.
   - Dispatches across supported categories:
     - `image_file_troubleshooting`
     - `engineering_task_assignment`
     - `technical_support`
     - `billing`
     - `account_access`
     - `general_inquiry`
5. **Context-Preserving Playbook RAG (`pbs/`)**:
   - Loads modular markdown/text playbooks from the `pbs/` directory.
   - Splits by heading and section blocks rather than naive character slicing, preserving sentence continuity.
   - Partitions vector/relevance retrieval to match predicted categories.
6. **Output Guardrails (`llm_guard.scan_output`)**:
   - Scrubs credentials, sensitive tokens, and maps vault tokens back into deanonymized safe text.
7. **FastAPI Service (`api/server.py`)**:
   - Exposes REST endpoints for querying the pipeline directly over HTTP.

---

## Project Structure

```text
mini-voice-bot/
├── annotation/
│   ├── clean_audio.py        # Audio noise cleaning and normalization
│   ├── augment.py            # Audio dataset augmentation
│   └── transcribe.py         # Wires the agents on the bus & triggers the RAG pipeline
├── agents/
│   ├── base.py               # Agent, Message, MessageBus
│   ├── stt_agent.py          # Agent 1: speech-to-text (Whisper)
│   └── translation_agent.py  # Agent 2: text-to-English (MarianMT)
├── api/
│   └── server.py              # FastAPI REST endpoints (/voice, /resolve)
├── pbs/                      # Knowledge base playbooks (auto-seeded if empty)
│   ├── image_file_troubleshooting.md
│   ├── engineering_task_assignment.md
│   ├── technical_support.md
│   ├── billing.md
│   └── account_access.md
├── nlp_rag.py                # Guardrails, classification, RAG retrieval & synthesis
└── README.md
```

---

## Setup & Installation

> **Note**: Whisper requires `ffmpeg` installed on your system PATH to read and decode audio files.

1. **Activate Virtual Environment**:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

2. **Install Core Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

---

## Running the Services

### 1. Preprocess Audio

Before executing transcription, run the preprocessing scripts from the `annotation` directory:

```bash
cd annotation
python clean_audio.py
python augment.py
cd ..
```

Or run them directly from the project root:

```bash
python annotation/clean_audio.py
python annotation/augment.py
```

### 2. Run Audio Transcription & RAG Pipeline

Run the speech-to-text and translation agents, then the end-to-end RAG analysis (the first run downloads a translation model for non-English audio):

```bash
python annotation/transcribe.py
# Or specify a custom audio target (e.g. French billing sample):
python annotation/transcribe.py message_facturation_fr.wav
```

### 2. Start the FastAPI Web Server

Start the server with hot-reload enabled:

```bash
uvicorn api.server:app --reload --host 0.0.0.0 --port 8000
OR
python -m uvicorn api.server:app --reload
```

### 3. API Endpoints

- **GET `/voice?text=<query>`**:
  Pass query text as a URL parameter:
  ```bash
  curl -X GET "http://127.0.0.1:8000/voice?text=Uploaded%20PNG%20images%20are%20failing%20and%20need%20to%20assign%20to%20engineer"
  ```
- **POST `/resolve`**:
  Send JSON payload:
  ```bash
  curl -X POST "http://127.0.0.1:8000/resolve" -H "Content-Type: application/json" -d "{\"text\": \"My audio device has distorted sound.\"}"
  ```
