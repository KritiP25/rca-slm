import json

FILE = "../../data/processed/training_dataset.jsonl"

with open(FILE, "r", encoding="utf-8") as f:

    sample = json.loads(next(f))

print("\nINPUT\n")
print(sample["input"])

print("\nOUTPUT\n")
print(sample["output"])