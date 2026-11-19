"""Turn a folder of master images plus metadata into gallery sets.

Each set in the input folder is one image (PNG, JPEG or WebP) and a JSON file
with the same name (schema, id, title, category, tags, colors). For every set the
script upscales the image to 3840 px, checks the safe areas, cuts the header
(top strip) and the wallpaper (the rest), writes a preview, and adds the set to
index.json. With --upload the full images go to the GitHub release named by
--batch.

    python tools/pipeline.py INPUT_DIR --batch batch-001 [--upscaler PATH] [--upload]

Needs Pillow. The upscaler is realesrgan-ncnn-vulkan with the
digital-art-4x model (realesrgan-x4plus for photo styles); without --upscaler, images are scaled plainly.
"""
import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageFilter, ImageStat

ROOT = Path(__file__).resolve().parent.parent
WIDTH = 3840
HEADER_HEIGHT = WIDTH // 12  # the add-on cuts the same 12:1 strip
GROUPS = json.loads((ROOT / "tools" / "tags.json").read_text())
TAGS = {tag for group in GROUPS.values() for tag in group}
HEX = re.compile(r"^#[0-9a-f]{6}$")
ID = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def lightness(hex_color):
    r, g, b = (int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5))
    return .2126 * r + .7152 * g + .0722 * b


def check_meta(meta, known_ids):
    errors = []
    if meta.get("schema") != 1:
        errors.append("schema must be 1")
    if not ID.match(meta.get("id", "")):
        errors.append("id must be kebab-case")
    elif meta["id"] in known_ids:
        errors.append(f"id {meta['id']} already exists")
    if not meta.get("title"):
        errors.append("title is missing")
    unknown = [t for t in meta.get("tags", []) if t not in TAGS]
    if unknown:
        errors.append("unknown tags: " + ", ".join(unknown))
    if meta.get("category") not in GROUPS["category"]:
        errors.append("category must be one of " + ", ".join(GROUPS["category"]))
    if len([t for t in meta.get("tags", []) if t in GROUPS["style"]]) != 1:
        errors.append("use exactly one style tag")
    if not 5 <= len(meta.get("tags", [])) <= 14:
        errors.append("use 5 to 14 tags")
    colors = meta.get("colors", {})
    for key in ("bottom", "menu", "accent"):
        if not HEX.match(str(colors.get(key, "")).lower()):
            errors.append(f"colors.{key} must be #rrggbb")
    return errors


# Photo styles upscale with the photo model; digital-art paints over fine
# photographic detail such as windows and facades.
PHOTO_STYLES = {"photorealistic", "cinematic", "realistic"}


def upscale(path, upscaler, style):
    image = Image.open(path).convert("RGB")
    if image.width < WIDTH and upscaler:
        with tempfile.TemporaryDirectory() as tmp:
            source, target = Path(tmp) / "in.png", Path(tmp) / "out.png"
            image.save(source)
            exe = Path(upscaler)
            # Small tiles and one thread keep the GPU load low and even; the
            # default large tiles made an older graphics card whine audibly.
            subprocess.run([str(exe), "-i", str(source), "-o", str(target), "-n", "realesrgan-x4plus" if style in PHOTO_STYLES else "digital-art-4x",
                            "-m", str(exe.parent / "models"), "-t", "64", "-j", "1:1:1"],
                           check=True, capture_output=True)
            image = Image.open(target).convert("RGB")
    height = round(image.height * WIDTH / image.width)
    return image.resize((WIDTH, height), Image.LANCZOS)


def percentile(gray, share):
    histogram = gray.histogram()
    limit, seen = share * sum(histogram), 0
    for value, count in enumerate(histogram):
        seen += count
        if seen >= limit:
            return value / 255
    return 1


