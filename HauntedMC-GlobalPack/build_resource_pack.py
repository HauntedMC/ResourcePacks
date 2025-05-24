#!/usr/bin/env python3
"""
build_resource_pack.py
──────────────────────
1. Copies lang.json → assets/minecraft/lang/<lang>.json          (128 files)
2. Creates / overwrites build/HauntedMC-GlobalPack.zip containing:
       • assets/   (recursive)
       • pack.mcmeta
       • pack.png
3. If --install <DIR> is supplied, also copies the ZIP into <DIR>.
4. Calculates the SHA-1 hash of the generated ZIP, prints it, and writes it to build/HauntedMCThemeRP.zip.sha1

Examples
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
import hashlib  # Added for SHA-1 hashing

# ---------------------------------------------------------------------------
# Raw filenames (abbreviated in this comment for brevity)
# ---------------------------------------------------------------------------
FILES_RAW = """
af_za.json be_latn.json cy_gb.json en_ca.json enws.json es_mx.json fil_ph.json ga_ie.json hu_hu.json it_it.json ksh.json lol_us.json mt_mt.json oc_fr.json rpr.json so_so.json ta_in.json tzo_mx.json yo_ng.json
ar_sa.json bg_bg.json da_dk.json en_gb.json eo_uy.json es_uy.json fo_fo.json gd_gb.json hy_am.json ja_jp.json kw_gb.json lt_lt.json nds_de.json ovd.json ru_ru.json sq_al.json th_th.json uk_ua.json zh_cn.json
ast_es.json brb.json de_at.json en_nz.json esan.json es_ve.json fra_de.json gl_es.json id_id.json jbo_en.json la_la.json lv_lv.json pl_pl.json ry_ua.json sr_cs.json tlh_aa.json val_es.json zh_hk.json
az_az.json br_fr.json de_ch.json enp.json es_ar.json et_ee.json fr_ca.json haw_us.json ig_ng.json ka_ge.json lb_lu.json lzh.json nl_be.json pt_br.json sah_sah.json sr_sp.json tl_ph.json vec_it.json zh_tw.json
bar.json bs_ba.json de_de.json en_pt.json es_cl.json eu_es.json fr_fr.json he_il.json io_en.json kn_in.json lmo.json mn_mn.json nn_no.json ro_ro.json sl_si.json szl.json tr_tr.json vp_vl.json
ba_ru.json ca_es.json el_gr.json en_ud.json es_ec.json fa_ir.json fur_it.json hi_in.json is_is.json ko_kr.json lo_la.json ms_my.json no_no.json sk_sk.json sxu.json tt_ru.json yi_de.json
be_by.json cs_cz.json en_au.json en_us.json es_es.json fi_fi.json fy_nl.json hr_hr.json isv.json li_li.json mk_mk.json nl_nl.json pt_pt.json se_no.json sv_se.json tok.json vi_vn.json zlm_arab.json
"""

LANG_CODES = [f.split(".")[0] for f in FILES_RAW.split() if f.endswith(".json")]

# ---------------------------------------------------------------------------
# Paths & constants
# ---------------------------------------------------------------------------
TEMPLATE   = Path("lang.json")
DEST_DIR   = Path("assets/minecraft/lang")

BUILD_DIR  = Path("build")                       # <── new build folder
ZIP_NAME   = BUILD_DIR / "HauntedMC-GlobalPack.zip"  # zip now lives here

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
    sync_languages()
    zip_resource_pack()
    if args.install:
        install_zip(args.install)
    # New step: compute and store SHA-1 hash of the zip
    compute_sha1(ZIP_NAME)
    print("✅  Done!")

if __name__ == "__main__":
    main()

