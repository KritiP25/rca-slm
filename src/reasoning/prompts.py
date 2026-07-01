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