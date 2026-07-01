# ==========================================================
# load_model.py
# Loads the Qwen2.5-3B base model with the LoRA adapter
# using Unsloth's FastLanguageModel.
#
# Uses a module-level singleton so the model is loaded only
# once per server process. Subsequent calls return the cached
# model and tokenizer immediately without hitting disk or GPU.
#
# IMPORTANT: load_adapter() is NOT used — Unsloth requires
# the adapter path to be passed directly to from_pretrained()
# so it can correctly patch and fuse the LoRA weights.
# ==========================================================

from unsloth import FastLanguageModel

# Module-level singletons — None until first call to load_model()
_MODEL = None
_TOKENIZER = None

# Path to the LoRA adapter saved in Google Drive after training
ADAPTER_PATH = "/content/drive/MyDrive/rca_twotask_final_adapter"

# Must match the max_seq_length used during training
MAX_SEQ_LENGTH = 3072


def load_model():
    """
    Returns the loaded model and tokenizer.

    On first call: loads the base model with LoRA adapter from Drive.
    On subsequent calls: returns the cached singleton immediately.

    Returns:
        tuple: (model, tokenizer)
    """
    global _MODEL, _TOKENIZER

    # Return cached model if already loaded — avoids reloading on every request
    if _MODEL is not None:
        return _MODEL, _TOKENIZER

    print("Loading model + LoRA adapter from Drive...")
    print(f"Adapter path: {ADAPTER_PATH}")

    # Pass the adapter path directly to from_pretrained — this is the correct
    # Unsloth pattern. It loads the base model AND fuses the LoRA weights
    # in a single call. Using load_adapter() separately does not work correctly
    # with Unsloth's patched model architecture.
    _MODEL, _TOKENIZER = FastLanguageModel.from_pretrained(
        model_name=ADAPTER_PATH,
        max_seq_length=MAX_SEQ_LENGTH,
        load_in_4bit=True,
        dtype=None,
    )

    # Switch model to inference mode — disables gradient computation
    # and enables Unsloth's optimised inference kernels
    FastLanguageModel.for_inference(_MODEL)

    print("Model loaded successfully and ready for inference.")

    return _MODEL, _TOKENIZER