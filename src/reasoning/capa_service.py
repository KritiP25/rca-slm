from src.reasoning.inference import generate_output
from src.reasoning.prompts import build_capa_prompt


def generate_capa(
    problem_description,
    business_impact,
    technical_investigation,
    approved_rca,
):

    prompt = build_capa_prompt(
        problem_description,
        business_impact,
        technical_investigation,
        approved_rca,
    )

    return generate_output(prompt)