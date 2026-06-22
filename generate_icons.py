"""
Run once: python generate_icons.py
Generates all PWA + favicon + nav logo sizes from the source logo.
"""
from PIL import Image
import os

SRC = r"C:\Users\DELL\.claude\projects\c--Users-DELL-Desktop-PU-Connect-1\b616f912-cc03-4d29-a331-fcc3d3f7fa25\tool-results\webfetch-1782126542811-ln4kl6.jpg"
OUT = r"c:\Users\DELL\Desktop\PU-Connect-1\static\icons"

os.makedirs(OUT, exist_ok=True)

src = Image.open(SRC).convert("RGBA")

# ── Crop to the logo content (remove the grey border whitespace) ──────────────
# The logo sits roughly centered with ~10% padding on all sides
w, h = src.size
pad = int(min(w, h) * 0.05)
cropped = src.crop((pad, pad, w - pad, h - pad))

def save(img, name, size):
    resized = img.resize((size, size), Image.LANCZOS)
    resized.save(os.path.join(OUT, name), "PNG", optimize=True)
    print(f"  {name}  ({size}x{size})")

print("Generating standard PWA icons...")
for sz in [16, 32, 48, 72, 96, 128, 144, 152, 180, 192, 256, 384, 512]:
    save(cropped, f"icon-{sz}.png", sz)

# ── Maskable icons: logo centred on a white circle, ~80% safe zone ───────────
print("\nGenerating maskable icons...")

def make_maskable(img, size):
    canvas = Image.new("RGBA", (size, size), (255, 255, 255, 255))
    logo_size = int(size * 0.75)
    logo = img.resize((logo_size, logo_size), Image.LANCZOS)
    offset = (size - logo_size) // 2
    canvas.paste(logo, (offset, offset), logo)
    return canvas

for sz in [192, 512]:
    m = make_maskable(cropped, sz)
    m.save(os.path.join(OUT, f"icon-maskable-{sz}.png"), "PNG", optimize=True)
    print(f"  icon-maskable-{sz}.png  ({sz}x{sz})")

# ── Apple touch icon (180x180, white bg, no transparency) ─────────────────────
print("\nGenerating Apple touch icon...")
apple = Image.new("RGB", (180, 180), (255, 255, 255))
logo = cropped.resize((160, 160), Image.LANCZOS)
apple.paste(logo, (10, 10), logo)
apple.save(os.path.join(OUT, "apple-touch-icon.png"), "PNG", optimize=True)
print("  apple-touch-icon.png  (180x180)")

# ── favicon.ico (multi-size: 16, 32, 48) ──────────────────────────────────────
print("\nGenerating favicon.ico...")
ico_sizes = [(16, 16), (32, 32), (48, 48)]
ico_imgs = [cropped.resize(s, Image.LANCZOS).convert("RGBA") for s in ico_sizes]
ico_imgs[0].save(
    os.path.join(OUT, "favicon.ico"),
    format="ICO",
    sizes=ico_sizes,
    append_images=ico_imgs[1:],
)
print("  favicon.ico  (16, 32, 48)")

# ── Nav logo (just a copy at a web-friendly size) ─────────────────────────────
print("\nGenerating nav logo...")
save(cropped, "logo.png", 256)

print("\nDone. All icons saved to static/icons/")
