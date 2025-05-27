#!/usr/bin/env python3
"""
build_resource_pack.py
──────────────────────
--------
python build_resource_pack.py                       # build only
python build_resource_pack.py --install ~/.minecraft/resourcepacks
"""

from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import argparse
import os
import shutil
import sys
import hashlib
import struct

# ---------------------------------------------------------------------------
# Paths & constants
# ---------------------------------------------------------------------------
BUILD_DIR  = Path("build")                           # <── new build folder
ZIP_NAME   = BUILD_DIR / "HauntedMC-SkyblockPack.zip"  # zip now lives here

PACK_META  = Path("pack.mcmeta")
PACK_PNG   = Path("pack.png")

# ---------------------------------------------------------------------------
# Functions
# ---------------------------------------------------------------------------
def zip_resource_pack() -> None:
    """Create / overwrite build/HauntedMC-<>Pack.zip"""
    for required in (PACK_META, PACK_PNG):
        if not required.is_file():
            sys.exit(f"Error: {required.name} not found in the current directory.")

    BUILD_DIR.mkdir(exist_ok=True)

    with ZipFile(ZIP_NAME, "w", ZIP_DEFLATED) as zf:
        # Add every file under assets/
        for root, _, files in os.walk("assets"):
            for fname in files:
                fp = Path(root, fname)
                zf.write(fp, arcname=fp.as_posix())
        # Add pack.mcmeta & pack.png
        zf.write(PACK_META, arcname=PACK_META.name)
        zf.write(PACK_PNG,  arcname=PACK_PNG.name)

    print(f"🗜️  Built {ZIP_NAME.resolve()}")

def install_zip(target_dir: Path) -> None:
    """Copy the generated ZIP to target_dir (overwrite if exists)"""
    target_dir = target_dir.expanduser().resolve()
    if not target_dir.is_dir():
        sys.exit(f"Error: {target_dir} is not a directory.")
    dest = target_dir / ZIP_NAME.name
    shutil.copy2(ZIP_NAME, dest)
    print(f"📦  Installed {ZIP_NAME.name} → {dest}")

def compute_sha1(file_path: Path) -> None:
    """Compute SHA-1 of the given file, print it, and save to .sha1 file"""
    sha1 = hashlib.sha1()
    with file_path.open('rb') as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            sha1.update(chunk)
    digest = sha1.hexdigest()
    sha_file = file_path.with_suffix(file_path.suffix + '.sha1')
    sha_file.write_text(digest)
    print(f"🔒  SHA-1 ({file_path.name}) = {digest}")
    print(f"📝  Wrote hash to {sha_file}")

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build a Minecraft resource pack zip.")
    p.add_argument(
        "--install",
        metavar="DIR",
        help="After building, copy the zip into DIR (e.g. ~/.minecraft/resourcepacks)",
        type=Path
    )
    return p.parse_args()

def main() -> None:
    args = parse_args()
    zip_resource_pack()
    if args.install:
        install_zip(args.install)
    compute_sha1(ZIP_NAME)
    print("✅  Done!")

if __name__ == "__main__":
    main()

