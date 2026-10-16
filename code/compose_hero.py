#!/usr/bin/env python3
"""Composite the headline figure onto the generated hero art.
Base art: hero_source/ (AI illustration, brand palette). Text sits on a
gradient scrim over the dark upper-left sky. Plain hyphens only.
Run: python3 code/compose_hero.py
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

PKG = Path(__file__).resolve().parent.parent
SRC = PKG / "hero_source/media-generation-hero-base-sales-keystone-v2-0-ff85fd0c-8952-4604-9920-0ea26d1f86af.webp"
OUT = PKG / "charts/hero.png"

img = Image.open(SRC).convert("RGB")
W, H = img.size
print("base size:", W, H)

scrim = Image.new("L", (1, H))
for y in range(H):
    t = y / (H * 0.46)
    a = max(0, int(165 * (1 - t))) if t < 1 else 0
    scrim.putpixel((0, y), a)
scrim = scrim.resize((W, H))
dark = Image.new("RGB", (W, H), (10, 13, 16))
img = Image.composite(dark, img, scrim.point(lambda v: v))

d = ImageDraw.Draw(img)
AMBER = (245, 168, 0)
PAPER = (242, 239, 233)
DIM = (178, 188, 194)
x = int(W * 0.045)
y = int(H * 0.05)

f_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(H * 0.115))
f_cap = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(H * 0.036))
f_sub = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(H * 0.0255))

d.text((x, y), "$595,000", font=f_big, fill=AMBER)
y += int(H * 0.135)
d.text((x, y), "Denver's median market sale price at its 2022 peak", font=f_cap, fill=PAPER)
y += int(H * 0.052)
d.text((x, y), "105,585 market sales recorded, 2020-2026 (2026 partial) - $450,000 median in 2020, $525,000 in 2025 - nominal dollars",
       font=f_sub, fill=DIM)

img.save(OUT)
print("saved", OUT)
