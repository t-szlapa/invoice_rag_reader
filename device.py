"""Wykrywanie urzadzenia do inferencji (mps na Apple Silicon, inaczej cpu)."""
from __future__ import annotations


def resolve_device(preference: str = "auto") -> str:
    """
    Zwraca nazwe urzadzenia dla PyTorch.

    - "auto": uzyj MPS (Apple Silicon GPU) jesli dostepne, w przeciwnym razie CPU.
    - "cpu" / "mps": wymus konkretne urzadzenie.

    Uwaga: w Dockerze na Macu MPS NIE jest dostepne (kontener widzi tylko CPU),
    wiec "auto" tam poprawnie zejdzie do "cpu".
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
        # torch jeszcze niezaladowany lub brak backendu - bezpieczny fallback
        pass

    return "cpu"
