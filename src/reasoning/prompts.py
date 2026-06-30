# ==========================================================
# RCA Prompt
# ==========================================================

def build_rca_prompt(
    problem_description: str,
    business_impact: str,
    technical_investigation: str,
) -> str:

    return f"""
Generate a Root Cause Analysis (RCA).

Problem Description:
{problem_description}

Business Impact:
{business_impact}

Technical Investigation:
{technical_investigation}

Return ONLY valid JSON.
""".strip()


# ==========================================================
# CAPA Prompt
# ==========================================================

def build_capa_prompt(
    problem_description: str,
    business_impact: str,
    technical_investigation: str,
    approved_rca: str,
) -> str:

    return f"""
Generate CAPA based on the approved RCA.

Problem Description:
{problem_description}

Business Impact:
{business_impact}

Technical Investigation:
{technical_investigation}

Approved RCA:
{approved_rca}

Return ONLY valid JSON.
""".strip()


# ==========================================================
# RCA Regeneration Prompt
# ==========================================================

def build_rca_regeneration_prompt(
    original_incident: str,
    previous_rca: str,
    feedback: str,
) -> str:

    return f"""
The previous RCA was reviewed by a human.

Original Incident:
{original_incident}

Previous RCA:
{previous_rca}

Reviewer Feedback:
{feedback}

Regenerate ONLY the RCA.

Return ONLY valid JSON.
""".strip()


# ==========================================================
# CAPA Regeneration Prompt
# ==========================================================

def build_capa_regeneration_prompt(
    approved_rca: str,
    previous_capa: str,
    feedback: str,
) -> str:

    return f"""
The previous CAPA was reviewed by a human.

Approved RCA:
{approved_rca}

Previous CAPA:
{previous_capa}

Reviewer Feedback:
{feedback}

Regenerate ONLY the CAPA.

Return ONLY valid JSON.
""".strip()