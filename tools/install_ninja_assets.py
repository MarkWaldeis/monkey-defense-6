from PIL import Image
import os

sess = r"C:\Users\Mark Waldeis\.grok\sessions\C%3A%5CUsers%5CMark%20Waldeis\019fb322-46f2-7560-9a64-72c0bc0438da\images"
base = r"C:\Users\Mark Waldeis\Desktop\Game Prompt\public\assets"
tower_dir = os.path.join(base, "towers", "ninja_monkey")
os.makedirs(tower_dir, exist_ok=True)


def black_to_alpha(img, thresh=28):
    img = img.convert("RGBA")
    px = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if r < thresh and g < thresh and b < thresh:
                px[x, y] = (0, 0, 0, 0)
            elif r < thresh + 18 and g < thresh + 18 and b < thresh + 18:
                mx = max(r, g, b)
                a2 = min(a, int((mx - thresh) / 18 * 255))
                px[x, y] = (r, g, b, a2)
    return img


def trim_and_pad(img, size=256, pad=0.06):
    img = img.convert("RGBA")
    bbox = img.getbbox()
    if not bbox:
        return img.resize((size, size), Image.Resampling.LANCZOS)
    cropped = img.crop(bbox)
    max_side = max(cropped.size)
    pad_px = int(max_side * pad)
    canvas = Image.new("RGBA", (max_side + pad_px * 2, max_side + pad_px * 2), (0, 0, 0, 0))
    ox = (canvas.size[0] - cropped.size[0]) // 2
    oy = (canvas.size[1] - cropped.size[1]) // 2
    canvas.paste(cropped, (ox, oy), cropped)
    return canvas.resize((size, size), Image.Resampling.LANCZOS)


# UI portrait on black (matches other BTD portraits)
portrait = black_to_alpha(Image.open(os.path.join(sess, "3.jpg")), thresh=22)
portrait = trim_and_pad(portrait, 256, 0.08)
black_bg = Image.new("RGBA", (256, 256), (0, 0, 0, 255))
black_bg.paste(portrait, (0, 0), portrait)
ui_path = os.path.join(base, "ui", "btd", "tower-ninja-monkey.png")
black_bg.convert("RGB").save(ui_path, "PNG")
portrait.save(os.path.join(tower_dir, "portrait.png"), "PNG")

# In-game idle
idle = black_to_alpha(Image.open(os.path.join(sess, "2.jpg")), thresh=25)
px = idle.load()
w, h = idle.size
for y in range(h):
    for x in range(w):
        r, g, b, a = px[x, y]
        if a > 0 and r > 245 and g > 245 and b > 245:
            if x < w * 0.12 or x > w * 0.88 or y < h * 0.12 or y > h * 0.88:
                px[x, y] = (0, 0, 0, 0)
idle = trim_and_pad(idle, 128, 0.04)
idle.save(os.path.join(tower_dir, "idle.png"), "PNG")
idle.transpose(Image.Transpose.FLIP_LEFT_RIGHT).save(os.path.join(tower_dir, "idle_1.png"), "PNG")

# Shuriken projectile
shu = black_to_alpha(Image.open(os.path.join(sess, "1.jpg")), thresh=40)
px = shu.load()
w, h = shu.size
cx, cy = w / 2, h / 2
for y in range(h):
    for x in range(w):
        r, g, b, a = px[x, y]
        if not a:
            continue
        if r < 55 and g < 55 and b < 55:
            px[x, y] = (0, 0, 0, 0)
            continue
        if r < 70 and g < 70 and b < 70 and abs(r - g) < 8 and abs(g - b) < 8:
            d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if d > w * 0.12 and max(r, g, b) - min(r, g, b) < 12:
                px[x, y] = (0, 0, 0, 0)
shu = trim_and_pad(shu, 64, 0.02)
shu_path = os.path.join(base, "effects", "projectiles", "shuriken.png")
shu.save(shu_path, "PNG")

for p in [ui_path, os.path.join(tower_dir, "idle.png"), os.path.join(tower_dir, "idle_1.png"), shu_path]:
    print("OK", p, os.path.getsize(p))
