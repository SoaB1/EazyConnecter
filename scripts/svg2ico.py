"""
icon.svg を icon.ico に変換するスクリプト（ビルド用）

変換方法（優先順）:
  1. Inkscape CLI  -- GitHub Actions Windows ランナーにプリインストール済み
  2. cairosvg      -- Cairo DLL が必要（ローカル環境向け）
  3. 変換スキップ  -- どちらもない場合
"""
import io
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SVG_PATH = "img/icon.svg"
ICO_PATH = "icon.ico"
SIZES    = [16, 32, 48, 64, 128, 256]

INKSCAPE_CANDIDATES = [
    r"C:\Program Files\Inkscape\bin\inkscape.exe",
    r"C:\Program Files (x86)\Inkscape\bin\inkscape.exe",
    "inkscape",   # PATH が通っている場合
]


def svg_to_png_inkscape(svg: str, size: int) -> bytes:
    inkscape = next(
        (p for p in INKSCAPE_CANDIDATES
         if p == "inkscape" or os.path.exists(p)), None)
    if inkscape is None:
        raise FileNotFoundError("Inkscape が見つかりません")

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


def svg_to_png_cairosvg(svg: str, size: int) -> bytes:
    import cairosvg
    return cairosvg.svg2png(url=svg, output_width=size, output_height=size)


def main():
    from PIL import Image

    if not os.path.exists(SVG_PATH):
        print(f"SKIP: {SVG_PATH} が見つかりません")
        sys.exit(0)

    # 変換方法を選択
    converter = None
    method    = ""
    try:
        svg_to_png_inkscape(SVG_PATH, 16)   # 動作確認
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
        print("SKIP: Inkscape も cairosvg も利用できません。icon.ico なしでビルドを続行します。")
        sys.exit(0)

    print(f"変換方法: {method}")

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
    print(f"icon.ico 生成完了 ({ICO_PATH})")


if __name__ == "__main__":
    main()
