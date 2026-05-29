"""
Downloads sample invoice images from the katanaml-org/invoices-donut-data-v1 dataset.

Usage:
    uv run setup/download_sample.py

Requires the datasets package:
    uv add datasets

The dataset has 3 splits: train (425), validation (50), test (26).
This script downloads from the test split to ensure honest OCR verification
(the model was trained on the train split only).
"""
from __future__ import annotations

import sys
from pathlib import Path
import argparse

OUTPUT_DIR = Path("samples")
SPLIT = "test"

parser = argparse.ArgumentParser()

parser.add_argument(
    "--samples",
    type=int,
    default=3,
    help="Number of samples to download (max 26 for test split)"
)

def main() -> None:
    args = parser.parse_args()
    samples = args.samples
    try:
        from datasets import load_dataset
    except ImportError:
        print("Package 'datasets' not found. Install it with: uv add datasets")
        sys.exit(1)

    print("Downloading dataset (may take a moment on first run)...")
    ds = load_dataset("katanaml-org/invoices-donut-data-v1", split=SPLIT)

    if samples > len(ds):
        print(f"Requested {samples} samples but split '{SPLIT}' has only {len(ds)}. Capping.")
        samples = len(ds)

    OUTPUT_DIR.mkdir(exist_ok=True)

    for i in range(samples):
        image = ds[i]["image"]
        out_path = OUTPUT_DIR / f"invoice_{i + 1:03d}.jpg"
        image.save(out_path)
        print(f"Saved: {out_path}")

    print(f"\nDone. Files are in '{OUTPUT_DIR}/'.")
    print("Example usage:")
    print(f"  curl -X POST http://127.0.0.1:8000/documents/upload -F 'file=@{OUTPUT_DIR}/invoice_001.jpg'")


if __name__ == "__main__":
    main()
