import sys
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Ensure project root is on the module search path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from agents import run_text_workflow

app = FastAPI(title="Voice Bot NLP & RAG API")


class TextPayload(BaseModel):
    text: str


@app.get("/voice")
def voice(text: Optional[str] = None):
    if text:
        return run_text_workflow(text)
    return {"response": "Hello from Voice AI!"}


@app.post("/resolve")
def resolve_text(payload: TextPayload):
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="Text payload cannot be empty.")
    return run_text_workflow(payload.text)