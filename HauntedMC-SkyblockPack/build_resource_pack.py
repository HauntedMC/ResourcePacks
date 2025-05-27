#!/usr/bin/env python3
"""
build_resource_pack.py
──────────────────────

Usage:
    python build_resource_pack.py                       # build only
    python build_resource_pack.py --install ~/.minecraft/resourcepacks
    python build_resource_pack.py --protect --install ~/.minecraft/resourcepacks
"""

from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import struct
import argparse
import os
import shutil
import sys
import hashlib

# ---------------------------------------------------------------------------
# Paths & constants
# ---------------------------------------------------------------------------
BUILD_DIR = Path("build")
ZIP_NAME  = BUILD_DIR / "HauntedMC-SkyblockPack.zip"
PACK_META = Path("pack.mcmeta")
PACK_PNG  = Path("pack.png")

# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------
def zip_resource_pack() -> None:
    """Create / overwrite build/HauntedMC-GlobalPack.zip"""
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

def protect_zip(zip_path: Path) -> None:
    """
    Overwrite each Central Directory entry's CRC32 and size fields with bogus values
    so that most unzip tools will refuse to extract, while Java's ZipInputStream
    will still stream the actual data.
    """
    data = zip_path.read_bytes()
    i = 0
    bogus = 0xDEADBEEF

    while True:
        sig = data.find(b"PK\x01\x02", i)
        if sig < 0:
            break

        crc_off  = sig + 16  # CRC32
        size_off = sig + 20  # compressed size
        comp_off = sig + 24  # uncompressed size

        # stomp 4 bytes at each offset
        data = (
            data[:crc_off]
            + bogus.to_bytes(4, "little")
            + data[crc_off+4:size_off]
            + bogus.to_bytes(4, "little")
            + data[size_off+4:comp_off]
            + bogus.to_bytes(4, "little")
            + data[comp_off+4:]
        )

        bogus = (bogus + 1) & 0xFFFFFFFF
        i = sig + 1

    zip_path.write_bytes(data)
    print(f"🔐  Applied unzip protection to {zip_path.name}")

def install_zip(target: Path) -> None:
    """Copy the built zip into a Minecraft resourcepacks dir."""
    dest_dir = target.expanduser().resolve()
    if not dest_dir.is_dir():
        sys.exit(f"Error: {dest_dir} is not a directory.")
    dest = dest_dir / ZIP_NAME.name
    shutil.copy2(ZIP_NAME, dest)
    print(f"📦  Installed {ZIP_NAME.name} → {dest}")


def compute_sha1(path: Path) -> None:
    """Compute and store SHA-1 digest of the zip."""
    h = hashlib.sha1()
    with path.open('rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    digest = h.hexdigest()
    sha_file = path.with_suffix(path.suffix + '.sha1')
    sha_file.write_text(digest)
    print(f"🔒  SHA-1 ({path.name}) = {digest}")
    print(f"📝  Wrote hash to {sha_file}")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build a Minecraft resource pack zip.")
    p.add_argument(
        "--protect",
        action="store_true",
        help="After building, overwrite the ZIP's central directory CRC/sizes to block unzip"
    )
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
    if args.protect:
        protect_zip(ZIP_NAME)
    if args.install:
        install_zip(args.install)
    compute_sha1(ZIP_NAME)
    print("✅  Done!")


if __name__ == '__main__':
    main()

