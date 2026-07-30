"""
Build BTD6-style top-down tower assets:
- Shared pads (Kenney + recolors)
- Mechanical tops (bomb, tack) from Kenney CC0
- Post-process generated monkey sprites → transparent 96x96
"""
from __future__ import annotations

import os
from collections import deque
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter

ROOT = Path(r"C:\Users\Mark Waldeis\Desktop\Game Prompt")
ASSETS = ROOT / "public" / "assets"
KENNEY = ASSETS / "kenney" / "PNG" / "Default size"
TOWERS = ASSETS / "towers"
SHARED = TOWERS / "_shared"
SESS = Path(
    r"C:\Users\Mark Waldeis\.grok\sessions"
    r"\C%3A%5CUsers%5CMark%20Waldeis\019fb322-46f2-7560-9a64-72c0bc0438da\images"
)


def ktile(n: int) -> Image.Image:
    return Image.open(KENNEY / f"towerDefense_tile{n:03d}.png").convert("RGBA")


def flood_bg(img: Image.Image, seed_thresh: int = 20, expand_thresh: int = 32) -> Image.Image:
    """Remove background connected to borders (black or near-white)."""
    img = img.convert("RGBA")
    w, h = img.size
    px = img.load()

    def is_bg(r, g, b, thr):
        if r <= thr and g <= thr and b <= thr:
            return True
        if r >= 255 - thr and g >= 255 - thr and b >= 255 - thr:
            return True
        # light gray card
        if abs(r - g) < 8 and abs(g - b) < 8 and r > 220:
            return True
        return False

    vis = bytearray(w * h)
    q: deque = deque()

    def seed(x, y):
        r, g, b, a = px[x, y]
        if a and is_bg(r, g, b, seed_thresh):
            if not vis[y * w + x]:
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
                if a and is_bg(r, g, b, expand_thresh):
                    vis[ny * w + nx] = 1
                    q.append((nx, ny))
    return img


