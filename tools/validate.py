"""Check index.json: unique ids, known tags, valid colors, existing previews."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GROUPS = json.loads((ROOT / "tools" / "tags.json").read_text())
TAGS = {tag for group in GROUPS.values() for tag in group}
HEX = re.compile(r"^#[0-9a-f]{6}$")
ID = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
RELEASE = re.compile(r"^batch-\d{3}$")

errors = []
index = json.loads((ROOT / "index.json").read_text(encoding="utf-8"))
seen = set()
for entry in index:
    set_id = entry.get("id", "?")
    if entry.get("schema") != 1:
        errors.append(f"{set_id}: schema must be 1")
    if not ID.match(set_id):
        errors.append(f"{set_id}: id must be kebab-case")
    if set_id in seen:
        errors.append(f"{set_id}: duplicate id")
    seen.add(set_id)
    if not entry.get("title"):
        errors.append(f"{set_id}: title is missing")
    if entry.get("category") not in GROUPS["category"]:
        errors.append(f"{set_id}: unknown category")
    if entry.get("style") not in GROUPS["style"] or entry["style"] not in entry.get("tags", []):
        errors.append(f"{set_id}: style must be one of its style tags")
    if not RELEASE.match(entry.get("release", "")):
        errors.append(f"{set_id}: release must look like batch-001")
    unknown = [t for t in entry.get("tags", []) if t not in TAGS]
    if unknown:
        errors.append(f"{set_id}: unknown tags {unknown}")
    for key in ("bottom", "menu", "accent"):
        if not HEX.match(entry.get("colors", {}).get(key, "")):
            errors.append(f"{set_id}: colors.{key} must be #rrggbb")
    if not (ROOT / entry.get("preview", "")).is_file():
        errors.append(f"{set_id}: preview file is missing")

print("\n".join(errors) or f"index.json OK, {len(index)} sets")
sys.exit(1 if errors else 0)
