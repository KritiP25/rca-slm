import json
from pathlib import Path

INPUT_FILE = "../../data/raw/clean_dataset.jsonl"
OUTPUT_FILE = "../../data/processed/training_dataset.jsonl"

Path("../../data/processed").mkdir(
    parents=True,
    exist_ok=True
)

records = []

with open(INPUT_FILE, "r", encoding="utf-8") as f:

    for line_num, line in enumerate(f, start=1):

        try:

            record = json.loads(line)

            # -----------------------------
            # INPUT
            # -----------------------------

            problem = record.get(
                "1.0_Problem_Summary",
                {}
            )

            input_data = {

                "problem_description":
                    problem.get(
                        "Problem_Description",
                        ""
                    ),

                "business_impact":
                    problem.get(
                        "Business_Impact",
                        []
                    ),

                "technical_investigation":
                    record.get(
                        "2.0_Incident_Review_Technical_Investigation",
                        []
                    )
            }

            # -----------------------------
            # OUTPUT
            # -----------------------------

            capa = []

            for action in record.get(
                "4.0_Corrective_and_Preventive_Actions",
                []
            ):

                capa.append({

                    "Action_Type":
                        action.get(
                            "Action_Type",
                            ""
                        ),

                    "Action_Description":
                        action.get(
                            "Action_Description",
                            ""
                        )

                })

            output_data = {

                "five_why_analysis":
                    record.get(
                        "3.0_5_Why_Analysis",
                        []
                    ),

                "root_cause_summary":
                    record.get(
                        "Root_Cause_Summary",
                        {}
                    ),

                "corrective_preventive_actions":
                    capa,

                "lessons_learned":
                    record.get(
                        "5.0_Lessons_Learned",
                        []
                    )
            }

            records.append(
                {
                    "input": input_data,
                    "output": output_data
                }
            )

        except Exception as e:

            print(
                f"Skipping Record {line_num}: {e}"
            )

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as f:

    for record in records:

        f.write(
            json.dumps(record)
            + "\n"
        )

print(
    f"\nCreated {len(records)} Records"
)

print(
    f"Saved To {OUTPUT_FILE}"
)