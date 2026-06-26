"""
generate_dummy_marksheet.py
===========================

Creates a FAKE, clearly-marked dummy marksheet image so you can test the
analyzer without using any real student document. This protects privacy:
we never need a real marksheet to demo the pipeline.

Run it (with the venv active) from the project root:

    python sample_data/generate_dummy_marksheet.py

It writes:
    sample_data/dummy_marksheet.png

Then analyze it with:
    python backend/analyze.py sample_data/dummy_marksheet.png

The text is intentionally generic and includes a "SPECIMEN / NOT A REAL
DOCUMENT" banner so it can never be mistaken for a genuine marksheet.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


OUTPUT_PATH = Path(__file__).resolve().parent / "dummy_marksheet.png"


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    """Try a common Windows font; fall back to PIL's built-in font."""
    for name in ("arial.ttf", "DejaVuSans.ttf", "calibri.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def main() -> None:
    width, height = 1240, 1754  # roughly A4 at 150 DPI
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)

    title_font = _load_font(46)
    head_font = _load_font(30)
    body_font = _load_font(26)
    small_font = _load_font(20)

    # A clear "this is fake" banner so it cannot be mistaken for a real doc.
    draw.rectangle([0, 0, width, 60], fill=(220, 30, 30))
    draw.text((30, 14), "SPECIMEN - DUMMY DOCUMENT - NOT A REAL MARKSHEET",
              fill="white", font=small_font)

    y = 110
    draw.text((width // 2 - 360, y), "CENTRAL BOARD OF SECONDARY EDUCATION",
              fill="black", font=head_font)
    y += 50
    draw.text((width // 2 - 90, y), "CBSE", fill="black", font=title_font)
    y += 80
    draw.text((width // 2 - 270, y), "STATEMENT OF MARKS - CLASS XII (SPECIMEN)",
              fill="black", font=body_font)

    y += 90
    rows = [
        "Candidate Name : SAMPLE STUDENT",
        "Roll No        : 1234567",
        "School         : SPECIMEN PUBLIC SCHOOL",
        "Examination    : SENIOR SCHOOL CERTIFICATE EXAMINATION",
        "",
        "Subject              Max Marks    Marks Obtained",
        "English                100             88",
        "Mathematics            100             92",
        "Physics                100             85",
        "Chemistry              100             90",
        "Computer Science       100             95",
        "",
        "Total Marks    : 450/500",
        "Percentage     : 90.0 %",
        "Result         : PASS",
    ]
    for line in rows:
        draw.text((90, y), line, fill="black", font=body_font)
        y += 44

    draw.text((90, height - 80),
              "This specimen is generated for software testing only.",
              fill=(90, 90, 90), font=small_font)

    image.save(OUTPUT_PATH)
    print(f"Dummy marksheet written to: {OUTPUT_PATH}")
    print("Now run:  python backend/analyze.py sample_data/dummy_marksheet.png")


if __name__ == "__main__":
    main()
