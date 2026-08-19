"""icon.svg を icon.ico に変換するスクリプト（ビルド用）"""
import sys
import io
import cairosvg
from PIL import Image

sizes = [16, 32, 48, 64, 128, 256]
imgs = []
for s in sizes:
    png = cairosvg.svg2png(url="img/icon.svg", output_width=s, output_height=s)
    imgs.append(Image.open(io.BytesIO(png)).convert("RGBA"))

imgs[0].save(
    "icon.ico",
    format="ICO",
    sizes=[(i.width, i.height) for i in imgs],
    append_images=imgs[1:],
)
print("icon.ico generated")
