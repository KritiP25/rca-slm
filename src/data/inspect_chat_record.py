import json
from pprint import pprint

FILE = "../../data/processed/train_chat.jsonl"

with open(FILE, "r", encoding="utf-8") as f:
    record = json.loads(next(f))

print("\nType:", type(record))

print("\nKeys:")
print(record.keys())

print("\nMessages:")
pprint(record["messages"])