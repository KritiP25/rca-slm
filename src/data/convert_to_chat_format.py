import json

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
You are an enterprise IT Problem Management expert.

Generate ONLY a valid JSON object.

Input Information

Problem Description:
{inp["problem_description"]}

Business Impact:
{json.dumps(inp["business_impact"], indent=2)}

Technical Investigation:
{json.dumps(inp["technical_investigation"], indent=2)}

Generate a JSON object with EXACTLY the following structure:

{{
  "five_why_analysis": [...],
  "root_cause_summary": {{...}},
  "corrective_preventive_actions": [...],
  "lessons_learned": [...]
}}

Rules:

1. Return ONLY valid JSON.
2. Do NOT generate explanations outside the JSON.
3. Do NOT invent technical details that are not supported by the input.
4. Every statement must be supported by the Problem Description, Business Impact, or Technical Investigation.
5. Keep the reasoning internally consistent.
6. Preserve the JSON structure exactly.
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