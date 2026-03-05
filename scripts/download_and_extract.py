"""
Download webui-7kbal zip files and extract ONLY metadata (skip screenshots).

Per-sample files:
  KEEP: *-axtree.json.gz, *-bb.json.gz, *-box.json.gz, *-class.json.gz,
        *-style.json.gz, *-html.html, *-links.json, *-url.txt
  SKIP: *-screenshot*.webp (these are the bulk of the size)
"""
import os
import sys
import zipfile
import tempfile
from pathlib import Path
from huggingface_hub import hf_hub_download

# Set HF_TOKEN as an environment variable before running:
#   export HF_TOKEN=your_token_here  (Linux/Mac)
#   $env:HF_TOKEN = "your_token_here"  (PowerShell)

EXTRACT_DIR = Path(__file__).parent.parent / "data" / "webui-7kbal"
EXTRACT_DIR.mkdir(parents=True, exist_ok=True)

SKIP_EXTENSIONS = {".webp", ".png", ".jpg", ".jpeg"}


def should_extract(filename: str) -> bool:
    """Only extract metadata files, skip screenshots."""
    ext = Path(filename).suffix.lower()
    return ext not in SKIP_EXTENSIONS


def download_and_extract():
    print("Step 1: Downloading zip parts from HuggingFace...")
    print("  (This is ~5.3GB total, will take a few minutes)")

    part1 = hf_hub_download("biglab/webui-7kbal", "balanced_7k.zip.001", repo_type="dataset")
    print(f"  Part 1: {part1}")

    part2 = hf_hub_download("biglab/webui-7kbal", "balanced_7k.zip.002", repo_type="dataset")
    print(f"  Part 2: {part2}")

    # Combine split zip into one temp file
    print("\nStep 2: Combining split zip files...")
    combined_path = os.path.join(tempfile.gettempdir(), "webui-7kbal-combined.zip")
    with open(combined_path, "wb") as outf:
        for part_path in [part1, part2]:
            print(f"  Appending {Path(part_path).name}...")
            with open(part_path, "rb") as inf:
                while True:
                    chunk = inf.read(1024 * 1024 * 64)  # 64MB chunks
                    if not chunk:
                        break
                    outf.write(chunk)
    print(f"  Combined size: {os.path.getsize(combined_path) / 1024 / 1024 / 1024:.2f} GB")

    # Extract only metadata files
    print(f"\nStep 3: Extracting metadata to {EXTRACT_DIR}...")
    extracted = 0
    skipped = 0
    with zipfile.ZipFile(combined_path, "r") as zf:
        members = zf.namelist()
        total = len(members)
        print(f"  Total files in zip: {total}")

        for i, member in enumerate(members):
            if should_extract(member):
                zf.extract(member, EXTRACT_DIR)
                extracted += 1
            else:
                skipped += 1

            if (i + 1) % 5000 == 0:
                print(f"  Progress: {i+1}/{total} (extracted: {extracted}, skipped screenshots: {skipped})")

    print(f"\nDone! Extracted {extracted} metadata files, skipped {skipped} screenshots.")
    print(f"Data directory: {EXTRACT_DIR}")

    # Clean up combined zip
    os.remove(combined_path)
    print("Cleaned up temp file.")

    # Show sample structure
    sample_dirs = [d for d in EXTRACT_DIR.iterdir() if d.is_dir()]
    if sample_dirs:
        first = sorted(sample_dirs)[0]
        # Handle nested structure
        while True:
            subdirs = [d for d in first.iterdir() if d.is_dir()]
            files = [f for f in first.iterdir() if f.is_file()]
            if files:
                break
            if subdirs:
                first = subdirs[0]
            else:
                break
        print(f"\nSample directory ({first.name}):")
        for f in sorted(first.iterdir()):
            print(f"  {f.name} ({f.stat().st_size} bytes)")


if __name__ == "__main__":
    download_and_extract()
