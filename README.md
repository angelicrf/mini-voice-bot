# Mini Voice Bot: NLP & Partitioned RAG System

A voice-to-action pipeline that transcribes audio using OpenAI Whisper, validates input and output safety using `llm-guard`, categorizes user intent across multi-label domains, and retrieves structured troubleshooting solutions from playbook markdown files (`pbs/`) preserving full semantic context.

---

## Architecture Overview

1. **Transcription (`annotation/transcribe.py`)**:
   - Uses OpenAI Whisper to convert incoming audio (`.wav`) into raw text.
2. **Input Guardrails (`llm_guard.scan_prompt`)**:
   - Runs PII anonymization (via `Vault`), toxicity filtering, and prompt injection screening prior to downstream routing.
3. **Intent Classification (`nlp_rag.py`)**:
   - Multi-label Zero-Shot Transformer classifier (`transformers.pipeline`) with an intelligent stem-aware keyword fallback.
   - Dispatches across supported categories:
     - `image_file_troubleshooting`
     - `engineering_task_assignment`
     - `technical_support`
     - `billing`
     - `account_access`
     - `general_inquiry`
4. **Context-Preserving Playbook RAG (`pbs/`)**:
   - Loads modular markdown/text playbooks from the `pbs/` directory.
   - Splits by heading and section blocks rather than naive character slicing, preserving sentence continuity.
   - Partitions vector/relevance retrieval to match predicted categories.
5. **Output Guardrails (`llm_guard.scan_output`)**:
   - Scrubs credentials, sensitive tokens, and maps vault tokens back into deanonymized safe text.
6. **FastAPI Service (`api/server.py`)**:
   - Exposes REST endpoints for querying the pipeline directly over HTTP.

---

## Project Structure

```text
mini-voice-bot/
├── annotation/
│   └── transcribe.py         # Whisper transcription runner & pipeline trigger
├── api/
│   └── server.py             # FastAPI REST endpoints (/voice, /resolve)
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

### 1. Test Audio Transcription & RAG Pipeline

Transcribe audio and run the end-to-end RAG analysis directly:

```bash
python annotation/transcribe.py
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
