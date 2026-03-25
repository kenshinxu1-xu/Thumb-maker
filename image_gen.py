import aiohttp
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
import textwrap
import os

FONT_BOLD = os.path.join("fonts", "DejaVuSans-Bold.ttf")
FONT_REG = os.path.join("fonts", "DejaVuSans.ttf")

async def download_image(url: str) -> Image.Image:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.read()
    return Image.open(BytesIO(data)).convert("RGBA")

def draw_multiline_text(draw, text, font, color, xy, max_width, line_spacing=4):
    lines = textwrap.wrap(text, width=max_width)
    y = xy[1]
    for line in lines:
        draw.text((xy[0], y), line, font=font, fill=color)
        y += font.getsize(line)[1] + line_spacing

def get_star_rating(rating):
    full = int(rating // 2)
    half = rating % 2 >= 0.5
    stars = "★" * full
    if half:
        stars += "½"
    stars += "☆" * (5 - full - (1 if half else 0))
    return stars
