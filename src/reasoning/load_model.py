from unsloth import FastLanguageModel

MODEL = None
TOKENIZER = None


def load_model():

    global MODEL, TOKENIZER

    if MODEL is not None:
        return MODEL, TOKENIZER

    print("Loading tokenizer and base model...")

    MODEL, TOKENIZER = FastLanguageModel.from_pretrained(
        model_name="unsloth/Qwen2.5-3B-Instruct-bnb-4bit",
        max_seq_length=3072,
        load_in_4bit=True,
        dtype=None,
    )

    print("Loading LoRA adapter...")

    MODEL.load_adapter("/content/drive/MyDrive/rca_twotask_final_adapter")

    FastLanguageModel.for_inference(MODEL)

    print("Model loaded successfully!")

    return MODEL, TOKENIZER