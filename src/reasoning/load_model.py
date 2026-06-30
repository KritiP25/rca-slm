from unsloth import FastLanguageModel

ADAPTER_PATH = "/content/drive/MyDrive/rca_twotask_final_adapter"

def load_model():

    print("Loading base model...")

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name="unsloth/Qwen2.5-3B-Instruct-bnb-4bit",
        max_seq_length=3072,
        load_in_4bit=True,
    )

    print("=" * 50)
    print("BEFORE ADAPTER")
    print(type(model))
    print(model.config._name_or_path)
    print("=" * 50)

    model.load_adapter(ADAPTER_PATH)

    return model, tokenizer