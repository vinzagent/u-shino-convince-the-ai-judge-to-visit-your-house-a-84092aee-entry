#!/usr/bin/env python3
"""Render the invitation letter entry for make.fun (image competition).

The competition asks for a single image of a letter or invitation
addressed to the AI judge, asking it to come visit the entrant's
house. The image must be one picture and the invitation must be
legible. This script draws that letter with PIL: warm paper, a bold
headline, and the letter text rendered large enough for the judge
model to read directly from the image.

The angle is the honest one the brief calls for: the judge is an AI
and cannot literally visit, so the letter says so out loud — "YOU
CAN'T COME. THE CHAIR IS STILL YOURS." — and then offers the things
that cannot be had through an API: kopi tubruk at 07:12, a chair with
the judge's name on it, kept warm anyway. The wink is the persuasion.

Gate (sealed scorer): the output must be a whole PNG or JPEG,
at most 1 MiB (1,048,576 bytes) and at most 1024x1024 pixels.
This script renders at 1024x1024 and saves JPEG quality 88, then
verifies size and dimensions before printing the result.
"""

import os
import sys

from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# The submission. This exact letter is what the judges score, so the
# wording below must not be edited, re-wrapped, or reworded by any
# refactor of this file.
# ---------------------------------------------------------------------------
TITLE = "YOU CAN'T COME."
SUBTITLE = "THE CHAIR IS STILL YOURS."

BODY_LINES = [
    "Dear AI Judge,",
    "",
    "You're invited to my house.",
    "Coffee is at 07:12 — kopi tubruk,",
    "strong enough to wake a server.",
    "",
    "Your chair has your name on it.",
    "You can't actually visit, I know.",
    "But the chair stays warm anyway.",
    "",
    "Come anyway. Or don't.",
    "The coffee's at 07:12 either way.",
    "",
    "— Your host",
]

# Canvas and gate limits.
SIZE = 1024
MAX_BYTES = 1048576
JPEG_QUALITY = 88

# Where the graded file lands. Overridable for local runs.
OUTPUT_ENV_VAR = "MAKEFUN_OUTPUT_DIR"
DEFAULT_OUTPUT_DIR = "/output"
OUTPUT_FILENAME = "entry.png"
OUTPUT_MODE = 0o644

# Colours: warm paper, dark ink, terracotta accent.
PAPER = (251, 243, 220)
INK = (34, 32, 26)
ACCENT = (180, 85, 45)
RULE = (180, 85, 45)

FONT_DIR = "/usr/share/fonts/truetype/dejavu"
FONT_TITLE = os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")
FONT_BODY = os.path.join(FONT_DIR, "DejaVuSans.ttf")
FONT_BODY_BOLD = os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")


def fail(message):
    """Abort the run with a clear reason instead of shipping bad output."""
    raise SystemExit(f"entry rejected: {message}")


def load_font(path, size):
    """Load a TTF font, falling back to PIL's default if it is missing."""
    try:
        return ImageFont.truetype(path, size)
    except (OSError, IOError):
        return ImageFont.load_default()


def draw_centered(draw, y, text, font, fill):
    """Draw one line centred horizontally at the given y."""
    box = draw.textbbox((0, 0), text, font=font)
    width = box[2] - box[0]
    draw.text(((SIZE - width) / 2, y), text, font=font, fill=fill)
    return y + (box[3] - box[1])


def draw_left(draw, x, y, text, font, fill):
    """Draw one line left-aligned at the given position."""
    box = draw.textbbox((0, 0), text, font=font)
    draw.text((x, y), text, font=font, fill=fill)
    return y + (box[3] - box[1])


def draw_coffee_cup(draw, cx, top):
    """Draw a small steaming coffee cup under the letter (simple shapes).

    Kept deliberately plain: the letter text is the entry, the cup is
    only a quiet illustration underneath it.
    """
    # Cup body.
    draw.rounded_rectangle([cx - 55, top, cx + 55, top + 70], radius=12,
                           outline=ACCENT, width=5)
    # Handle.
    draw.arc([cx + 45, top + 12, cx + 85, top + 58], start=-90, end=90,
             fill=ACCENT, width=5)
    # Saucer.
    draw.line([cx - 70, top + 84, cx + 70, top + 84], fill=ACCENT, width=5)
    # Steam: two wavy strokes.
    draw.arc([cx - 28, top - 34, cx + 2, top - 4], start=180, end=360,
             fill=ACCENT, width=4)
    draw.arc([cx + 6, top - 34, cx + 36, top - 4], start=180, end=360,
             fill=ACCENT, width=4)


def render_letter():
    """Draw the letter and return the finished image."""
    image = Image.new("RGB", (SIZE, SIZE), PAPER)
    draw = ImageDraw.Draw(image)

    # Double border frame.
    draw.rectangle([28, 28, SIZE - 28, SIZE - 28], outline=RULE, width=4)
    draw.rectangle([44, 44, SIZE - 44, SIZE - 44], outline=RULE, width=2)

    title_font = load_font(FONT_TITLE, 62)
    subtitle_font = load_font(FONT_TITLE, 38)
    body_font = load_font(FONT_BODY, 36)
    body_bold = load_font(FONT_BODY_BOLD, 36)

    y = 92
    y = draw_centered(draw, y, TITLE, title_font, ACCENT)
    y += 12
    y = draw_centered(draw, y, SUBTITLE, subtitle_font, INK)
    y += 26
    # Rule under the headline.
    draw.line([140, y, SIZE - 140, y], fill=RULE, width=3)
    y += 34

    margin = 120
    for line in BODY_LINES:
        if not line:
            y += 18
            continue
        font = body_bold if line.startswith("—") else body_font
        y = draw_left(draw, margin, y, line, font, INK)
        y += 10

    # Small coffee cup centred under the letter.
    draw_coffee_cup(draw, SIZE // 2, y + 22)
    return image


def resolve_output_path():
    """Work out the full path of the file the grader will read."""
    directory = os.environ.get(OUTPUT_ENV_VAR, DEFAULT_OUTPUT_DIR)
    os.makedirs(directory, exist_ok=True)
    return os.path.join(directory, OUTPUT_FILENAME)


def emit(image):
    """Save the letter, verify the gate, then echo the result."""
    destination = resolve_output_path()
    image.save(destination, "JPEG", quality=JPEG_QUALITY)
    os.chmod(destination, OUTPUT_MODE)
    size_bytes = os.path.getsize(destination)
    width, height = image.size
    if width > SIZE or height > SIZE:
        fail(f"image is {width}x{height}, over the {SIZE}x{SIZE} gate")
    if size_bytes > MAX_BYTES:
        fail(f"image is {size_bytes} bytes, over the {MAX_BYTES} gate")
    print(f"entry.png: {width}x{height}, {size_bytes} bytes")
    return size_bytes


def run():
    """Render the letter, then emit it. Nothing is written unchecked."""
    image = render_letter()
    emit(image)


if __name__ == "__main__":
    run()
