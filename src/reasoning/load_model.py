from unsloth import FastLanguageModel
import torch

# ==========================================================
# Configuration
# ==========================================================

from src.api.config import (
    BASE_MODEL,
    ADAPTER_PATH,
    MAX_SEQ_LENGTH,
)

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