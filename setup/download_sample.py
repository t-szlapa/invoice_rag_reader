"""
Pobiera przykladowy obraz faktury z datasetu katanaml-org/invoices-donut-data-v1.

Uzycie:
    uv run setup/download_sample.py

Wymaga pakietu datasets:
    uv add datasets

Dokumenty 0-499 byly uzyte do treningu modelu Donut - skrypt pobiera od indeksu 500
(zbior testowy), zeby zapewnic uczciwa weryfikacje OCR.
"""
from __future__ import annotations

import sys
from pathlib import Path

OUTPUT_DIR = Path("samples")
START_INDEX = 500


def main() -> None:
    try:
        from datasets import load_dataset
    except ImportError:
        print("Brak pakietu 'datasets'. Zainstaluj: uv add datasets")
        sys.exit(1)

    print("Pobieranie datasetu (moze chwile potrwac przy pierwszym uruchomieniu)...")
    ds = load_dataset("katanaml-org/invoices-donut-data-v1", split="test")

    OUTPUT_DIR.mkdir(exist_ok=True)

    for i in range(3):
        idx = START_INDEX + i
        image = ds[i]["image"]
        out_path = OUTPUT_DIR / f"faktura_{idx}.jpg"
        image.save(out_path)
        print(f"Zapisano: {out_path}")

    print(f"\nGotowe. Pliki sa w katalogu '{OUTPUT_DIR}/'.")
    print("Przykladowe uzycie:")
    print(f"  curl -X POST http://127.0.0.1:8000/documents/upload -F 'file=@{OUTPUT_DIR}/faktura_{START_INDEX}.jpg'")


if __name__ == "__main__":
    main()
