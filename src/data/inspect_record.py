import json
from pprint import pprint

DATASET_PATH = "../../data/raw/clean_dataset.jsonl"

with open(DATASET_PATH, "r", encoding="utf-8") as f:
    first_record = json.loads(next(f))

print("\n========== FIRST RECORD ==========\n")

for key, value in first_record.items():

    print("\n" + "="*70)
    print(key)
    print("="*70)

    pprint(value)

    print("\n")