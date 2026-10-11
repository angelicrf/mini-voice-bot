from pydub import AudioSegment

audio = AudioSegment.from_file("../audio/message_facturation_fr.wav")

audio = audio.normalize()

audio.export("../audio/clean.wav", format="wav")

print("Audio normalized")