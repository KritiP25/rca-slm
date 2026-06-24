import json
from collections import Counter

DATASET_PATH = "../../data/raw/clean_dataset.jsonl"

keys_counter = Counter()

with open(DATASET_PATH, "r", encoding="utf-8") as f:
    for i, line in enumerate(f):
        record = json.loads(line)

        for key in record.keys():
            keys_counter[key] += 1

        if i == 0:
            print("\nFIRST RECORD KEYS:\n")
            print(record.keys())

print("\nFIELD FREQUENCIES:\n")

for key, count in keys_counter.items():
    print(f"{key}: {count}")