import torch

from src.reasoning.load_model import load_model


def generate_output(user_content, max_new_tokens=2000):

    model, tokenizer = load_model()

    inputs = tokenizer.apply_chat_template(
        [
            {
                "role": "user",
                "content": user_content,
            }
        ],
        tokenize=True,
        add_generation_prompt=True,
        return_tensors="pt",
    ).to("cuda")

    with torch.no_grad():

        outputs = model.generate(
            input_ids=inputs,
            max_new_tokens=max_new_tokens,
            temperature=0.1,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id,
        )

    response = tokenizer.decode(
        outputs[0][inputs.shape[1]:],
        skip_special_tokens=True,
    ).strip()

    return response