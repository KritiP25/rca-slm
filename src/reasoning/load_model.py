from unsloth import FastLanguageModel
import torch

# ==========================================================
# Configuration
# ==========================================================

BASE_MODEL = "unsloth/Qwen3-4B-Instruct-2507"

ADAPTER_PATH = "/content/drive/MyDrive/rca_twotask_final_adapter"

MAX_SEQ_LENGTH = 3072

DTYPE = None

LOAD_IN_4BIT = True


# ==========================================================
# Load Model
# ==========================================================

def load_model():

    print("Loading tokenizer and base model...")

    model, tokenizer = FastLanguageModel.from_pretrained(

        model_name=BASE_MODEL,

        max_seq_length=MAX_SEQ_LENGTH,

        dtype=DTYPE,

        load_in_4bit=LOAD_IN_4BIT,
    )

    print("Loading LoRA adapter...")

    model.load_adapter(ADAPTER_PATH)

    FastLanguageModel.for_inference(model)

    print("Model loaded successfully!")

    return model, tokenizer