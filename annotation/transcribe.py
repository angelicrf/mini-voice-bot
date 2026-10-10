import json
import sys
from pathlib import Path
import whisper

# Ensure root directory is on the module search path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from nlp_rag import process_and_resolve

model = whisper.load_model("base")

result = model.transcribe("../audio/noisy.wav")
transcribed_text = result["text"].strip()

print(f"Transcribed Text: {transcribed_text}\n")
resolution = process_and_resolve(transcribed_text)
print("Categorization & Solution:")
print(json.dumps(resolution, indent=2))