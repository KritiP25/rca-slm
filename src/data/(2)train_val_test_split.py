"""
train_val_test_split.py
─────────────────────────────────────────────────────────────────────────────
Splits  data/processed/training_dataset.jsonl
  →     data/processed/train_task.jsonl
        data/processed/val_task.jsonl
        data/processed/test_task.jsonl

Split ratio: 80 / 10 / 10

Stratified by task type so both GENERATE RCA and GENERATE CAPA
are proportionally represented in every split.

Usage:
  python src/data/train_val_test_split.py
─────────────────────────────────────────────────────────────────────────────
"""

import json
import random
import os

# ── Config ───────────────────────────────────────────────────────────────────
INPUT_FILE  = "data/processed/(2)training_dataset.jsonl"
TRAIN_FILE  = "data/processed/train_task.jsonl"
VAL_FILE    = "data/processed/val_task.jsonl"
TEST_FILE   = "data/processed/test_task.jsonl"

TRAIN_RATIO = 0.80
VAL_RATIO   = 0.10
# TEST_RATIO  = 0.10  (remainder)

RANDOM_SEED = 42


# ── Helpers ──────────────────────────────────────────────────────────────────

def get_task_type(sample: dict) -> str:
    """Returns 'GENERATE RCA' or 'GENERATE CAPA' based on user content."""
    content = sample["messages"][0]["content"]
    if "TASK: GENERATE RCA" in content:
        return "GENERATE_RCA"
    if "TASK: GENERATE CAPA" in content:
        return "GENERATE_CAPA"
    return "UNKNOWN"


def split_list(items: list, train_r: float, val_r: float):
    """Splits a list into train / val / test by ratio."""
    n       = len(items)
    n_train = int(n * train_r)
    n_val   = int(n * val_r)
    train   = items[:n_train]
    val     = items[n_train : n_train + n_val]
    test    = items[n_train + n_val :]
    return train, val, test


def write_jsonl(path: str, samples: list):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for s in samples:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    random.seed(RANDOM_SEED)

    if not os.path.exists(INPUT_FILE):
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}\n"
            "Run convert_to_task_format.py first."
        )

    # Load all samples
    all_samples = []
    with open(INPUT_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                all_samples.append(json.loads(line))

    print(f"Loaded {len(all_samples)} samples from {INPUT_FILE}")

    # Separate by task type for stratified split
    rca_samples  = [s for s in all_samples if get_task_type(s) == "GENERATE_RCA"]
    capa_samples = [s for s in all_samples if get_task_type(s) == "GENERATE_CAPA"]
    unknown      = [s for s in all_samples if get_task_type(s) == "UNKNOWN"]

    if unknown:
        print(f"  Warning: {len(unknown)} samples with unknown task type — added to train")

    print(f"  GENERATE RCA  samples: {len(rca_samples)}")
    print(f"  GENERATE CAPA samples: {len(capa_samples)}")

    # Shuffle each group independently before splitting
    random.shuffle(rca_samples)
    random.shuffle(capa_samples)

    # Split each group
    rca_train,  rca_val,  rca_test  = split_list(rca_samples,  TRAIN_RATIO, VAL_RATIO)
    capa_train, capa_val, capa_test = split_list(capa_samples, TRAIN_RATIO, VAL_RATIO)

    # Merge splits and shuffle within each split
    train = rca_train + capa_train + unknown
    val   = rca_val   + capa_val
    test  = rca_test  + capa_test

    random.shuffle(train)
    random.shuffle(val)
    random.shuffle(test)

    # Write output files
    write_jsonl(TRAIN_FILE, train)
    write_jsonl(VAL_FILE,   val)
    write_jsonl(TEST_FILE,  test)

    # Summary
    total = len(train) + len(val) + len(test)
    print()
    print("=" * 55)
    print(f"  Train : {len(train):>5} samples  ({len(train)/total*100:.1f}%)")
    print(f"  Val   : {len(val):>5} samples  ({len(val)/total*100:.1f}%)")
    print(f"  Test  : {len(test):>5} samples  ({len(test)/total*100:.1f}%)")
    print(f"  Total : {total:>5} samples")
    print()
    print(f"  {TRAIN_FILE}")
    print(f"  {VAL_FILE}")
    print(f"  {TEST_FILE}")
    print("=" * 55)

    # Verify task balance in train split
    train_rca  = sum(1 for s in train if get_task_type(s) == "GENERATE_RCA")
    train_capa = sum(1 for s in train if get_task_type(s) == "GENERATE_CAPA")
    print(f"\n  Train task balance:")
    print(f"    GENERATE RCA  : {train_rca}")
    print(f"    GENERATE CAPA : {train_capa}")


if __name__ == "__main__":
    main()
