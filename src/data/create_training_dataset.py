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

            # -------------------------
            # INPUT
            # -------------------------

            problem = record.get(
                "1.0_Problem_Summary",
                {}
            )

            input_data = {

                "incident_description":
                    problem.get(
                        "Problem_Description",
                        ""
                    ),

                "business_impact":
                    problem.get(
                        "Business_Impact",
                        []
                    ),

                "service_tower":
                    problem.get(
                        "Impacted_Service_Tower",
                        ""
                    ),

                "affected_service":
                    problem.get(
                        "Name_of_Impacted_Applications_or_Infrastructure_Services",
                        ""
                    ),

                "category":
                    problem.get(
                        "Impacted_Business_Unit",
                        ""
                    )
            }

            # -------------------------
            # CAPA
            # -------------------------

            capa = record.get(
                "4.0_Corrective_and_Preventive_Actions",
                []
            )

            corrective_actions = []
            preventive_actions = []

            for action in capa:

                if not isinstance(action, dict):
                    continue

                action_type = action.get(
                    "Action_Type",
                    ""
                )

                if action_type == "CA":

                    corrective_actions.append(
                        action
                    )

                elif action_type == "PA":

                    preventive_actions.append(
                        action
                    )

                else:
                    # Skip unexpected CAPA formats
                    continue

            # -------------------------
            # OUTPUT
            # -------------------------

            output_data = {

                "technical_investigation":
                    record.get(
                        "2.0_Incident_Review_Technical_Investigation",
                        []
                    ),

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

                "corrective_actions":
                    corrective_actions,

                "preventive_actions":
                    preventive_actions,

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
                f"Skipping record {line_num}: {e}"
            )

            continue

# -------------------------
# SAVE
# -------------------------

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

print("\nDone!")
print(f"Records Created: {len(records)}")
print(f"Saved To: {OUTPUT_FILE}")