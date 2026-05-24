#!/usr/bin/env python3
"""
Reorganize public/ to production paths under /images/, remove junk, update src references.
Run: python scripts/reorganize_public_assets.py
"""

from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
SRC = ROOT / "src"
IMAGES = PUBLIC / "images"

RASTER = {".webp", ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".avif"}
KEEP_SVG = {"vercel.svg", "file.svg", "window.svg"}


def win_long(path: Path) -> Path:
    resolved = path.resolve()
    if sys.platform != "win32":
        return resolved
    s = str(resolved)
    if s.startswith("\\\\?\\") or len(s) < 240:
        return resolved
    return Path("\\\\?\\" + s)


def safe_copy(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(win_long(src), win_long(dst))


def find_one(directory: Path, pattern: str) -> Path | None:
    matches = list(directory.glob(pattern))
    return matches[0] if matches else None


def build_moves() -> list[tuple[Path, Path]]:
    moves: list[tuple[Path, Path]] = []

    def add(src_rel: str, dst_rel: str) -> None:
        src = PUBLIC / src_rel.replace("/", "\\") if "\\" not in src_rel else PUBLIC / src_rel
        if not src.exists():
            src = PUBLIC / src_rel
        if src.exists():
            moves.append((src, IMAGES / dst_rel))

    # Brand & hero
    add("h2hLogo-caps.webp", "brand/logo-caps.webp")
    add("h2h-short-logo.webp", "brand/logo-short.webp")
    add("hero-section-banner.webp", "hero/home-banner.webp")

    # Clinic (misc)
    clinic = PUBLIC / "misc"
    if clinic.is_dir():
        for f in clinic.glob("*.webp"):
            moves.append((f, IMAGES / "clinic" / f.name))

    # Services (long AI filenames -> short)
    svc = PUBLIC / "services-images"
    svc_map = [
        ("*nutrition*", "services/nutrition-coaching.webp"),
        ("*physiotherapy_service*", "services/physiotherapy-hero.webp"),
        ("*therapeutic_yoga*", "services/therapeutic-yoga-hero.webp"),
        ("*advanced_rehabilitation*", "services/advanced-rehab-hero.webp"),
        ("*general_healthcare*", "services/wellness-consultation.webp"),
        ("*mental_wellness*", "services/mental-wellness-hero.webp"),
    ]
    if svc.is_dir():
        for pattern, dest in svc_map:
            hit = find_one(svc, pattern)
            if hit:
                moves.append((hit, IMAGES / dest))

    # About
    about = PUBLIC / "about-us"
    about_map = [
        ("*home_visits*", "about/home-visits.webp"),
        ("*expert_care*", "about/expert-care.webp"),
        ("*patient_first_care*", "about/patient-first-care.webp"),
        ("*evidence_led*", "about/evidence-led-workspace.webp"),
    ]
    if about.is_dir():
        for pattern, dest in about_map:
            hit = find_one(about, pattern)
            if hit:
                moves.append((hit, IMAGES / dest))
    add("about-us/akshat.webp", "about/team-akshat.webp")
    add("about-us/deepti-4k.webp", "about/team-deepti.webp")
    add("founders-image--4k.webp", "about/founders-group.webp")

    # Team
    for name, dest in [
        ("sayandeeppaul.webp", "team/sayandeep-paul.webp"),
        ("rishav.webp", "team/rishav.webp"),
        ("sayantan.webp", "team/sayantan.webp"),
    ]:
        add(f"our-team/{name}", dest)

    # Excellence (only used set)
    exc_map = [
        ("ccl.webp", "excellence/ccl-trophy.webp"),
        ("football.webp", "excellence/football-training.webp"),
        ("sai-ncoe-yoga.webp", "excellence/sai-ncoe-yoga.webp"),
        ("phsio-image-akshat.webp", "excellence/physio-akshat.webp"),
    ]
    for src_name, dest in exc_map:
        add(f"our-excellence/{src_name}", dest)

    # Partners
    partners = PUBLIC / "trusted-logos"
    if partners.is_dir():
        for f in sorted(partners.glob("logo*.webp")):
            num = re.search(r"logo(\d+)", f.name)
            if num:
                moves.append((f, IMAGES / "partners" / f"partner-{int(num.group(1)):02d}.webp"))

    return moves


def apply_moves(moves: list[tuple[Path, Path]]) -> dict[str, str]:
    url_map: dict[str, str] = {}
    for src, dst in moves:
        safe_copy(src, dst)
        old_url = "/" + src.relative_to(PUBLIC).as_posix()
        new_url = "/" + dst.relative_to(PUBLIC).as_posix()
        url_map[old_url] = new_url
        print(f"  {old_url} -> {new_url}")
    return url_map


def delete_path(path: Path) -> None:
    long = win_long(path)
    if long.is_file():
        long.unlink(missing_ok=True)
    elif long.is_dir():
        shutil.rmtree(long, ignore_errors=True)


def delete_tree(directory: Path) -> None:
    """Remove a directory tree (handles Windows long paths)."""
    long = win_long(directory)
    if long.is_dir():
        shutil.rmtree(long, ignore_errors=True)


def cleanup_public(keep_urls: set[str]) -> None:
    # WhatsApp & unoptimized rasters at root
    for f in PUBLIC.rglob("*"):
        if not f.is_file():
            continue
        rel = "/" + f.relative_to(PUBLIC).as_posix()
        if f.name in KEEP_SVG:
            continue
        if f.suffix.lower() not in RASTER and f.suffix.lower() != ".json":
            continue
        if rel in keep_urls:
            continue
        if "images/" in rel:
            continue
        if "WhatsApp" in f.name:
            delete_path(f)
            print(f"  removed {rel}")
            continue
        if f.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff"}:
            delete_path(f)
            print(f"  removed unoptimized {rel}")
            continue
        # Old webp outside /images/
        if f.suffix.lower() == ".webp":
            delete_path(f)
            print(f"  removed legacy webp {rel}")

    for folder in (
        "misc",
        "services-images",
        "about-us",
        "our-excellence",
        "our-team",
        "trusted-logos",
        "featured-cards",
    ):
        p = PUBLIC / folder
        if p.exists():
            delete_tree(p)
            print(f"  removed folder {folder}/")

    for name in (
        ".image-optimization-manifest.json",
        "founders-image.webp",
        "contact-us.webp",
        "mens-hockey.webp",
        "striver-coach.webp",
        "h2h-fulltext.webp",
        "h2hLogo-normal.webp",
        "h2hwebsitelogo.webp",
        "ncr.avif",
        "chd.avif",
        "kolk.avif",
    ):
        p = PUBLIC / name
        if p.exists():
            delete_path(p)
            print(f"  removed {name}")


def update_code(url_map: dict[str, str]) -> int:
  # Longest paths first; also map old misc path prefix to clinic
    replacements = sorted(url_map.items(), key=lambda x: len(x[0]), reverse=True)

    extra = [
        ("/misc/", "/images/clinic/"),
        ("/services-images/", "/images/services/"),
        ("/about-us/", "/images/about/"),
        ("/our-excellence/", "/images/excellence/"),
        ("/our-team/", "/images/team/"),
        ("/trusted-logos/", "/images/partners/"),
        ("/hero-section-banner.webp", "/images/hero/home-banner.webp"),
        ("/h2hLogo-caps.webp", "/images/brand/logo-caps.webp"),
        ("/h2h-short-logo.webp", "/images/brand/logo-short.webp"),
        ("/founders-image--4k.webp", "/images/about/founders-group.webp"),
        ("/founders-image--4k", "/images/about/founders-group"),
        ("logo1.webp", "partner-01.webp"),
        ("logo2.webp", "partner-02.webp"),
        ("logo3.webp", "partner-03.webp"),
        ("logo4.webp", "partner-04.webp"),
        ("logo5.webp", "partner-05.webp"),
        ("logo6.webp", "partner-06.webp"),
        ("logo7.webp", "partner-07.webp"),
        ("logo8.webp", "partner-08.webp"),
        ("logo10.webp", "partner-10.webp"),
        ("/our-excellence/ccl.webp", "/images/excellence/ccl-trophy.webp"),
        ("/our-excellence/football.webp", "/images/excellence/football-training.webp"),
        ("/our-excellence/phsio-image-akshat.webp", "/images/excellence/physio-akshat.webp"),
        (
            "/services-images/high_quality_professional_lifestyle_photography_for_a_nutrition_and_lifestyle_coaching_service._a_beautiful_top_down_shot_of_a_healthy_vibrant_meal_like_a_nourish_bowl_with_fresh_vegetables_grains_and_protein_on_a_.webp",
            "/images/services/nutrition-coaching.webp",
        ),
        (
            "/about-us/professional_lifestyle_photography_for_a_home_visits_section._a_friendly_healthcare_professional_entering_a_bright_comfortable_and_modern_home_environment_greeted_warmly_by_a_patient._the_shot_is_wide_and_inviting_.webp",
            "/images/about/home-visits.webp",
        ),
    ]
    for a, b in extra:
        if a not in dict(replacements):
            replacements.append((a, b))

    replacements.sort(key=lambda x: len(x[0]), reverse=True)
    changed = 0
    files = list(SRC.rglob("*")) + [ROOT / "next.config.ts"]
    for fp in files:
        if fp.suffix not in {".ts", ".tsx", ".js", ".jsx"}:
            continue
        text = fp.read_text(encoding="utf-8")
        orig = text
        for old, new in replacements:
            text = text.replace(old, new)
        if text != orig:
            fp.write_text(text, encoding="utf-8")
            changed += 1
    return changed


def main() -> None:
    print("\n  Reorganize public assets\n  ========================\n")
    moves = build_moves()
    if not moves:
        print("  No files to move.")
        sys.exit(1)

    print("  Copying to public/images/ ...\n")
    url_map = apply_moves(moves)
    keep = set(url_map.values())

    print("\n  Cleaning up legacy paths ...\n")
    cleanup_public(keep)

    print("\n  Updating source references ...\n")
    n = update_code(url_map)
    print(f"\n  Done. {len(moves)} assets in /images/, {n} code files updated.\n")


if __name__ == "__main__":
    main()
