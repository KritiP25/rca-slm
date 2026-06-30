from src.reasoning.inference import generate_output
from src.reasoning.prompts import build_rca_prompt


def generate_rca(
    problem_description,
    business_impact,
    technical_investigation,
):

    prompt = build_rca_prompt(
        problem_description,
        business_impact,
        technical_investigation,
    )

    return generate_output(prompt)