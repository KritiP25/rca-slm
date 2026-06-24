import json
import random
from pathlib import Path

INPUT_FILE = "../../data/processed/training_dataset.jsonl"

TRAIN_FILE = "../../data/processed/train.jsonl"
VAL_FILE = "../../data/processed/val.jsonl"
TEST_FILE = "../../data/processed/test.jsonl"

random.seed(42)

records = []

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    for line in f:
        records.append(json.loads(line))

random.shuffle(records)

total = len(records)

train_end = int(total * 0.80)
val_end = int(total * 0.90)

train_data = records[:train_end]
val_data = records[train_end:val_end]
test_data = records[val_end:]

for file_path, data in [
    (TRAIN_FILE, train_data),
    (VAL_FILE, val_data),
    (TEST_FILE, test_data)
]:

    with open(file_path, "w", encoding="utf-8") as f:

        for record in data:
            f.write(json.dumps(record) + "\n")

print(f"Total Records : {total}")
print(f"Train Records : {len(train_data)}")
print(f"Validation Records : {len(val_data)}")
print(f"Test Records : {len(test_data)}")