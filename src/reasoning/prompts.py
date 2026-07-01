# ==========================================================
# prompts.py
# Builds prompts exactly matching the two-task training format.
# The model was fine-tuned with "TASK: GENERATE RCA" and
# "TASK: GENERATE CAPA" prefixes — these MUST be present
# at inference time or the model produces wrong output.
# issue_summary is intentionally excluded — removed from schema.
# ==========================================================


def build_rca_prompt(
    problem_description: str,
    business_impact: str,
    technical_investigation: str,
) -> str:
    """
    Builds the Task A prompt matching the exact training format.
    Expected output: five_why_analysis + root_cause_summary only.
    No issue_summary — it was removed from the schema.
    The five_why_analysis questions must be full descriptive sentences
    drilling progressively deeper — not numbered placeholders.
    """
    return (
        "TASK: GENERATE RCA\n\n"
        f"Problem Description:\n{problem_description}\n\n"
        f"Business Impact:\n{business_impact}\n\n"
        f"Technical Investigation:\n{technical_investigation}\n\n"
        "Return ONLY valid JSON with exactly these two keys:\n"
        "- five_why_analysis: a list of exactly 5 objects, each with 'question' "
        "(a full descriptive why-question drilling progressively deeper into the root cause) "
        "and 'answer' (a detailed explanation of at least 2-3 sentences)\n"
        "- root_cause_summary: an object with 'statement' "
        "(a detailed paragraph explaining the root cause) "
        "and 'root_cause_category' (e.g. Process, Technology, People)"
    )


def build_capa_prompt(
    problem_description: str,
    business_impact: str,
    technical_investigation: str,
    approved_rca: str,
) -> str:
    """
    Builds the Task B prompt matching the exact training format.
    The approved RCA is passed as input so CAPA is conditioned on it.
    Expected output: corrective_preventive_actions + lessons_learned only.
    """
    return (
        "TASK: GENERATE CAPA\n\n"
        f"Problem Description:\n{problem_description}\n\n"
        f"Business Impact:\n{business_impact}\n\n"
        f"Technical Investigation:\n{technical_investigation}\n\n"
        f"Approved Root Cause:\n{approved_rca}\n\n"
        "Return ONLY valid JSON with exactly these two keys:\n"
        "- corrective_preventive_actions: a list of objects each with "
        "'action_type' (CA for corrective or PA for preventive), "
        "'action_description' (a detailed paragraph), "
        "and 'action_owner' (team or person responsible)\n"
        "- lessons_learned: a list of strings, each a detailed lesson"
    )


def build_rca_regeneration_prompt(
    original_incident: str,
    previous_rca: str,
    feedback: str,
) -> str:
    """
    Builds the regeneration prompt for Task A.
    Includes the previous RCA and human feedback so the model
    can correct specific issues rather than starting from scratch.
    """
    return (
        "TASK: GENERATE RCA\n\n"
        f"Original Incident:\n{original_incident}\n\n"
        f"Previous RCA (rejected):\n{previous_rca}\n\n"
        f"Reviewer Feedback:\n{feedback}\n\n"
        "Regenerate the RCA addressing the feedback above.\n"
        "Return ONLY valid JSON with exactly these two keys:\n"
        "- five_why_analysis: a list of exactly 5 objects, each with 'question' "
        "(a full descriptive why-question drilling progressively deeper into the root cause) "
        "and 'answer' (a detailed explanation of at least 2-3 sentences)\n"
        "- root_cause_summary: an object with 'statement' "
        "(a detailed paragraph explaining the root cause) "
        "and 'root_cause_category' (e.g. Process, Technology, People)"
    )


def build_capa_regeneration_prompt(
    original_incident: str,
    approved_rca: str,
    previous_capa: str,
    feedback: str,
) -> str:
    """
    Builds the regeneration prompt for Task B.
    Includes original incident, approved RCA, previous CAPA and feedback.
    The approved RCA must stay unchanged — only CAPA is regenerated.
    """
    return (
        "TASK: GENERATE CAPA\n\n"
        f"Original Incident:\n{original_incident}\n\n"
        f"Approved Root Cause:\n{approved_rca}\n\n"
        f"Previous CAPA (rejected):\n{previous_capa}\n\n"
        f"Reviewer Feedback:\n{feedback}\n\n"
        "Regenerate ONLY the CAPA addressing the feedback above.\n"
        "Return ONLY valid JSON with exactly these two keys:\n"
        "- corrective_preventive_actions: a list of objects each with "
        "'action_type' (CA for corrective or PA for preventive), "
        "'action_description' (a detailed paragraph), "
        "and 'action_owner' (team or person responsible)\n"
        "- lessons_learned: a list of strings, each a detailed lesson"
    )