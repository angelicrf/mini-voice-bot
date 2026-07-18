from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained(
    "bert-base-uncased"
)

tokens = tokenizer(
    "Hello world"
)

print(tokens)