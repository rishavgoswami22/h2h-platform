#!/usr/bin/env python3
"""
Re-optimize excellence WebPs from raster sources.

Place source JPG/PNG in public/images/excellence/_sources/ (same basenames as
RENAME keys) or restore from git history, then run: npm run assets:excellence
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "public" / "images" / "excellence" / "_sources"
DST_DIR = ROOT / "public" / "images" / "excellence"

# Original filename -> production WebP name
RENAME: dict[str, str] = {
    "archery.jpg": "archery-team.webp",
    "award.jpg": "award-ceremony.webp",
    "award2.jpeg": "award-ceremony-alt.webp",
    "bengal-u19.jpg": "bengal-u19-cricket.webp",
    "ccl.jpg": "ccl-cricket.webp",
    "ccl2.jpg": "ccl-cricket-2.webp",
    "ccl3.jpg": "ccl-cricket-3.webp",
    "cricket.jpg": "cricket-match.webp",
    "cricket2.jpg": "cricket-match-alt.webp",
    "football-img.jpg": "football-athlete.webp",
    "football.jpg": "football-duo.webp",
    "gym-image-akshat.jpeg": "gym-group-akshat.webp",
    "hockey-champion.jpg": "hockey-champions.webp",
    "image-gym-akshat.jpeg": "gym-session-akshat.webp",
    "mens-hockey.jpg": "mens-hockey-team.webp",
    "phsio-image-akshat.jpeg": "physio-akshat.webp",
    "president-with.jpg": "leadership-visit.webp",
    "rcb-womens.jpg": "rcb-womens.webp",
    "sai-ncoe-yoga.png": "sai-ncoe-yoga.webp",
}


def convert(src: Path, dst: Path, max_px: int = 1920, quality: int = 82) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as im:
        im = ImageOps.exif_transpose(im)
        w, h = im.size
        if max(w, h) > max_px:
            scale = max_px / max(w, h)
            im = im.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)
        if im.mode not in ("RGB", "RGBA"):
            im = im.convert("RGBA" if "A" in im.getbands() else "RGB")
        im.save(dst, format="WEBP", quality=quality, method=6, optimize=True)


def main() -> None:
    if not SRC_DIR.is_dir():
        print(f"No sources in {SRC_DIR.relative_to(ROOT)}")
        print("  Add originals there, or: git checkout HEAD -- public/our-excellence")
        print("  then point SRC_DIR at that folder once, run this script, and delete our-excellence.")
        sys.exit(1)

    DST_DIR.mkdir(parents=True, exist_ok=True)
    done = 0
    for src_name, dst_name in RENAME.items():
        src = SRC_DIR / src_name
        if not src.exists():
            print(f"  skip missing {src_name}")
            continue
        dst = DST_DIR / dst_name
        convert(src, dst)
        print(f"  {src_name} -> {dst_name}")
        done += 1

    print(f"\n  {done} excellence images ready in {DST_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
