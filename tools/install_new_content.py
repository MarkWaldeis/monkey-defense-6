"""Install water/glue/boomerang towers, portraits, and MOAB-class sprites."""
from pathlib import Path
from collections import deque
from PIL import Image

SESS = Path(
    r"C:\Users\Mark Waldeis\.grok\sessions"
    r"\C%3A%5CUsers%5CMark%20Waldeis\019fb322-46f2-7560-9a64-72c0bc0438da\images"
)
ASSETS = Path(r"C:\Users\Mark Waldeis\Desktop\Game Prompt\public\assets")
TOWERS = ASSETS / "towers"
SHARED = TOWERS / "_shared"
UI = ASSETS / "ui" / "btd"
BLOONS = ASSETS / "bloons"
PROJ = ASSETS / "effects" / "projectiles"


def flood_bg(img, thr_d=22, thr_l=225):
    img = img.convert("RGBA")
    w, h = img.size
    px = img.load()
    vis = bytearray(w * h)
    q = deque()

    def is_bg(r, g, b):
        if r <= thr_d and g <= thr_d and b <= thr_d:
            return True
        if r >= thr_l and g >= thr_l and b >= thr_l:
            return True
        if abs(r - g) < 10 and abs(g - b) < 10 and r > 200:
            return True
        return False

    def seed(x, y):
        r, g, b, a = px[x, y]
        if a and is_bg(r, g, b) and not vis[y * w + x]:
            vis[y * w + x] = 1
            q.append((x, y))

    for x in range(w):
        seed(x, 0)
        seed(x, h - 1)
    for y in range(h):
        seed(0, y)
        seed(w - 1, y)
    while q:
        x, y = q.popleft()
        px[x, y] = (0, 0, 0, 0)
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if 0 <= nx < w and 0 <= ny < h and not vis[ny * w + nx]:
                r, g, b, a = px[nx, ny]
                if a and is_bg(r, g, b):
                    vis[ny * w + nx] = 1
                    q.append((nx, ny))
    return img


def trim(img, size=96, pad=0.05):
    bbox = img.getbbox()
    if not bbox:
        return Image.new("RGBA", (size, size), (0, 0, 0, 0))
    c = img.crop(bbox)
    side = max(c.size)
    p = int(side * pad)
    canvas = Image.new("RGBA", (side + 2 * p, side + 2 * p), (0, 0, 0, 0))
    canvas.paste(c, ((canvas.size[0] - c.size[0]) // 2, (canvas.size[1] - c.size[1]) // 2), c)
    return canvas.resize((size, size), Image.Resampling.LANCZOS)


def save_tower(name, idle_src, pad_name):
    out = TOWERS / name
    out.mkdir(parents=True, exist_ok=True)
    body = trim(flood_bg(Image.open(SESS / idle_src)), 96, 0.04)
    body.save(out / "idle.png")
    body.transpose(Image.Transpose.FLIP_LEFT_RIGHT).save(out / "idle_1.png")
    body.save(out / "attack_0.png")
    body.save(out / "attack_1.png")
    pad = SHARED / f"pad_{pad_name}.png"
    if pad.exists():
        Image.open(pad).save(out / "pad.png")
    print("tower", name)


def save_portrait(src, dest_name):
    # keep black bg for UI portraits like dart
    im = Image.open(SESS / src).convert("RGBA")
    im = flood_bg(im, 18, 240)
    body = trim(im, 256, 0.08)
    bg = Image.new("RGB", (256, 256), (0, 0, 0))
    bg.paste(body, (0, 0), body)
    path = UI / dest_name
    bg.save(path, "PNG")
    print("portrait", dest_name)


def save_bloon(src, dest_name, size=128):
    im = trim(flood_bg(Image.open(SESS / src), 20, 230), size, 0.04)
    im.save(BLOONS / dest_name)
    print("bloon", dest_name)


def make_proj_water():
    im = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    from PIL import ImageDraw
    d = ImageDraw.Draw(im)
    d.ellipse((4, 8, 28, 24), fill=(66, 165, 245, 230))
    d.ellipse((8, 10, 16, 16), fill=(187, 222, 251, 200))
    im.save(PROJ / "water.png")
    print("proj water")


def make_proj_glue():
    im = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    from PIL import ImageDraw
    d = ImageDraw.Draw(im)
    d.ellipse((6, 6, 26, 26), fill=(124, 179, 66, 230))
    d.ellipse((10, 10, 18, 18), fill=(174, 213, 129, 200))
    im.save(PROJ / "glue.png")
    print("proj glue")


def make_proj_boomerang():
    im = Image.new("RGBA", (40, 40), (0, 0, 0, 0))
    from PIL import ImageDraw
    d = ImageDraw.Draw(im)
    d.arc((4, 4, 36, 36), 200, 340, fill=(161, 98, 43, 255), width=6)
    d.arc((8, 8, 32, 32), 200, 340, fill=(198, 140, 83, 255), width=4)
    im.save(PROJ / "boomerang.png")
    print("proj boomerang")


# Towers
save_tower("water_monkey", "20.jpg", "ice")
save_tower("glue_gunner", "22.jpg", "grass")
save_tower("boomerang_monkey", "18.jpg", "wood")

# Portraits
save_portrait("24.jpg", "tower-water-monkey.png")
save_portrait("25.jpg", "tower-glue-gunner.png")
save_portrait("29.jpg", "tower-boomerang-monkey.png")
save_portrait("28.jpg", "tower-ninja-monkey.png")

# MOAB class
save_bloon("23.jpg", "moab.png", 140)
save_bloon("19.jpg", "bfb.png", 160)
save_bloon("27.jpg", "zomg.png", 180)
save_bloon("21.jpg", "ddt.png", 130)
save_bloon("26.jpg", "bad.png", 200)

make_proj_water()
make_proj_glue()
make_proj_boomerang()
print("DONE")
