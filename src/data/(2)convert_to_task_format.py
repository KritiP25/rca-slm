"""
convert_to_task_format.py
─────────────────────────────────────────────────────────────────────────────
Converts clean_dataset.jsonl  →  two-task chat format JSONL

Each raw sample produces TWO training examples:

  Task A  —  GENERATE RCA
    Input  : Problem Description + Business Impact + Technical Investigation
    Output : issue_summary + five_why_analysis + root_cause_summary

  Task B  —  GENERATE CAPA
    Input  : Problem Description + Business Impact + Technical Investigation
             + Approved Root Cause  (RCA output used as conditioning input)
    Output : corrective_preventive_actions + lessons_learned

Output format (Qwen chat / messages format):
  {
    "messages": [
      {"role": "user",      "content": "..."},
      {"role": "assistant", "content": "{...json...}"}
    ]
  }

Usage:
  python src/data/convert_to_task_format.py
─────────────────────────────────────────────────────────────────────────────
"""

import json
import random
import os

# ── Paths ────────────────────────────────────────────────────────────────────
INPUT_FILE  = "data/raw/clean_dataset.jsonl"
OUTPUT_FILE = "data/processed/training_dataset.jsonl"   # combined, shuffled
RANDOM_SEED = 42

# ── Helpers ──────────────────────────────────────────────────────────────────

def format_business_impact(bi) -> str:
    """Business Impact can be a list or a plain string."""
    if isinstance(bi, list):
        return "\n".join(f"- {item}" for item in bi)
    return str(bi)


def format_technical_investigation(ti_list: list) -> str:
    """
    Technical Investigation is a list of dicts:
      {"Date": ..., "Time_ET": ..., "Activity": ...}
    Format as a readable timeline.
    """
    lines = []
    for entry in ti_list:
        time    = entry.get("Time_ET", "")
        date    = entry.get("Date", "")
        activity = entry.get("Activity", "")
        lines.append(f"[{date} {time}] {activity}")
    return "\n".join(lines)


def build_user_input_base(sample: dict) -> str:
    """
    Builds the shared user input block used by both Task A and Task B.
    Contains: Problem Description, Business Impact, Technical Investigation.
    """
    ps = sample["1.0_Problem_Summary"]

    problem_description = ps.get("Problem_Description", "")
    business_impact     = format_business_impact(ps.get("Business_Impact", ""))
    tech_investigation  = format_technical_investigation(
        sample.get("2.0_Incident_Review_Technical_Investigation", [])
    )

    return (
        f"Problem Description:\n{problem_description}\n\n"
        f"Business Impact:\n{business_impact}\n\n"
        f"Technical Investigation:\n{tech_investigation}"
    )


def build_rca_output(sample: dict) -> dict:
    """
    Builds the Task A assistant output dict.
    Contains: issue_summary, five_why_analysis, root_cause_summary.

    issue_summary is derived from the Problem Description since the raw
    dataset does not have a separate issue_summary field — this mirrors
    what the model should learn to generate.
    """
    ps       = sample["1.0_Problem_Summary"]
    five_why = sample.get("3.0_5_Why_Analysis", [])
    rcs      = sample.get("Root_Cause_Summary", {})

    # Build a clean five_why list with consistent keys
    five_why_clean = []
    for entry in five_why:
        five_why_clean.append({
            "question": entry.get("Question", ""),
            "answer":   entry.get("Answer", "")
        })

    return {
        "issue_summary": ps.get("Problem_Description", ""),
        "five_why_analysis": five_why_clean,
        "root_cause_summary": {
            "statement":              rcs.get("Statement", ""),
            "root_cause_category":    rcs.get("Root_Cause_Category", ""),
        }
    }


def build_capa_output(sample: dict) -> dict:
    """
    Builds the Task B assistant output dict.
    Contains: corrective_preventive_actions, lessons_learned.
    """
    capa_raw = sample.get("4.0_Corrective_and_Preventive_Actions", [])
    lessons  = sample.get("5.0_Lessons_Learned", [])

    # Clean CAPA — keep only the fields the model should generate
    capa_clean = []
    for entry in capa_raw:
        capa_clean.append({
            "action_type":        entry.get("Action_Type", ""),
            "action_description": entry.get("Action_Description", ""),
            "action_owner":       entry.get("Action_Owner", ""),
        })

    return {
        "corrective_preventive_actions": capa_clean,
        "lessons_learned": lessons if isinstance(lessons, list) else [lessons]
    }


def make_task_a(sample: dict) -> dict:
    """Creates a Task A (GENERATE RCA) training example."""
    user_base  = build_user_input_base(sample)
    rca_output = build_rca_output(sample)

    return {
        "messages": [
            {
                "role": "user",
                "content": f"TASK: GENERATE RCA\n\n{user_base}"
            },
            {
                "role": "assistant",
                "content": json.dumps(rca_output, ensure_ascii=False, indent=2)
            }
        ]
    }


def make_task_b(sample: dict) -> dict:
    """
    Creates a Task B (GENERATE CAPA) training example.
    The approved RCA is embedded in the user input so CAPA is
    conditioned on it — this is the key architectural difference
    from the old single-task approach.
    """
    user_base   = build_user_input_base(sample)
    rca_output  = build_rca_output(sample)
    capa_output = build_capa_output(sample)

    approved_rca_str = json.dumps(rca_output, ensure_ascii=False, indent=2)

    return {
        "messages": [
            {
                "role": "user",
                "content": (
                    f"TASK: GENERATE CAPA\n\n"
                    f"{user_base}\n\n"
                    f"Approved Root Cause:\n{approved_rca_str}"
                )
            },
            {
                "role": "assistant",
                "content": json.dumps(capa_output, ensure_ascii=False, indent=2)
            }
        ]
    }


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    random.seed(RANDOM_SEED)

    # Verify input exists
    if not os.path.exists(INPUT_FILE):
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}\n"
            f"Make sure you run this script from the repo root (rca-slm/)."
        )

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    task_a_samples = []
    task_b_samples = []
    skipped        = 0

    print(f"Reading: {INPUT_FILE}")

    with open(INPUT_FILE, encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                sample = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"  [SKIP] Line {i}: JSON parse error — {e}")
                skipped += 1
                continue

            # Validate required keys
            required = [
                "1.0_Problem_Summary",
                "2.0_Incident_Review_Technical_Investigation",
                "3.0_5_Why_Analysis",
                "Root_Cause_Summary",
                "4.0_Corrective_and_Preventive_Actions",
                "5.0_Lessons_Learned",
            ]
            missing = [k for k in required if k not in sample]
            if missing:
                print(f"  [SKIP] Line {i}: missing keys {missing}")
                skipped += 1
                continue

            task_a_samples.append(make_task_a(sample))
            task_b_samples.append(make_task_b(sample))

    # Combine and shuffle so tasks are interleaved randomly
    all_samples = task_a_samples + task_b_samples
    random.shuffle(all_samples)

    # Write combined output
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for sample in all_samples:
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")

    print()
    print("=" * 55)
    print(f"  Input samples       : {len(task_a_samples) + skipped}")
    print(f"  Skipped             : {skipped}")
    print(f"  Task A samples      : {len(task_a_samples)}")
    print(f"  Task B samples      : {len(task_b_samples)}")
    print(f"  Total output samples: {len(all_samples)}")
    print(f"  Output file         : {OUTPUT_FILE}")
    print("=" * 55)


if __name__ == "__main__":
    main()
