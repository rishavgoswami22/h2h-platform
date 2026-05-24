#!/usr/bin/env python3
"""
Convert and optimize raster images under public/ to WebP, then update src references.

Usage:
  pip install -r scripts/requirements-image-optimize.txt
  python scripts/optimize_images_to_webp.py
  python scripts/optimize_images_to_webp.py --update-code
  python scripts/optimize_images_to_webp.py --update-code --prune-originals
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

try:
    from PIL import Image, ImageOps
except ImportError:
    print("Install dependencies: pip install -r scripts/requirements-image-optimize.txt")
    sys.exit(1)

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_DIR = ROOT / "public"
SRC_DIR = ROOT / "src"
MANIFEST_PATH = PUBLIC_DIR / ".image-optimization-manifest.json"


def win_long_path(path: Path) -> Path:
    """Windows: enable paths >260 chars for Pillow and stat."""
    resolved = path.resolve()
    if sys.platform != "win32":
        return resolved
    text = str(resolved)
    if text.startswith("\\\\?\\"):
        return resolved
    if len(text) >= 240:
        return Path("\\\\?\\" + text)
    return resolved


def is_raster_file(path: Path) -> bool:
    try:
        return win_long_path(path).is_file()
    except OSError:
        return False

RASTER_EXT = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".tif"}
SKIP_NAME_PARTS = ("WhatsApp Image",)

# Paths that must keep a small PNG for favicon / legacy (also emit WebP for UI).
FAVICON_STEMS = {"h2h-short-logo", "h2hLogo-caps"}


@dataclass(frozen=True)
class Profile:
    max_px: int
    quality: int
    min_quality: int = 72
    method: int = 6


PROFILES: dict[str, Profile] = {
    "hero": Profile(max_px=2560, quality=84),
    "photo": Profile(max_px=1920, quality=82),
    "logo": Profile(max_px=960, quality=90),
    "thumb": Profile(max_px=1280, quality=80),
}


def pick_profile(rel_posix: str) -> Profile:
    lower = rel_posix.lower()
    if any(x in lower for x in ("logo", "trusted-logos", "h2h-short", "h2hlogo")):
        return PROFILES["logo"]
    if any(x in lower for x in ("hero", "banner", "og-image", "founders", "4k")):
        return PROFILES["hero"]
    if any(x in lower for x in ("team", "avatar", "thumb")):
        return PROFILES["thumb"]
    return PROFILES["photo"]


def should_skip(path: Path) -> bool:
    if path.suffix.lower() not in RASTER_EXT:
        return True
    if path.name.startswith("."):
        return True
    return any(part in path.name for part in SKIP_NAME_PARTS)


def resize_if_needed(img: Image.Image, max_px: int) -> Image.Image:
    w, h = img.size
    longest = max(w, h)
    if longest <= max_px:
        return img
    scale = max_px / longest
    new_size = (max(1, int(w * scale)), max(1, int(h * scale)))
    return img.resize(new_size, Image.Resampling.LANCZOS)


def to_webp_bytes(img: Image.Image, profile: Profile) -> bytes:
    from io import BytesIO

    buf = BytesIO()
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGBA" if "A" in img.getbands() else "RGB")
    save_kw: dict = {
        "format": "WEBP",
        "quality": profile.quality,
        "method": profile.method,
        "optimize": True,
    }
    if img.mode == "RGBA":
        save_kw["lossless"] = False
    img.save(buf, **save_kw)
    return buf.getvalue()


def optimize_png_favicon(src: Path) -> None:
    """Re-compress favicon PNGs in place (lossless-friendly) for layout metadata."""
    with Image.open(src) as im:
        im = ImageOps.exif_transpose(im)
        if im.mode not in ("RGBA", "RGB", "P"):
            im = im.convert("RGBA")
        elif im.mode == "P":
            im = im.convert("RGBA")
        im.save(src, format="PNG", optimize=True, compress_level=9)


def convert_file(src: Path, public_dir: Path, force: bool) -> dict | None:
    if should_skip(src):
        return None

    rel = src.relative_to(public_dir)
    rel_posix = rel.as_posix()
    dst = src.with_suffix(".webp")
    profile = pick_profile(rel_posix)

    src_long = win_long_path(src)
    dst_long = win_long_path(dst)
    src_mtime = src_long.stat().st_mtime
    if dst_long.exists() and not force and dst_long.stat().st_mtime >= src_mtime:
        return {
            "source": rel_posix,
            "webp": dst.relative_to(public_dir).as_posix(),
            "skipped": True,
            "bytes_before": src_long.stat().st_size,
            "bytes_after": dst_long.stat().st_size,
        }

    with Image.open(src_long) as im:
        im = ImageOps.exif_transpose(im)
        im = resize_if_needed(im, profile.max_px)
        data = to_webp_bytes(im, profile)

    # If WebP is larger than source (rare for PNG UI), lower quality once.
    if len(data) >= src_long.stat().st_size and src.suffix.lower() in {".jpg", ".jpeg"}:
        with Image.open(src_long) as im:
            im = ImageOps.exif_transpose(im)
            im = resize_if_needed(im, profile.max_px)
            lowered = Profile(
                max_px=profile.max_px,
                quality=profile.min_quality,
                method=profile.method,
            )
            data = to_webp_bytes(im, lowered)

    dst_long.write_bytes(data)

    stem = src.stem
    if stem in FAVICON_STEMS and src.suffix.lower() == ".png":
        optimize_png_favicon(src_long)

    before = src_long.stat().st_size
    after = dst_long.stat().st_size
    saved = max(0.0, (1 - after / before) * 100) if before else 0.0
    return {
        "source": rel_posix,
        "webp": dst.relative_to(public_dir).as_posix(),
        "skipped": False,
        "bytes_before": before,
        "bytes_after": after,
        "saved_pct": round(saved, 1),
        "profile": profile.__dict__,
    }


def collect_sources(public_dir: Path) -> list[Path]:
    files: list[Path] = []
    for path in public_dir.rglob("*"):
        if is_raster_file(path) and not should_skip(path):
            files.append(path)
    return sorted(files)


def update_source_references(manifest: list[dict], src_dir: Path, public_dir: Path) -> int:
    """Replace raster paths with .webp in src when WebP exists under public/."""
    replacements: list[tuple[str, str]] = []
    for entry in manifest:
        src_rel = entry["source"]
        webp_rel = entry["webp"]
        old_url = "/" + src_rel.replace("\\", "/")
        new_url = "/" + webp_rel.replace("\\", "/")
        if old_url != new_url:
            replacements.append((old_url, new_url))

    # Any file in public that has a .webp sibling (covers pruned originals).
    for webp in public_dir.rglob("*.webp"):
        stem_url = "/" + webp.relative_to(public_dir).with_suffix("").as_posix()
        for ext in (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff"):
            replacements.append((stem_url + ext, stem_url + ".webp"))
    # Dedupe, longest first
    deduped: dict[str, str] = {}
    for old, new in replacements:
        deduped[old] = new
    replacements = sorted(deduped.items(), key=lambda x: len(x[0]), reverse=True)

    exts = (".ts", ".tsx", ".js", ".jsx", ".json", ".md")
    changed_files = 0

    def apply_replacements(path: Path) -> bool:
        text = path.read_text(encoding="utf-8")
        original = text
        for old, new in replacements:
            if old in text:
                text = text.replace(old, new)
        if text != original:
            path.write_text(text, encoding="utf-8")
            return True
        return False

    for file in src_dir.rglob("*"):
        if file.suffix in exts and apply_replacements(file):
            changed_files += 1

    for cfg in (ROOT / "next.config.ts",):
        if cfg.exists() and apply_replacements(cfg):
            changed_files += 1

    return changed_files


def prune_originals(manifest: list[dict], public_dir: Path) -> int:
    removed = 0
    for entry in manifest:
        if entry.get("skipped"):
            continue
        src = public_dir / entry["source"]
        src_long = win_long_path(src)
        if not src_long.exists():
            continue
        stem = src.stem
        if stem in FAVICON_STEMS:
            continue
        webp = public_dir / entry["webp"]
        webp_long = win_long_path(webp)
        if webp_long.exists() and webp_long.stat().st_size < src_long.stat().st_size:
            src_long.unlink()
            removed += 1
    return removed


def main() -> None:
    parser = argparse.ArgumentParser(description="Optimize public images to WebP.")
    parser.add_argument("--public-dir", type=Path, default=PUBLIC_DIR)
    parser.add_argument("--force", action="store_true", help="Reconvert even if WebP is newer.")
    parser.add_argument("--update-code", action="store_true", help="Rewrite src/ paths to .webp.")
    parser.add_argument(
        "--prune-originals",
        action="store_true",
        help="Delete originals when WebP is smaller (keeps favicon PNGs).",
    )
    args = parser.parse_args()

    public_dir: Path = args.public_dir.resolve()
    if not public_dir.is_dir():
        print(f"Public directory not found: {public_dir}")
        sys.exit(1)

    print("\n  H2H image optimizer (WebP)")
    print("  ==========================\n")
    print(f"  Scanning: {public_dir}\n")

    sources = collect_sources(public_dir)
    manifest: list[dict] = []
    converted = 0

    for src in sources:
        result = convert_file(src, public_dir, args.force)
        if not result:
            continue
        manifest.append(result)
        if result.get("skipped"):
            print(f"  skip (up to date): {result['source']}")
        else:
            converted += 1
            pct = result.get("saved_pct", 0)
            print(f"  ok {result['source']} -> {result['webp']} ({pct}% smaller)")

    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    total_before = sum(m["bytes_before"] for m in manifest)
    total_after = sum(m["bytes_after"] for m in manifest)
    overall = (1 - total_after / total_before) * 100 if total_before else 0

    print("\n  --------------------------")
    print(f"  Converted: {converted} | Manifest: {len(manifest)} files")
    print(f"  Total: {total_before / 1024 / 1024:.1f} MB -> {total_after / 1024 / 1024:.1f} MB ({overall:.1f}% saved)")

    if args.update_code:
        n = update_source_references(manifest, SRC_DIR, public_dir)
        print(f"  Updated {n} source file(s) to use .webp paths.")

    if args.prune_originals:
        n = prune_originals(manifest, public_dir)
        print(f"  Pruned {n} original file(s).")

    print()


if __name__ == "__main__":
    main()
