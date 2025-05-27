#!/usr/bin/env python3
"""
build_resource_pack.py
──────────────────────

Usage:
python build_resource_pack.py                       # build only
python build_resource_pack.py --protect            # build + protect
python build_resource_pack.py --install ~/.minecraft/resourcepacks
python build_resource_pack.py --protect --install ~/.minecraft/resourcepacks
"""

from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import argparse
import os
import shutil
import sys
import hashlib

# ---------------------------------------------------------------------------
# Raw filenames (abbreviated in this comment for brevity)
# ---------------------------------------------------------------------------
FILES_RAW = """
af_za.json be_latn.json cy_gb.json en_ca.json enws.json es_mx.json fil_ph.json
ga_ie.json hu_hu.json it_it.json ksh.json lol_us.json mt_mt.json oc_fr.json
rpr.json so_so.json ta_in.json tzo_mx.json yo_ng.json ar_sa.json bg_bg.json da_dk.json
en_gb.json eo_uy.json es_uy.json fo_fo.json gd_gb.json hy_am.json ja_jp.json kw_gb.json
lt_lt.json nds_de.json ovd.json ru_ru.json sq_al.json th_th.json uk_ua.json zh_cn.json
ast_es.json brb.json de_at.json en_nz.json esan.json es_ve.json fra_de.json gl_es.json
id_id.json jbo_en.json la_la.json lv_lv.json pl_pl.json ry_ua.json sr_cs.json tlh_aa.json
val_es.json zh_hk.json az_az.json br_fr.json de_ch.json enp.json es_ar.json et_ee.json
fr_ca.json haw_us.json ig_ng.json ka_ge.json lb_lu.json lzh.json nl_be.json pt_br.json
sah_sah.json sr_sp.json tl_ph.json vec_it.json zh_tw.json bar.json bs_ba.json de_de.json
en_pt.json es_cl.json eu_es.json fr_fr.json he_il.json io_en.json kn_in.json lmo.json mn_mn.json
nn_no.json ro_ro.json sl_si.json szl.json tr_tr.json vp_vl.json ba_ru.json ca_es.json el_gr.json
en_ud.json es_ec.json fa_ir.json fur_it.json hi_in.json is_is.json ko_kr.json lo_la.json
ms_my.json no_no.json sk_sk.json sxu.json tt_ru.json yi_de.json be_by.json cs_cz.json en_au.json
en_us.json es_es.json fi_fi.json fy_nl.json hr_hr.json isv.json li_li.json mk_mk.json nl_nl.json
pt_pt.json se_no.json sv_se.json tok.json vi_vn.json zlm_arab.json
"""

LANG_CODES = [f.split(".")[0] for f in FILES_RAW.split() if f.endswith(".json")]

# ---------------------------------------------------------------------------
# Paths & constants
# ---------------------------------------------------------------------------
TEMPLATE   = Path("lang.json")
DEST_DIR   = Path("assets/minecraft/lang")

BUILD_DIR  = Path("build")
ZIP_NAME   = BUILD_DIR / "HauntedMC-GlobalPack.zip"

PACK_META  = Path("pack.mcmeta")
PACK_PNG   = Path("pack.png")

# ---------------------------------------------------------------------------
# Functions
# ---------------------------------------------------------------------------
def sync_languages() -> None:
    """Copy lang.json → assets/minecraft/lang/<lang>.json"""
    if not TEMPLATE.is_file():
        sys.exit("Error: lang.json not found in the current directory.")
    DEST_DIR.mkdir(parents=True, exist_ok=True)
    data = TEMPLATE.read_bytes()
    for code in LANG_CODES:
        (DEST_DIR / f"{code}.json").write_bytes(data)
    print(f"📄  Wrote {len(LANG_CODES)} language files → {DEST_DIR}")

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
        while chunk := f.read(8192):
            sha1.update(chunk)
    digest = sha1.hexdigest()
    sha_file = file_path.with_suffix(file_path.suffix + '.sha1')
    sha_file.write_text(digest)
    print(f"🔒  SHA-1 ({file_path.name}) = {digest}")
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
    sync_languages()
    zip_resource_pack()
    if args.protect:
        protect_zip(ZIP_NAME)
    if args.install:
        install_zip(args.install)
    compute_sha1(ZIP_NAME)
    print("✅  Done!")

if __name__ == "__main__":
    main()

