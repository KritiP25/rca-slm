# ==========================================================
# load_model.py
# Loads the Qwen2.5-3B base model with the LoRA adapter.
# Sets the Qwen2.5 chat template explicitly after loading
# because the adapter's saved tokenizer may not have it.
# ==========================================================

from unsloth import FastLanguageModel

_MODEL = None
_TOKENIZER = None

ADAPTER_PATH = "/content/drive/MyDrive/rca_twotask_final_adapter"
MAX_SEQ_LENGTH = 3072

# Qwen2.5-Instruct chat template — set explicitly to ensure
# it is always present regardless of what was saved in the adapter
QWEN_CHAT_TEMPLATE = (
    "{% for message in messages %}"
    "{{'<|im_start|>' + message['role'] + '\n' + message['content'] + '<|im_end|>' + '\n'}}"
    "{% endfor %}"
    "{% if add_generation_prompt %}"
    "{{ '<|im_start|>assistant\n' }}"
    "{% endif %}"
)


def load_model():
    """
    Returns the loaded model and tokenizer.
    On first call: loads model + adapter and sets chat template.
    On subsequent calls: returns cached singleton immediately.
    """
    global _MODEL, _TOKENIZER

    if _MODEL is not None:
        return _MODEL, _TOKENIZER

    print(f"Loading model + LoRA adapter from: {ADAPTER_PATH}")

    _MODEL, _TOKENIZER = FastLanguageModel.from_pretrained(
        model_name=ADAPTER_PATH,
        max_seq_length=MAX_SEQ_LENGTH,
        load_in_4bit=True,
        dtype=None,
    )

    # Set chat template explicitly — the adapter's saved tokenizer
    # may not have preserved this from the original Qwen2.5-Instruct model
    _TOKENIZER.chat_template = QWEN_CHAT_TEMPLATE

    FastLanguageModel.for_inference(_MODEL)

    print("Model loaded successfully and ready for inference.")

    return _MODEL, _TOKENIZER