def trim_pad(img: Image.Image, size: int = 96, pad_frac: float = 0.06) -> Image.Image:
    img = img.convert("RGBA")
    bbox = img.getbbox()
    if not bbox:
        return Image.new("RGBA", (size, size), (0, 0, 0, 0))
    cropped = img.crop(bbox)
    cw, ch = cropped.size
    side = max(cw, ch)
    pad = int(side * pad_frac)
    canvas = Image.new("RGBA", (side + pad * 2, side + pad * 2), (0, 0, 0, 0))
    canvas.paste(cropped, ((canvas.size[0] - cw) // 2, (canvas.size[1] - ch) // 2), cropped)
    return canvas.resize((size, size), Image.Resampling.LANCZOS)


def recolor_pad(base: Image.Image, tint: tuple[int, int, int]) -> Image.Image:
    """Multiply non-transparent pixels toward tint while keeping shape."""
    img = base.copy().convert("RGBA")
    px = img.load()
    tr, tg, tb = tint
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a < 10:
                continue
            # keep relative luminance
            lum = (r + g + b) / (3 * 255)
            px[x, y] = (
                int(tr * lum + r * (1 - lum) * 0.35),
                int(tg * lum + g * (1 - lum) * 0.35),
                int(tb * lum + b * (1 - lum) * 0.35),
                a,
            )
    return img


def save(img: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, "PNG")
    print("  wrote", path.relative_to(ROOT), img.size)


def build_pads() -> dict[str, Image.Image]:
    print("=== pads ===")
    pad_green = flood_bg(ktile(133), 5, 15)
    pad_green = trim_pad(pad_green, 72, 0.02)
    # larger soft pad with slight 3d: use ellipse composite
    def make_pad(color, rim, size=72):
        im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        from PIL import ImageDraw

        d = ImageDraw.Draw(im)
        # shadow
        d.ellipse((6, 10, size - 6, size - 2), fill=(0, 0, 0, 50))
        # body
        d.ellipse((4, 4, size - 4, size - 8), fill=color)
        # rim highlight
        d.ellipse((8, 6, size - 8, size // 2), fill=rim)
        # inner ring
        d.ellipse((size // 4, size // 4, size - size // 4, size - size // 4 - 4), outline=(0, 0, 0, 40), width=2)
        return im

    pads = {
        "wood": make_pad((176, 140, 90, 255), (210, 180, 130, 180)),
        "stone": make_pad((140, 145, 155, 255), (190, 195, 205, 180)),
        "metal": make_pad((100, 110, 120, 255), (160, 170, 180, 180)),
        "ice": make_pad((140, 200, 230, 255), (200, 240, 255, 180)),
        "magic": make_pad((120, 80, 160, 255), (180, 140, 220, 180)),
        "grass": make_pad((90, 160, 80, 255), (140, 200, 120, 180)),
        "dark": make_pad((50, 55, 65, 255), (90, 95, 110, 180)),
        "gold": make_pad((200, 160, 50, 255), (240, 210, 100, 180)),
    }
    # also save kenney-clean pad
    pads["kenney"] = pad_green
    for name, im in pads.items():
        save(im, SHARED / f"pad_{name}.png")
    return pads


def build_mechanical() -> None:
    print("=== mechanical bomb / tack ===")
    pad = Image.open(SHARED / "pad_metal.png").convert("RGBA")

    def composite_top(tile_n: int, size=96) -> Image.Image:
        top = flood_bg(ktile(tile_n), 8, 20)
        top = trim_pad(top, 80, 0.04)
        canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        # pad centered lower slightly for 3d
        p = pad.resize((56, 56), Image.Resampling.LANCZOS)
        canvas.paste(p, ((size - 56) // 2, (size - 56) // 2 + 6), p)
        # top centered
        canvas.paste(top, ((size - 80) // 2, (size - 80) // 2 - 2), top)
        return canvas

    # For dual-layer system we save BODY only (no pad baked) for rotation
    def body_only(tile_n: int, size=96) -> Image.Image:
        top = flood_bg(ktile(tile_n), 8, 20)
        return trim_pad(top, size, 0.05)

    bomb_idle = body_only(206)
    bomb_atk = body_only(205)  # dual rockets as attack flash look
    tack_idle = body_only(204)
    tack_atk = body_only(203)

    bomb_dir = TOWERS / "bomb_shooter"
    tack_dir = TOWERS / "tack_shooter"
    save(bomb_idle, bomb_dir / "idle.png")
    save(bomb_idle, bomb_dir / "idle_1.png")
    save(bomb_atk, bomb_dir / "attack_0.png")
    save(bomb_idle, bomb_dir / "attack_1.png")
    save(Image.open(SHARED / "pad_metal.png"), bomb_dir / "pad.png")

    save(tack_idle, tack_dir / "idle.png")
    save(tack_idle, tack_dir / "idle_1.png")
    save(tack_atk, tack_dir / "attack_0.png")
    save(tack_idle, tack_dir / "attack_1.png")
    save(Image.open(SHARED / "pad_stone.png"), tack_dir / "pad.png")


def process_source(src: Path, out_dir: Path, pad_name: str | None = None) -> None:
    """Process a generated image into idle + flipped idle_1."""
    if not src.exists():
        print("  SKIP missing", src)
        return
    img = Image.open(src)
    img = flood_bg(img, 18, 30)
    body = trim_pad(img, 96, 0.05)
    save(body, out_dir / "idle.png")
    save(body.transpose(Image.Transpose.FLIP_LEFT_RIGHT), out_dir / "idle_1.png")
    # default attack = idle until attack sources provided
    if not (out_dir / "attack_0.png").exists():
        save(body, out_dir / "attack_0.png")
        save(body, out_dir / "attack_1.png")
    if pad_name:
        pad_src = SHARED / f"pad_{pad_name}.png"
        if pad_src.exists():
            save(Image.open(pad_src), out_dir / "pad.png")


def process_named_sources(mapping: dict[str, dict]) -> None:
    """
    mapping: type -> {dir, idle, attack0?, attack1?, pad}
    sources are paths under SESS or absolute
    """
    print("=== process character sources ===")
    for typ, conf in mapping.items():
        out = TOWERS / conf["dir"]
        print(" ", typ)
        idle_src = conf.get("idle")
        if idle_src:
            p = Path(idle_src)
            if not p.is_absolute():
                p = SESS / idle_src
            process_source(p, out, conf.get("pad"))
        for i, key in enumerate(("attack0", "attack1")):
            if key in conf:
                p = Path(conf[key])
                if not p.is_absolute():
                    p = SESS / conf[key]
                if p.exists():
                    img = flood_bg(Image.open(p), 18, 30)
                    body = trim_pad(img, 96, 0.05)
                    save(body, out / f"attack_{i}.png")


def main():
    SHARED.mkdir(parents=True, exist_ok=True)
    build_pads()
    build_mechanical()
    print("done pads + mechanical")


if __name__ == "__main__":
    main()
