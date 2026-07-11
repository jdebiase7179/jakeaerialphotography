#!/usr/bin/env python3
"""Build the deployable site into _site/.

Scans photos/<category>/ for images, generates web-sized JPEGs and thumbnails,
and writes assets/gallery.json. Runs in GitHub Actions on every push, so
adding a photo to photos/ is all it takes to update the live gallery.

If photos/ is empty, the committed placeholder gallery.json is kept so the
site still renders a full-looking gallery.

Usage: python3 scripts/build_gallery.py   (requires Pillow)
"""

import json
import re
import shutil
import sys
from pathlib import Path

from PIL import Image, ImageOps

try:  # iPhone HEIC photos, if pillow-heif is installed
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    pass

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "_site"
PHOTOS = ROOT / "photos"

STATIC = ["index.html", "styles.css", "app.js", "assets"]
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".tif", ".tiff"}

# Folder name -> label shown on the filter buttons. Folders not listed here
# still work; they get a title-cased label automatically.
CATEGORY_LABELS = {
    "aerial": "Aerial",
    "real-estate": "Real Estate",
    "events": "Events",
    "automotive": "Automotive",
}

WEB_EDGE = 2000   # long edge for lightbox image
THUMB_EDGE = 800  # long edge for grid thumbnail


def humanize(stem: str) -> str:
    """DJI_0231-lakeview-house -> 'Lakeview house' (drops camera prefixes)."""
    words = re.sub(r"[_\-]+", " ", stem).strip()
    words = re.sub(r"^(dji|img|dsc|gopro|pano)[ ]*\d*[ ]*", "", words, flags=re.I).strip()
    return words[:1].upper() + words[1:] if words else "Photo"


def process(src: Path, dest_dir: Path) -> dict:
    dest_dir.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as im:
        im = ImageOps.exif_transpose(im)
        if im.mode != "RGB":
            im = im.convert("RGB")
        w, h = im.size

        web = im.copy()
        web.thumbnail((WEB_EDGE, WEB_EDGE))
        web_path = dest_dir / (src.stem + ".jpg")
        web.save(web_path, "JPEG", quality=82, optimize=True, progressive=True)

        thumb = im.copy()
        thumb.thumbnail((THUMB_EDGE, THUMB_EDGE))
        thumb_path = dest_dir / (src.stem + "_thumb.jpg")
        thumb.save(thumb_path, "JPEG", quality=78, optimize=True, progressive=True)

    return {
        "src": str(web_path.relative_to(OUT)),
        "thumb": str(thumb_path.relative_to(OUT)),
        "w": w,
        "h": h,
    }


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    for name in STATIC:
        src = ROOT / name
        if src.is_dir():
            shutil.copytree(src, OUT / name)
        else:
            shutil.copy2(src, OUT / name)

    items = []
    if PHOTOS.is_dir():
        for cat_dir in sorted(PHOTOS.iterdir()):
            if not cat_dir.is_dir():
                continue
            category = cat_dir.name
            label = CATEGORY_LABELS.get(category, category.replace("-", " ").title())
            for photo in sorted(cat_dir.iterdir(), reverse=True):
                if photo.suffix.lower() not in IMAGE_EXTS:
                    continue
                try:
                    entry = process(photo, OUT / "assets" / "gallery" / category)
                except Exception as exc:  # a bad file shouldn't sink the deploy
                    print(f"SKIPPED {photo}: {exc}", file=sys.stderr)
                    continue
                entry["alt"] = f"{label} — {humanize(photo.stem)}"
                entry["category"] = category
                entry["categoryLabel"] = label
                items.append(entry)
                print(f"  {photo} -> {entry['src']}")

    if items:
        (OUT / "assets" / "gallery.json").write_text(json.dumps(items, indent=1))
        # Real photos exist: the committed placeholders are no longer needed.
        shutil.rmtree(OUT / "assets" / "placeholder", ignore_errors=True)
        print(f"Built gallery with {len(items)} photos.")
    else:
        print("No photos found in photos/ — keeping placeholder gallery.")


if __name__ == "__main__":
    main()
