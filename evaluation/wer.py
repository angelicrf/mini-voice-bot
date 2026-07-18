from jiwer import wer

truth = "hello world"

prediction = "hello word"

print("WER:", wer(truth, prediction))