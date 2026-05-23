"""Inference device detection (MPS on Apple Silicon, otherwise CPU)."""
from __future__ import annotations


def resolve_device(preference: str = "auto") -> str:
    """
    Return the PyTorch device name.

    - "auto": use MPS (Apple Silicon GPU) if available, otherwise CPU.
    - "cpu" / "mps": force a specific device.

    Note: MPS is NOT available inside Docker on Mac (container sees CPU only),
    so "auto" will correctly fall back to "cpu" in that environment.
    """
    if preference in ("cpu", "mps"):
        return preference

    try:
        import torch

        if torch.backends.mps.is_available():
            return "mps"
        if torch.cuda.is_available():
            return "cuda"
    except Exception:
        # torch not yet loaded or backend unavailable — safe fallback
        pass

    return "cpu"
