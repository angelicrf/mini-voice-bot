import json
import sys
from pathlib import Path

# Ensure root directory is on the module search path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
from nlp_rag import process_and_resolve
from agents import Message, MessageBus, SpeechToTextAgent, TranslationAgent

# Resolve audio path relative to project root (accepts CLI argument or defaults to message_facturation_fr.wav)
audio_target = sys.argv[1] if len(sys.argv) > 1 else "message_facturation_fr.wav"
audio_path = Path(audio_target) if Path(audio_target).is_file() else BASE_DIR / "audio" / audio_target
if not audio_path.exists():
    # Fallback to local audio/ folder under annotation/ if present
    alt_path = Path(__file__).resolve().parent / "audio" / audio_target
    if alt_path.exists():
        audio_path = alt_path
    else:
        raise FileNotFoundError(
            f"Audio file not found at '{audio_path}'. "
            f"Please ensure '{audio_target}' exists in your audio directory."
        )

bus = MessageBus()
bus.register(SpeechToTextAgent())   # agent 1: speech -> text (original language)
bus.register(TranslationAgent())    # agent 2: text -> English
bus.send(Message("user", "stt", "audio", {"audio_path": str(audio_path)}))

final = bus.results[-1].payload
print(f"Detected Language: {final['language']} ({final['confidence']:.2%})")
print(f"Original Text    : {final['original_text']}")
print(f"English Text     : {final['text']}\n")
resolution = process_and_resolve(final["text"])
print("Categorization & Solution:")
print(json.dumps(resolution, indent=2))