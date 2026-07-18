import whisper

model = whisper.load_model("base")

result = model.transcribe("../audio/noisy.wav")

print(result["text"])