"""
inspect_task_dataset.py
─────────────────────────────────────────────────────────────────────────────
Verifies the converted two-task dataset before you push to GitHub.

Checks:
  - File exists and is valid JSONL
  - Task A / Task B counts and balance
  - One printed example of each task type
  - Token length distribution (using char/4 approximation)
  - Flags samples that will be truncated at max_length=3072

Usage:
  python src/data/inspect_task_dataset.py
─────────────────────────────────────────────────────────────────────────────
"""

import json
import os
import statistics

# ── Config ───────────────────────────────────────────────────────────────────
FILES = {
    "train": "data/processed/train_task.jsonl",
    "val":   "data/processed/val_task.jsonl",
    "test":  "data/processed/test_task.jsonl",
}
MAX_LENGTH = 3072   # Must match your SFTConfig max_length


# ── Helpers ──────────────────────────────────────────────────────────────────

def load_jsonl(path):
    samples = []
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                samples.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"  [ERROR] Line {i} in {path}: {e}")
    return samples


def get_task_type(sample):
    content = sample["messages"][0]["content"]
    if "TASK: GENERATE RCA" in content:
        return "GENERATE_RCA"
    if "TASK: GENERATE CAPA" in content:
        return "GENERATE_CAPA"
    return "UNKNOWN"


def approx_tokens(sample):
    """Rough token estimate: total chars / 4."""
    total_chars = sum(len(m["content"]) for m in sample["messages"])
    return total_chars / 4


def analyze_split(name, samples):
    print(f"\n{'='*55}")
    print(f"  SPLIT: {name.upper()}  ({len(samples)} samples)")
    print(f"{'='*55}")

    rca_samples  = [s for s in samples if get_task_type(s) == "GENERATE_RCA"]
    capa_samples = [s for s in samples if get_task_type(s) == "GENERATE_CAPA"]
    unknown      = [s for s in samples if get_task_type(s) == "UNKNOWN"]

    print(f"  GENERATE RCA  : {len(rca_samples)}")
    print(f"  GENERATE CAPA : {len(capa_samples)}")
    if unknown:
        print(f"  UNKNOWN task  : {len(unknown)}  ← investigate these")

    # Token length stats
    token_lengths = [approx_tokens(s) for s in samples]
    over_limit    = sum(1 for t in token_lengths if t > MAX_LENGTH)

    print(f"\n  Token length (approx, chars/4):")
    print(f"    avg : {statistics.mean(token_lengths):.0f}")
    print(f"    p50 : {sorted(token_lengths)[len(token_lengths)//2]:.0f}")
    print(f"    p95 : {sorted(token_lengths)[int(len(token_lengths)*0.95)]:.0f}")
    print(f"    max : {max(token_lengths):.0f}")
    print(f"    > {MAX_LENGTH} (will truncate): {over_limit} ({over_limit/len(samples)*100:.1f}%)")

    if over_limit / len(samples) > 0.10:
        print(f"  ⚠️  Warning: >{over_limit/len(samples)*100:.0f}% samples exceed max_length={MAX_LENGTH}")
        print(f"     Consider increasing max_length or the model will truncate heavily.")


def print_example(samples, task_type, label):
    example = next((s for s in samples if get_task_type(s) == task_type), None)
    if not example:
        print(f"\n  No {label} example found.")
        return
    print(f"\n{'─'*55}")
    print(f"  EXAMPLE: {label}")
    print(f"{'─'*55}")
    user_content = example["messages"][0]["content"]
    asst_content = example["messages"][1]["content"]
    print(f"  USER (first 600 chars):\n{user_content[:600]}")
    print(f"\n  ASSISTANT (first 400 chars):\n{asst_content[:400]}")
    print(f"\n  Approx tokens: {approx_tokens(example):.0f}")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("Two-Task Dataset Inspector")
    print(f"Checking max_length = {MAX_LENGTH} tokens\n")

    all_train = None

    for split_name, path in FILES.items():
        if not os.path.exists(path):
            print(f"  [MISSING] {path} — run the preprocessing scripts first.")
            continue

        samples = load_jsonl(path)
        analyze_split(split_name, samples)

        if split_name == "train":
            all_train = samples

    # Print one example of each task type from train set
    if all_train:
        print_example(all_train, "GENERATE_RCA",  "TASK A — GENERATE RCA")
        print_example(all_train, "GENERATE_CAPA", "TASK B — GENERATE CAPA")

    print(f"\n{'='*55}")
    print("  Inspection complete.")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    main()