def fingerprint(image):
    """Difference hash: 256 bits that barely change for near-identical pictures."""
    pixels = list(image.convert("L").resize((17, 16)).get_flattened_data())
    return sum(1 << i for i in range(256) if pixels[i // 16 * 17 + i % 16] > pixels[i // 16 * 17 + i % 16 + 1])


def soft_warnings(image):
    """Hints, not failures: flat or soft pictures. Thresholds measured on the
    first 107 sets, where the median contrast was 24."""
    gray = image.convert("L").resize((960, round(image.height * 960 / image.width)))
    contrast = ImageStat.Stat(gray).stddev[0]
    detail = ImageStat.Stat(gray.filter(ImageFilter.FIND_EDGES)).mean[0]
    hints = []
    if contrast < 13:
        hints.append(f"low contrast ({contrast:.0f})")
    if detail < 3.5:
        hints.append(f"little detail ({detail:.1f})")
    return hints


def check_image(image, light):
    """Measured rules from the prompt; returns a list of failures."""
    errors = []
    ratio = image.width / image.height
    if not 1.5 <= ratio <= 2.4:
        errors.append(f"aspect ratio {ratio:.2f}, expected 3:2 to 2:1")
    gray = image.convert("L")
    w, h = gray.size
    left = gray.crop((0, 0, int(w * .15), h))
    top_left = gray.crop((0, 0, w // 2, int(h * .15)))
    bottom = gray.crop((0, int(h * .95), w, h))
    left_mean = ImageStat.Stat(left).mean[0] / 255
    left_detail = ImageStat.Stat(left.filter(ImageFilter.FIND_EDGES)).mean[0]
    if light:
        if left_mean < .55:
            errors.append(f"left edge too dark for a light set ({left_mean:.2f})")
        if percentile(top_left, .02) < .3:
            errors.append("dark spots behind the tab titles")
    else:
        if left_mean > .5:
            errors.append(f"left edge too bright ({left_mean:.2f})")
        if percentile(left, .99) > .75:
            errors.append("bright objects at the left edge")
        if percentile(top_left, .99) > .9:
            errors.append("bright spots behind the tab titles")
    # Subdued scenery is allowed at the left edge; only clutter fails. A
    # lantern and a tea house at the edge measured 5.1, dense hedges about 9.
    if left_detail > 7:
        errors.append(f"left edge too busy ({left_detail:.1f})")
    if ImageStat.Stat(bottom).stddev[0] / 255 > .12:
        errors.append("bottom edge does not settle into one color")
    return errors


README_SETS = 30


def write_readme(index):
    """Rebuild the preview grid between the markers in README.md: the newest
    sets only, so the page stays fast as the gallery grows."""
    path = ROOT / "README.md"
    text = path.read_text(encoding="utf-8")
    start, end = "<!-- sets:start -->", "<!-- sets:end -->"
    cells = [f'<a href="{e["preview"]}"><img src="{e["preview"]}" width="260" alt="{e["title"]}"></a><br>'
             f'<b>{e["title"]}</b><br><code>{e["id"]}</code>' for e in index[::-1][:README_SETS]]
    rows = ["<tr>" + "".join(f"<td>{c}</td>" for c in cells[i:i + 3]) + "</tr>" for i in range(0, len(cells), 3)]
    grid = "\n".join([start, "<table>", *rows, "</table>", "", f"{len(index)} sets; the newest {min(len(index), README_SETS)} are shown. "
                      "Browse all of them in the add-on or in [index.json](index.json).", end])
    path.write_text(text[:text.index(start)] + grid + text[text.index(end) + len(end):], encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input", type=Path)
    parser.add_argument("--batch", required=True, help="release tag, for example batch-001")
    parser.add_argument("--upscaler", help="path to realesrgan-ncnn-vulkan(.exe)")
    parser.add_argument("--upload", action="store_true", help="upload the images to the release")
    parser.add_argument("--force", action="store_true", help="keep sets that fail the image checks")
    args = parser.parse_args()

    index_path = ROOT / "index.json"
    index = json.loads(index_path.read_text()) if index_path.exists() else []
    known = {entry["id"] for entry in index}
    out = ROOT / "out" / args.batch
    out.mkdir(parents=True, exist_ok=True)
    (ROOT / "previews").mkdir(exist_ok=True)
    added, failed, warned = [], 0, 0
    hashes = {e["id"]: fingerprint(Image.open(ROOT / e["preview"])) for e in index if (ROOT / e["preview"]).is_file()}

    for meta_path in sorted(args.input.glob("*.json")):
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        image_path = next((p for p in meta_path.parent.glob(meta_path.stem + ".*")
                           if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")), None)
        meta["colors"] = {k: str(v).lower() for k, v in meta.get("colors", {}).items()}
        errors = check_meta(meta, known) + ([] if image_path else ["image is missing"])
        if errors:
            print(f"FAIL {meta_path.name}: " + "; ".join(errors))
            failed += 1
            continue
        light = lightness(meta["colors"]["menu"]) > .55
        image = upscale(image_path, args.upscaler, next(t for t in meta["tags"] if t in GROUPS["style"]))
        problems = check_image(image, light)
        if problems:
            print(f"{'WARN' if args.force else 'FAIL'} {meta['id']}: " + "; ".join(problems))
            if not args.force:
                failed += 1
                continue
        set_id = meta["id"]
        mark = fingerprint(image)
        twin = next((other for other, h in hashes.items() if bin(mark ^ h).count("1") <= 20), None)
        if twin:
            print(f"FAIL {set_id}: nearly identical to {twin}")
            failed += 1
            continue
        hints = soft_warnings(image)
        if hints:
            print(f"HINT {set_id}: " + "; ".join(hints))
            warned += 1
        hashes[set_id] = mark
        image.crop((0, 0, WIDTH, HEADER_HEIGHT)).save(out / f"{set_id}-header.jpg", quality=90)
        image.crop((0, HEADER_HEIGHT, WIDTH, image.height)).save(out / f"{set_id}-wallpaper.jpg", quality=90)
        image.resize((480, round(image.height * 480 / WIDTH)), Image.LANCZOS).save(
            ROOT / "previews" / f"{set_id}.jpg", quality=80)
        tags = sorted(set(meta["tags"]) | {"light" if light else "dark"})
        style = next(t for t in meta["tags"] if t in GROUPS["style"])
        index.append({"schema": 1, "id": set_id, "title": meta["title"], "category": meta["category"],
                      "style": style, "release": args.batch,
                      "tags": tags, "colors": meta["colors"], "preview": f"previews/{set_id}.jpg"})
        known.add(set_id)
        added.append(set_id)
        print(f"OK   {set_id}")

    index.sort(key=lambda entry: entry["id"])
    index_path.write_text(json.dumps(index, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    write_readme(index)
    print(f"{len(added)} added, {failed} failed, {warned} with hints")

    if args.upload and added:
        files = [str(out / f"{i}-{part}.jpg") for i in added for part in ("header", "wallpaper")]
        exists = subprocess.run(["gh", "release", "view", args.batch], capture_output=True).returncode == 0
        if not exists:
            subprocess.run(["gh", "release", "create", args.batch, "--title", args.batch,
                            "--notes", f"Images for {len(added)} sets."], check=True)
        subprocess.run(["gh", "release", "upload", args.batch, "--clobber", *files], check=True)
    return 1 if failed and not added else 0


if __name__ == "__main__":
    sys.exit(main())
