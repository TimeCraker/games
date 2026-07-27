# -*- coding: utf-8 -*-
"""Build hand-directed game portraits and an optimized menu hero image.

The source set contains two photos and two illustrations. Automatic frontal-face
recognition is intentionally not used: two subjects are profiles/looking down and
were previously misdetected as grass, sky, and fabric.
"""
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter

SOURCE = Path.home() / "Pictures" / "消消乐用"
ROOT = Path(__file__).resolve().parents[1]
FACE_DIR = ROOT / "public" / "assets" / "faces"
BG_DIR = ROOT / "public" / "assets" / "backgrounds"


def source_by_size(size):
    for path in SOURCE.iterdir():
        if path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
            continue
        with Image.open(path) as image:
            if image.size == size:
                return path
    raise FileNotFoundError(f"No source image with size {size}")


def crop_square(path, box, brightness=1.0, contrast=1.0, color=1.0):
    image = Image.open(path).convert("RGB").crop(box)
    image = ImageEnhance.Brightness(image).enhance(brightness)
    image = ImageEnhance.Contrast(image).enhance(contrast)
    image = ImageEnhance.Color(image).enhance(color)
    image = image.resize((512, 512), Image.Resampling.LANCZOS)
    return image.filter(ImageFilter.UnsharpMask(radius=1.2, percent=110, threshold=3))


def main():
    FACE_DIR.mkdir(parents=True, exist_ok=True)
    BG_DIR.mkdir(parents=True, exist_ok=True)

    minecraft = source_by_size((678, 1083))
    sunset = source_by_size((3414, 1920))
    selfie = source_by_size((1546, 1928))
    anime = source_by_size((1672, 941))

    recipes = [
        # Two seated characters, with foreground grass excluded.
        (minecraft, (174, 566, 524, 916), 1.06, 1.08, 1.12),
        # Sunset profile; lift shadows so the face remains legible at 40px.
        (sunset, (980, 500, 1700, 1220), 1.23, 0.98, 1.10),
        # Mirror portrait, composed around hair and face rather than clothing.
        (selfie, (410, 185, 1190, 965), 1.04, 1.08, 1.04),
        # Anime portrait focused on the face/headphones.
        (anime, (195, 0, 835, 640), 1.03, 1.08, 1.12),
    ]
    for index, (path, box, brightness, contrast, color) in enumerate(recipes):
        result = crop_square(path, box, brightness, contrast, color)
        output = FACE_DIR / f"face{index}.jpg"
        result.save(output, "JPEG", quality=92, optimize=True, progressive=True)
        print(f"face{index}: {path.name} {box} -> {output}")

    # Cinematic menu cover. Preserve the original composition and optimize for web.
    hero = Image.open(sunset).convert("RGB")
    hero = ImageEnhance.Contrast(hero).enhance(1.04)
    hero = ImageEnhance.Color(hero).enhance(1.06)
    hero.thumbnail((1920, 1080), Image.Resampling.LANCZOS)
    hero.save(BG_DIR / "hero-sunset.webp", "WEBP", quality=84, method=6)
    print(f"hero: {sunset.name} -> {BG_DIR / 'hero-sunset.webp'}")


if __name__ == "__main__":
    main()
