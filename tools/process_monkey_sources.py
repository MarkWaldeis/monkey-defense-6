from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from build_topdown_towers import flood_bg, trim_pad, save, SHARED, TOWERS, SESS
from PIL import Image

mapping = {
    "dart": {"dir": "dart_monkey", "idle": "7.jpg", "atk": ["13.jpg"], "pad": "grass"},
    "sniper": {"dir": "sniper_monkey", "idle": "5.jpg", "atk": ["14.jpg"], "pad": "grass"},
    "ninja": {"dir": "ninja_monkey", "idle": "6.jpg", "atk": ["15.jpg"], "pad": "dark"},
    "ice": {"dir": "ice_monkey", "idle": "8.jpg", "atk": ["12.jpg"], "pad": "ice"},
    "wizard": {"dir": "wizard_monkey", "idle": "11.jpg", "atk": ["16.jpg"], "pad": "magic"},
    "super": {"dir": "super_monkey", "idle": "9.jpg", "atk": ["17.jpg"], "pad": "dark"},
    "farm": {"dir": "banana_farm", "idle": "10.jpg", "atk": [], "pad": "wood"},
}


def clean_white_card(body: Image.Image) -> Image.Image:
    """Remove residual light gray/white cards while keeping eye whites inside body."""
    body = body.copy()
    px = body.load()
    w, h = body.size
    # flood near-white from borders
    from collections import deque

    vis = bytearray(w * h)
    q = deque()

    def is_whiteish(r, g, b):
        return r > 230 and g > 230 and b > 230 and abs(r - g) < 20 and abs(g - b) < 20

    def seed(x, y):
        r, g, b, a = px[x, y]
        if a and is_whiteish(r, g, b) and not vis[y * w + x]:
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
                if a and is_whiteish(r, g, b):
                    vis[ny * w + nx] = 1
                    q.append((nx, ny))
    return body


for typ, conf in mapping.items():
    out = TOWERS / conf["dir"]
    print("==", typ)
    idle = flood_bg(Image.open(SESS / conf["idle"]), 22, 38)
    body = clean_white_card(trim_pad(idle, 96, 0.04))
    save(body, out / "idle.png")
    save(body.transpose(Image.Transpose.FLIP_LEFT_RIGHT), out / "idle_1.png")
    atks = conf["atk"]
    if atks:
        a0 = clean_white_card(trim_pad(flood_bg(Image.open(SESS / atks[0]), 22, 38), 96, 0.04))
        save(a0, out / "attack_0.png")
        save(body, out / "attack_1.png")
    else:
        save(body, out / "attack_0.png")
        save(body, out / "attack_1.png")
    pad_src = SHARED / f"pad_{conf['pad']}.png"
    if pad_src.exists():
        save(Image.open(pad_src), out / "pad.png")

for typ, conf in mapping.items():
    p = TOWERS / conf["dir"] / "idle.png"
    im = Image.open(p)
    corners = [im.getpixel(c) for c in [(0, 0), (95, 0), (0, 95), (95, 95)]]
    print(typ, im.size, "corners", corners)

print("ALL OK")
