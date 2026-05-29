"""Donut model loading and inference."""
from __future__ import annotations

import json
import re
from pathlib import Path

from app.config import settings
from app.services.device import resolve_device

_processor = None
_model = None


def load_model() -> None:
    """Load Donut processor and model once at application startup."""
    global _processor, _model

    import torch
    from transformers import DonutProcessor, VisionEncoderDecoderModel

    device = resolve_device(settings.device)
    print(f"[Donut] Loading model '{settings.donut_model}' on device '{device}'...")

    if settings.hf_token:
        from huggingface_hub import login
        login(token=settings.hf_token, add_to_git_credential=False)

    _processor = DonutProcessor.from_pretrained(settings.donut_model)
    _model = VisionEncoderDecoderModel.from_pretrained(settings.donut_model)
    _model.to(device)
    _model.eval()

    print("[Donut] Model ready.")


def run_inference(image_path: str) -> tuple[str, str]:
    """
    Run Donut OCR on an image file.

    Returns (ocr_text, ocr_json) where ocr_json is a JSON string.
    Raises RuntimeError if the model has not been loaded.
    """
    if _processor is None or _model is None:
        raise RuntimeError("Donut model is not loaded. Call load_model() first.")

    import torch
    from PIL import Image

    device = next(_model.parameters()).device
    image = Image.open(image_path).convert("RGB")
    image = image.resize((960, 1280))  # width x height matching training dimensions

    task_prompt = "<s_cord-v2>"
    decoder_input_ids = _processor.tokenizer(
        task_prompt, add_special_tokens=False, return_tensors="pt"
    ).input_ids.to(device)

    pixel_values = _processor(image, return_tensors="pt").pixel_values.to(device)

    with torch.no_grad():
        outputs = _model.generate(
            pixel_values,
            decoder_input_ids=decoder_input_ids,
            max_length=_model.decoder.config.max_position_embeddings,
            pad_token_id=_processor.tokenizer.pad_token_id,
            eos_token_id=_processor.tokenizer.eos_token_id,
            use_cache=True,
            num_beams=1,
            bad_words_ids=[[_processor.tokenizer.unk_token_id]],
            return_dict_in_generate=True,
        )

    sequence = _processor.batch_decode(outputs.sequences)[0]
    sequence = sequence.replace(_processor.tokenizer.eos_token, "")
    sequence = sequence.replace(_processor.tokenizer.pad_token, "")
    sequence = re.sub(r"<.*?>", "", sequence, count=1).strip()

    parsed = _processor.token2json(sequence)
    ocr_text = sequence
    ocr_json = json.dumps(parsed, ensure_ascii=False)

    return ocr_text, ocr_json
