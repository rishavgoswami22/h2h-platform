#!/usr/bin/env python3
"""Fail if any path in marketing-images.ts is missing on disk."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
text = (ROOT / "src/constants/marketing-images.ts").read_text(encoding="utf-8")
paths = set(re.findall(r"`(\$\{IMG\}[^`]+)`", text))
paths |= set(re.findall(r"'(/images/[^']+)'", text))
# Expand ${IMG} -> /images
paths = {p.replace("${IMG}", "/images") for p in paths}
missing = [p for p in sorted(paths) if not (PUBLIC / p.lstrip("/")).exists()]
if missing:
    print("Missing assets:")
    for m in missing:
        print(" ", m)
    sys.exit(1)
print(f"OK — {len(paths)} image paths verified.")
