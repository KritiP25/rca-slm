import json
from pathlib import Path

INPUT_FILES = [
    "../../data/processed/train.jsonl",
    "../../data/processed/val.jsonl",
    "../../data/processed/test.jsonl"
]

OUTPUT_FILES = [
    "../../data/processed/train_chat.jsonl",
    "../../data/processed/val_chat.jsonl",
    "../../data/processed/test_chat.jsonl"
]


def build_user_prompt(record):

    inp = record["input"]

    return f"""
Generate a ServiceNow-style RCA.

Problem Description:
{inp['problem_description']}

Business Impact:
{json.dumps(inp['business_impact'], indent=2)}

Technical Investigation:
{json.dumps(inp['technical_investigation'], indent=2)}

Generate:
1. 5 Why Analysis
2. Root Cause Summary
3. Corrective & Preventive Actions
4. Lessons Learned

Do not add unsupported technical assumptions.
"""


def build_assistant_response(record):

    return json.dumps(
        record["output"],
        ensure_ascii=False,
        indent=2
    )


for input_file, output_file in zip(
    INPUT_FILES,
    OUTPUT_FILES
):

    count = 0

    with open(
        input_file,
        "r",
        encoding="utf-8"
    ) as fin, open(
        output_file,
        "w",
        encoding="utf-8"
    ) as fout:

        for line in fin:

            record = json.loads(line)

            chat_record = {

                "messages": [

                    {
                        "role": "user",
                        "content":
                            build_user_prompt(
                                record
                            )
                    },

                    {
                        "role": "assistant",
                        "content":
                            build_assistant_response(
                                record
                            )
                    }

                ]
            }

            fout.write(
                json.dumps(
                    chat_record,
                    ensure_ascii=False
                )
                + "\n"
            )

            count += 1

    print(
        f"Converted {count} records -> {output_file}"
    )

print("\nDone.")