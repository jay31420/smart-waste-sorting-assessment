"""Build the painterly opening-scene background from a public-domain source."""

from __future__ import annotations

import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / "assets" / "landscape_source_redmond.jpg"
OUTPUT_PATH = ROOT / "assets" / "scene_oil_landscape.png"
WIDTH = 1920
HEIGHT = 1080


def _fit_scene(source: Image.Image) -> Image.Image:
    target_ratio = WIDTH / HEIGHT
    source_ratio = source.width / source.height
    if source_ratio > target_ratio:
        crop_width = int(source.height * target_ratio)
        left = (source.width - crop_width) // 2
        source = source.crop((left, 0, left + crop_width, source.height))
    else:
        crop_height = int(source.width / target_ratio)
        top = int((source.height - crop_height) * 0.46)
        source = source.crop((0, top, source.width, top + crop_height))

    scene = source.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS).convert("RGB")
    scene = ImageEnhance.Color(scene).enhance(0.96)
    scene = ImageEnhance.Contrast(scene).enhance(0.96)
    scene = ImageEnhance.Brightness(scene).enhance(1.045)
    return scene


def _add_clouds(scene: Image.Image) -> Image.Image:
    cloud_layer = Image.new("RGBA", scene.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(cloud_layer)
    clouds = (
        (390, 92, 520, 58),
        (610, 76, 430, 48),
        (1210, 80, 280, 38),
        (1420, 134, 340, 45),
    )
    for x, y, width, height in clouds:
        draw.ellipse((x, y + height * 0.34, x + width, y + height), fill=(247, 245, 232, 118))
        draw.ellipse((x + width * 0.13, y, x + width * 0.58, y + height * 0.80), fill=(251, 249, 239, 132))
        draw.ellipse((x + width * 0.42, y + height * 0.12, x + width * 0.86, y + height * 0.78), fill=(238, 241, 228, 106))
    cloud_layer = cloud_layer.filter(ImageFilter.GaussianBlur(22))
    return Image.alpha_composite(scene.convert("RGBA"), cloud_layer)


def _add_people_and_bin(scene: Image.Image) -> Image.Image:
    scale = 3
    layer = Image.new("RGBA", (WIDTH * scale, HEIGHT * scale), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)

    def box(values: tuple[float, float, float, float]) -> tuple[int, int, int, int]:
        return tuple(int(value * scale) for value in values)

    # Soft ground shadows.
    draw.ellipse(box((505, 747, 782, 790)), fill=(49, 55, 46, 70))
    draw.ellipse(box((558, 735, 652, 770)), fill=(41, 51, 44, 70))

    # A simple modern two-stream bin, intentionally without labels or logos.
    draw.rounded_rectangle(box((680, 554, 792, 747)), radius=15 * scale, fill=(104, 111, 105, 226))
    draw.rounded_rectangle(box((673, 544, 799, 579)), radius=11 * scale, fill=(82, 91, 87, 238))
    draw.rounded_rectangle(box((699, 559, 773, 575)), radius=7 * scale, fill=(39, 51, 50, 245))
    draw.rounded_rectangle(box((696, 588, 776, 714)), radius=8 * scale, outline=(225, 221, 199, 74), width=2 * scale)
    draw.line(box((735, 586, 735, 722)), fill=(64, 73, 70, 220), width=2 * scale)
    draw.rounded_rectangle(box((697, 747, 720, 760)), radius=4 * scale, fill=(69, 76, 72, 230))
    draw.rounded_rectangle(box((753, 747, 776, 760)), radius=4 * scale, fill=(69, 76, 72, 230))
    draw.ellipse(box((685, 550, 790, 565)), fill=(182, 177, 159, 55))

    # Person seen from behind. No face is shown, and one hand is raised while dropping a bag.
    sage = (72, 101, 78, 245)
    sage_dark = (55, 80, 64, 245)
    trouser = (50, 62, 57, 245)
    skin = (188, 151, 119, 245)
    draw.ellipse(box((566, 530, 611, 579)), fill=sage_dark)
    draw.rounded_rectangle(box((560, 574, 617, 666)), radius=18 * scale, fill=sage)
    draw.polygon(
        [box((579, 657, 574, 749))[0:2], box((579, 657, 574, 749))[2:4], box((599, 657, 608, 747))[2:4], box((599, 657, 608, 747))[0:2]],
        fill=trouser,
    )
    draw.line(box((607, 590, 663, 555)), fill=sage, width=16 * scale, joint="curve")
    draw.line(box((663, 555, 682, 590)), fill=sage_dark, width=13 * scale, joint="curve")
    draw.line(box((566, 590, 536, 651)), fill=sage_dark, width=14 * scale, joint="curve")
    draw.ellipse(box((662, 542, 678, 558)), fill=skin)
    draw.polygon(
        [box((659, 593, 710, 574))[0:2], box((659, 593, 710, 574))[2:4], box((718, 653, 682, 620))[2:4], box((718, 653, 682, 620))[0:2]],
        fill=(47, 59, 53, 210),
    )

    # Fine highlights and translucent brush marks keep the inserted objects from looking like flat icons.
    draw.line(box((577, 585, 602, 585)), fill=(167, 180, 150, 65), width=3 * scale)
    draw.line(box((693, 605, 693, 720)), fill=(229, 224, 202, 35), width=3 * scale)
    texture_source = random.Random(2718)
    person_strokes = (
        (565, 585, 607, 592, (157, 176, 143, 38)),
        (566, 605, 600, 596, (45, 68, 54, 52)),
        (571, 626, 608, 620, (163, 178, 148, 34)),
        (580, 655, 586, 722, (219, 219, 196, 28)),
    )
    bin_strokes = (
        (687, 590, 781, 584, (224, 222, 204, 42)),
        (689, 623, 782, 617, (57, 66, 63, 38)),
        (700, 670, 771, 666, (210, 208, 190, 30)),
        (694, 713, 778, 707, (54, 64, 61, 34)),
    )
    for x0, y0, x1, y1, color in person_strokes + bin_strokes:
        draw.line(box((x0, y0, x1, y1)), fill=color, width=texture_source.choice((2, 3, 4)) * scale)
    for _ in range(42):
        x = texture_source.randrange(560, 792)
        y = texture_source.randrange(545, 748)
        length = texture_source.randrange(4, 18)
        color = texture_source.choice(((231, 226, 205, 22), (48, 60, 54, 26), (123, 142, 111, 24)))
        draw.line(box((x, y, x + length, y + texture_source.choice((-2, -1, 0, 1, 2)))), fill=color, width=2 * scale)

    layer = layer.filter(ImageFilter.GaussianBlur(0.75 * scale))
    layer = layer.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    return Image.alpha_composite(scene.convert("RGBA"), layer)


def _add_paint_texture(scene: Image.Image) -> Image.Image:
    rgb = np.asarray(scene.convert("RGB")).astype(np.int16)
    rng = np.random.default_rng(31420)
    grain = rng.normal(0, 2.2, (HEIGHT, WIDTH, 1))
    rgb = np.clip(rgb + grain.astype(np.int16), 0, 255).astype(np.uint8)
    textured = Image.fromarray(rgb, mode="RGB").convert("RGBA")

    strokes = Image.new("RGBA", textured.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(strokes)
    random_source = random.Random(31420)
    for _ in range(180):
        x = random_source.randrange(0, WIDTH)
        y = random_source.randrange(0, HEIGHT)
        length = random_source.randrange(18, 72)
        alpha = random_source.randrange(3, 10)
        color = (255, 246, 218, alpha) if random_source.random() > 0.45 else (49, 78, 72, alpha)
        draw.line((x, y, x + length, y + random_source.choice((-2, -1, 0, 1, 2))), fill=color, width=2)
    return Image.alpha_composite(textured, strokes).convert("RGB")


def main() -> None:
    if not SOURCE_PATH.is_file():
        raise FileNotFoundError(SOURCE_PATH)
    scene = _fit_scene(Image.open(SOURCE_PATH))
    scene = _add_clouds(scene)
    scene = _add_people_and_bin(scene)
    scene = _add_paint_texture(scene)
    scene.save(OUTPUT_PATH, optimize=True)
    print(f"Wrote {OUTPUT_PATH} ({WIDTH}x{HEIGHT})")


if __name__ == "__main__":
    main()
