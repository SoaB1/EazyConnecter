# -*- coding: utf-8 -*-
"""
Convert img/icon.svg to icon.ico for build process.

Priority:
  1. Inkscape CLI  (pre-installed on GitHub Actions windows-latest)
  2. cairosvg      (requires Cairo DLL, for local environments)
  3. Skip          (if neither is available)
"""
import io
import os
import subprocess
import sys
import tempfile

# Force UTF-8 output to avoid encoding errors in CI environments
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

SVG_PATH = "img/icon.svg"
ICO_PATH = "icon.ico"
SIZES    = [16, 32, 48, 64, 128, 256]

INKSCAPE_CANDIDATES = [
    r"C:\Program Files\Inkscape\bin\inkscape.exe",
    r"C:\Program Files (x86)\Inkscape\bin\inkscape.exe",
    "inkscape",
]


def svg_to_png_inkscape(svg, size):
    inkscape = next(
        (p for p in INKSCAPE_CANDIDATES
         if p == "inkscape" or os.path.exists(p)), None)
    if inkscape is None:
        raise FileNotFoundError("Inkscape not found")

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        subprocess.run(
            [inkscape, "--export-type=png",
             f"--export-filename={tmp_path}",
             f"--export-width={size}",
             f"--export-height={size}",
             svg],
            check=True, capture_output=True)
        with open(tmp_path, "rb") as f:
            return f.read()
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def svg_to_png_cairosvg(svg, size):
    import cairosvg
    return cairosvg.svg2png(url=svg, output_width=size, output_height=size)


def main():
    from PIL import Image

    if not os.path.exists(SVG_PATH):
        print(f"SKIP: {SVG_PATH} not found")
        sys.exit(0)

    converter = None
    method    = ""

    try:
        svg_to_png_inkscape(SVG_PATH, 16)
        converter = svg_to_png_inkscape
        method    = "Inkscape"
    except Exception:
        pass

    if converter is None:
        try:
            svg_to_png_cairosvg(SVG_PATH, 16)
            converter = svg_to_png_cairosvg
            method    = "cairosvg"
        except Exception:
            pass

    if converter is None:
        print("SKIP: Inkscape and cairosvg are both unavailable. Building without icon.")
        sys.exit(0)

    print(f"Method: {method}")
    imgs = []
    for s in SIZES:
        png = converter(SVG_PATH, s)
        imgs.append(Image.open(io.BytesIO(png)).convert("RGBA"))
        print(f"  {s}x{s} OK")

    imgs[0].save(
        ICO_PATH,
        format="ICO",
        sizes=[(i.width, i.height) for i in imgs],
        append_images=imgs[1:],
    )
    print(f"Generated: {ICO_PATH}")


if __name__ == "__main__":
    main()
