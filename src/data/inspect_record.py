import json
from pprint import pprint

FILE = "../../data/raw/clean_dataset.jsonl"

with open(FILE, "r", encoding="utf-8") as f:
    record = json.loads(next(f))

pprint(record, width=200)