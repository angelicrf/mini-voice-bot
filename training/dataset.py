from datasets import Dataset

data = {
    "audio": ["sample.wav"],
    "text": ["Hello world"]
}

dataset = Dataset.from_dict(data)

print(dataset)