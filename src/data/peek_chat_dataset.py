import json

FILE = "../../data/processed/train_chat.jsonl"

with open(FILE, "r", encoding="utf-8") as f:

    sample = json.loads(next(f))

print(json.dumps(
    sample,
    indent=2
))