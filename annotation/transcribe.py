import json
import sys
from pathlib import Path
import torch
import whisper

# Ensure root directory is on the module search path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
from nlp_rag import process_and_resolve

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

device = "cuda" if torch.cuda.is_available() else "cpu"
model = whisper.load_model("base", device=device)

# 1. Detect language from the first 30 seconds
audio = whisper.load_audio(str(audio_path))
audio_segment = whisper.pad_or_trim(audio)
mel = whisper.log_mel_spectrogram(audio_segment).to(model.device)

_, probs = model.detect_language(mel)
detected_lang = max(probs, key=probs.get)
confidence = float(probs[detected_lang])

# 2. Translate foreign speech into English; otherwise transcribe
task = "transcribe" if detected_lang == "en" else "translate"
result = model.transcribe(str(audio_path), task=task, fp16=(device == "cuda"))
transcribed_text = result["text"].strip()

print(f"Detected Language: {detected_lang} ({confidence:.2%})")
print(f"Task Performed   : {task}")
print(f"Output Text      : {transcribed_text}\n")
resolution = process_and_resolve(transcribed_text)
print("Categorization & Solution:")
print(json.dumps(resolution, indent=2))