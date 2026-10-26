import json
import sys
from pathlib import Path

# Ensure root directory is on the module search path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
from agents import run_voice_workflow

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

final = run_voice_workflow(audio_path)
print("Research & Final Response:")
print(json.dumps(final, indent=2))