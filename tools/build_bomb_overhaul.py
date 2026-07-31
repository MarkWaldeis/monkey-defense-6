"""
Bomb Shooter visual overhaul — procedurally drawn BTD6-style sprites with PIL.

Generates (all RGBA, transparent bg):
  public/assets/towers/bomb_shooter/{idle,idle_1,attack_0,attack_1,pad}.png
  public/assets/effects/projectiles/{bomb,rocket,frag}.png
  public/assets/effects/muzzle_flash.png
  public/assets/effects/explosion/explosion_00..07.png
  public/assets/ui/btd/tower-bomb-icon.png

Towers face UP (12 o'clock); projectiles/effects point RIGHT (3 o'clock).
Run:  python tools/build_bomb_overhaul.py
"""
from __future__ import annotations

import math
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(r"C:\Users\Mark Waldeis\Desktop\Game Prompt")
ASSETS = ROOT / "public" / "assets"
TOWER_DIR = ASSETS / "towers" / "bomb_shooter"
PROJ_DIR = ASSETS / "effects" / "projectiles"
FX_DIR = ASSETS / "effects"
EXPL_DIR = FX_DIR / "explosion"
UI_DIR = ASSETS / "ui" / "btd"

OUTLINE = (18, 20, 26)

# ---------------------------------------------------------------- helpers


def canvas(S: int) -> Image.Image:
    return Image.new("RGBA", (S, S), (0, 0, 0, 0))


def over(base: Image.Image, lay: Image.Image) -> Image.Image:
    base.alpha_composite(lay)
    return base


def blur(im: Image.Image, r: float) -> Image.Image:
    return im.filter(ImageFilter.GaussianBlur(r))


def _grad_rgb(t: np.ndarray, stops: list[tuple[float, tuple[int, int, int]]]) -> np.ndarray:
    """Piecewise-linear multi-stop gradient. t in [0,1] -> (...,3) float."""
    ts = np.array([s[0] for s in stops], np.float32)
    cs = np.array([s[1] for s in stops], np.float32)
    idx = np.clip(np.searchsorted(ts, t) - 1, 0, len(stops) - 2)
    t0, t1 = ts[idx], ts[idx + 1]
    c0, c1 = cs[idx], cs[idx + 1]
    u = np.clip((t - t0) / np.maximum(t1 - t0, 1e-6), 0, 1)[..., None]
    return c0 + (c1 - c0) * u


def shaded_disc(S, cx, cy, r, stops, light_dir=(-0.45, -0.89), aa=1.6,
                light_strength=0.75):
    """Directionally lit disc as an RGBA image. stops = [(pos, rgb), ...]."""
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    dx = (xx - cx) / r
    dy = (yy - cy) / r
    d = np.sqrt(dx * dx + dy * dy)
    t = np.clip(0.5 - (dx * light_dir[0] + dy * light_dir[1]) * light_strength, 0, 1)
    rgb = _grad_rgb(t, stops)
    alpha = np.clip((1.0 - d) * r / aa, 0, 1) * 255.0
    return Image.fromarray(np.dstack([rgb, alpha]).astype(np.uint8), "RGBA")


def shade_over_mask(mask: Image.Image, stops, light_dir=(-0.45, -0.89),
                    light_strength=0.75) -> Image.Image:
    """Apply a directional gradient inside an L-mode mask."""
    bbox = mask.getbbox()
    S = mask.size[0]
    if not bbox:
        return canvas(S)
    x0, y0, x1, y1 = bbox
    w, h = max(x1 - x0, 1), max(y1 - y0, 1)
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    nx = (xx - (x0 + w / 2)) / (w / 2)
    ny = (yy - (y0 + h / 2)) / (h / 2)
    t = np.clip(0.5 - (nx * light_dir[0] + ny * light_dir[1]) * light_strength, 0, 1)
    rgb = _grad_rgb(t, stops)
    full = np.zeros((S, S, 4), np.uint8)
    full[y0:y1, x0:x1, :3] = rgb.astype(np.uint8)
    full[:, :, 3] = np.asarray(mask, np.uint8)
    return Image.fromarray(full, "RGBA")


def dilate(mask: Image.Image, px: int) -> Image.Image:
    return mask.filter(ImageFilter.MaxFilter(px * 2 + 1))


def mask_fill(mask: Image.Image, color) -> Image.Image:
    S = mask.size[0]
    im = canvas(S)
    im.paste(Image.new("RGBA", (S, S), color), (0, 0), mask)
    return im


def gloss(base: Image.Image, cx, cy, rx, ry, alpha=90, blur_r=None, rot=0):
    """Soft white specular blob."""
    S = base.size[0]
    lay = canvas(S)
    d = ImageDraw.Draw(lay)
    d.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=(255, 255, 255, alpha))
    if rot:
        lay = lay.rotate(rot, center=(cx, cy), resample=Image.Resampling.BICUBIC)
    lay = blur(lay, blur_r if blur_r is not None else max(rx, ry) * 0.45)
    return over(base, lay)


def spark(base, x, y, r, core=(255, 240, 160), glow_c=(255, 150, 40), rays=4):
    """Lit-fuse spark: glow + bright core + tiny rays."""
    S = base.size[0]
    glow = canvas(S)
    d = ImageDraw.Draw(glow)
    d.ellipse((x - r * 2.4, y - r * 2.4, x + r * 2.4, y + r * 2.4),
              fill=glow_c + (150,))
    over(base, blur(glow, r * 1.1))
    d = ImageDraw.Draw(base)
    for i in range(rays):
        a = i * math.pi / rays + 0.4
        d.line((x - math.cos(a) * r * 2.2, y - math.sin(a) * r * 2.2,
                x + math.cos(a) * r * 2.2, y + math.sin(a) * r * 2.2),
               fill=(255, 210, 90, 255), width=max(2, int(r * 0.55)))
    d.ellipse((x - r, y - r, x + r, y + r), fill=core + (255,))
    return base


def trim_center(img: Image.Image, size: int, margin=0.05) -> Image.Image:
    bbox = img.getbbox()
    if not bbox:
        return canvas(size)
    cropped = img.crop(bbox)
    cw, ch = cropped.size
    side = max(cw, ch)
    pad = int(side * margin / (1 - margin)) + 1
    c = canvas(side + pad * 2)
    c.paste(cropped, ((c.size[0] - cw) // 2, (c.size[1] - ch) // 2), cropped)
    return c.resize((size, size), Image.Resampling.LANCZOS)


def crop_shared(imgs: list[Image.Image], size: int, margin=0.05):
    """Crop all frames to their union bbox so animations don't jitter."""
    union = None
    for im in imgs:
        b = im.getbbox()
        if not b:
            continue
        union = b if union is None else (min(union[0], b[0]), min(union[1], b[1]),
                                         max(union[2], b[2]), max(union[3], b[3]))
    out = []
    for im in imgs:
        cropped = im.crop(union)
        cw, ch = cropped.size
        side = max(cw, ch)
        pad = int(side * margin / (1 - margin)) + 1
        c = canvas(side + pad * 2)
        c.paste(cropped, ((c.size[0] - cw) // 2, (c.size[1] - ch) // 2), cropped)
        out.append(c.resize((size, size), Image.Resampling.LANCZOS))
    return out


def save(img: Image.Image, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, "PNG")
    print("  wrote", path.relative_to(ROOT), img.size)


# palette ----------------------------------------------------------------

GUNMETAL = [(0.0, (40, 45, 56)), (0.5, (88, 97, 112)), (1.0, (138, 148, 163))]
STEEL = [(0.0, (28, 32, 40)), (0.5, (60, 66, 78)), (1.0, (104, 112, 126))]
BRASS = [(0.0, (140, 92, 22)), (0.5, (219, 168, 62)), (1.0, (255, 228, 140))]
BOMB_BLACK = [(0.0, (8, 9, 13)), (0.55, (30, 33, 42)), (1.0, (78, 86, 102))]
RED = (214, 48, 40)
RED_DARK = (132, 22, 18)


# ---------------------------------------------------------------- cannon


def draw_cannon(S: int, variant: str = "idle", ow=None) -> Image.Image:
    """Chunky top-down bomb cannon facing UP. variant: idle|idle1|recoil|recover."""
    im = canvas(S)
    ow = ow or max(2, round(S * 0.036))          # outline width
    cx = S * 0.5
    tc_y = S * 0.56                              # turret centre
    tr = S * 0.295                               # turret radius

    # geometry per variant
    barrel_top = {"idle": S * 0.105, "idle1": S * 0.105,
                  "recoil": S * 0.27, "recover": S * 0.05}[variant]
    bw = S * 0.25                                # barrel width
    recoil = variant == "recoil"

    # -- ground shadow
    sh = canvas(S)
    d = ImageDraw.Draw(sh)
    d.ellipse((cx - tr * 1.05, tc_y - tr * 0.9, cx + tr * 1.05, tc_y + tr * 1.05),
              fill=(0, 0, 0, 70))
    over(im, blur(sh, S * 0.02))

    # -- turret base (drawn first; the barrel sits on top of it)
    over(im, mask_fill(dilate(_circle_mask(S, cx, tc_y, tr), ow), OUTLINE + (255,)))
    over(im, shaded_disc(S, cx, tc_y, tr, GUNMETAL))
    # inner mounting ring
    d = ImageDraw.Draw(im)
    d.ellipse((cx - tr * 0.66, tc_y - tr * 0.66, cx + tr * 0.66, tc_y + tr * 0.66),
              outline=(24, 27, 34, 255), width=max(2, int(S * 0.016)))
    d.ellipse((cx - tr * 0.60, tc_y - tr * 0.60, cx + tr * 0.60, tc_y + tr * 0.60),
              outline=(110, 118, 132, 160), width=max(1, int(S * 0.008)))
    # 8 rivets
    for i in range(8):
        a = math.radians(i * 45 + 22.5)
        rx = cx + math.cos(a) * tr * 0.83
        ry = tc_y + math.sin(a) * tr * 0.83
        rr = S * 0.021
        d.ellipse((rx - rr, ry - rr, rx + rr, ry + rr), fill=OUTLINE + (255,))
        d.ellipse((rx - rr * 0.72, ry - rr * 0.72, rx + rr * 0.72, ry + rr * 0.72),
                  fill=(88, 96, 110, 255))
        d.ellipse((rx - rr * 0.5, ry - rr * 0.62, rx - rr * 0.05, ry - rr * 0.18),
                  fill=(170, 180, 196, 230))
    # turret gloss top-left + bottom-right contact shadow
    im = gloss(im, cx - tr * 0.35, tc_y - tr * 0.42, tr * 0.5, tr * 0.28,
               alpha=46, rot=25)
    sh2 = canvas(S)
    d = ImageDraw.Draw(sh2)
    d.arc((cx - tr * 0.9, tc_y - tr * 0.9, cx + tr * 0.9, tc_y + tr * 0.9),
          start=20, end=140, fill=(0, 0, 0, 90), width=int(S * 0.03))
    over(im, blur(sh2, S * 0.012))

    # -- barrel (on top of the turret, muzzle pointing up)
    bb = tc_y + S * 0.06                         # breech end buried in turret
    bm = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(bm)
    rad = bw * 0.32
    d.rounded_rectangle((cx - bw / 2, barrel_top, cx + bw / 2, bb),
                        radius=rad, fill=255)
    # outline = dilated mask
    over(im, mask_fill(dilate(bm, ow), OUTLINE + (255,)))
    over(im, shade_over_mask(bm, STEEL, light_dir=(-0.92, -0.39),
                             light_strength=0.85))
    # barrel centre ridge highlight
    hl = canvas(S)
    d = ImageDraw.Draw(hl)
    d.rounded_rectangle((cx - bw * 0.28, barrel_top + bw * 0.3,
                         cx - bw * 0.02, bb - bw * 0.3),
                        radius=bw * 0.1, fill=(255, 255, 255, 60))
    hl.putalpha(Image.composite(hl.getchannel("A"), Image.new("L", (S, S), 0), bm))
    over(im, blur(hl, S * 0.004))

    # -- red hazard ring near muzzle
    hz0 = barrel_top + S * 0.075
    hz1 = barrel_top + S * 0.145
    d = ImageDraw.Draw(im)
    d.rectangle((cx - bw / 2 - ow * 0.4, hz0, cx + bw / 2 + ow * 0.4, hz1),
                fill=RED + (255,))
    # dark diagonal stripes on the ring
    stripe = Image.new("L", (S, S), 0)
    ds = ImageDraw.Draw(stripe)
    for i in range(-1, 5):
        sx = cx - bw / 2 + i * bw * 0.34
        ds.polygon([(sx, hz1), (sx + bw * 0.16, hz1),
                    (sx + bw * 0.34, hz0), (sx + bw * 0.18, hz0)], fill=255)
    ring_m = Image.new("L", (S, S), 0)
    dr = ImageDraw.Draw(ring_m)
    dr.rectangle((cx - bw / 2 - ow * 0.4, hz0, cx + bw / 2 + ow * 0.4, hz1), fill=255)
    over(im, mask_fill(Image.composite(stripe, Image.new("L", (S, S), 0), ring_m),
                       RED_DARK + (255,)))
    d.rectangle((cx - bw / 2 - ow * 0.4, hz0, cx + bw / 2 + ow * 0.4, hz1),
                outline=OUTLINE + (255,), width=max(2, ow // 2))

    # -- brass reinforcing band
    by0 = barrel_top + S * 0.21
    by1 = by0 + S * 0.068
    bwm = bw * 0.62
    bm2 = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(bm2)
    d.rounded_rectangle((cx - bwm, by0, cx + bwm, by1), radius=(by1 - by0) * 0.3,
                        fill=255)
    over(im, mask_fill(dilate(bm2, max(2, ow * 2 // 3)), OUTLINE + (255,)))
    over(im, shade_over_mask(bm2, BRASS, light_dir=(-0.8, -0.6)))
    # band rivets
    d = ImageDraw.Draw(im)
    for sgn in (-1, 1):
        rx = cx + sgn * bwm * 0.62
        ry = (by0 + by1) / 2
        rr = (by1 - by0) * 0.16
        d.ellipse((rx - rr, ry - rr, rx + rr, ry + rr), fill=(110, 70, 15, 255))
        d.ellipse((rx - rr * 0.6, ry - rr * 0.7, rx, ry - rr * 0.1),
                  fill=(255, 230, 150, 220))

    # -- muzzle opening (dark ellipse at top end)
    mz_y = barrel_top + S * 0.038
    mz_w = bw * 0.86
    mz_h = S * 0.062
    d.ellipse((cx - mz_w / 2 - ow * 0.5, mz_y - mz_h / 2 - ow * 0.5,
               cx + mz_w / 2 + ow * 0.5, mz_y + mz_h / 2 + ow * 0.5),
              fill=OUTLINE + (255,))
    bore = canvas(S)
    dbo = ImageDraw.Draw(bore)
    dbo.ellipse((cx - mz_w / 2, mz_y - mz_h / 2, cx + mz_w / 2, mz_y + mz_h / 2),
                fill=(10, 11, 16, 255))
    over(im, bore)
    d.ellipse((cx - mz_w / 2 + ow * 0.35, mz_y - mz_h / 2 + ow * 0.35,
               cx + mz_w / 2 - ow * 0.35, mz_y + mz_h * 0.05),
              fill=(38, 42, 52, 255))  # inner back wall of the bore
    d.arc((cx - mz_w / 2, mz_y - mz_h / 2, cx + mz_w / 2, mz_y + mz_h / 2),
          start=15, end=165, fill=(120, 128, 142, 255), width=max(2, ow // 2))

    if recoil:
        # leftover orange glow at muzzle
        gl = canvas(S)
        dg = ImageDraw.Draw(gl)
        dg.ellipse((cx - mz_w, mz_y - mz_h * 1.4, cx + mz_w, mz_y + mz_h * 1.2),
                   fill=(255, 130, 30, 120))
        over(im, blur(gl, S * 0.02))

    # -- breech collar where the barrel enters the turret
    cm = Image.new("L", (S, S), 0)
    dc = ImageDraw.Draw(cm)
    dc.rounded_rectangle((cx - bw * 0.66, bb - S * 0.055, cx + bw * 0.66, bb),
                        radius=S * 0.02, fill=255)
    over(im, mask_fill(dilate(cm, max(2, ow * 2 // 3)), OUTLINE + (255,)))
    over(im, shade_over_mask(cm, STEEL, light_dir=(-0.92, -0.39)))

    # -- breech bomb (ammo) nestled at bottom of turret
    bx, by = cx + (S * 0.01 if variant != "idle1" else -S * 0.015), S * 0.815
    br = S * 0.108
    over(im, mask_fill(dilate(_circle_mask(S, bx, by, br), max(2, ow * 3 // 4)),
                       OUTLINE + (255,)))
    over(im, shaded_disc(S, bx, by, br, BOMB_BLACK, light_strength=0.9))
    im = gloss(im, bx - br * 0.34, by - br * 0.4, br * 0.34, br * 0.2,
               alpha=150, rot=30)
    # fuse: brown cord curving up-left out of the bomb
    fx0, fy0 = bx - br * 0.25, by - br * 0.8
    if variant == "idle1":
        fx1, fy1 = bx - br * 1.25, by - br * 1.85
        mx, my = bx - br * 0.95, by - br * 1.15
    else:
        fx1, fy1 = bx - br * 0.95, by - br * 1.7
        mx, my = bx - br * 0.75, by - br * 1.05
    d = ImageDraw.Draw(im)
    for wd, col in ((int(S * 0.022), OUTLINE + (255,)),
                    (int(S * 0.013), (122, 82, 40, 255))):
        d.line((fx0, fy0, mx, my, fx1, fy1), fill=col, width=max(2, wd),
               joint="curve")
    im = spark(im, fx1, fy1, S * 0.016)

    if recoil:
        # smoke wisps drifting from the muzzle
        rnd = random.Random(7)
        sm = canvas(S)
        dsm = ImageDraw.Draw(sm)
        for i in range(5):
            wx = cx + rnd.uniform(-S * 0.10, S * 0.10)
            wy = mz_y - S * 0.02 - i * S * 0.04
            wr = S * (0.045 + i * 0.016)
            g = rnd.randint(155, 195)
            dsm.ellipse((wx - wr, wy - wr, wx + wr, wy + wr),
                        fill=(g, g, g, 160 - i * 14))
        over(im, blur(sm, S * 0.016))
    return im


def _circle_mask(S, cx, cy, r) -> Image.Image:
    m = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(m)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=255)
    return m


# ---------------------------------------------------------------- pad


def draw_pad(S: int) -> Image.Image:
    """Octagonal heavy platform, top-down."""
    im = canvas(S)
    ow = max(2, round(S * 0.04))
    cx = cy = S / 2
    R = S * 0.44

    sh = canvas(S)
    d = ImageDraw.Draw(sh)
    d.ellipse((cx - R, cy - R * 0.86, cx + R, cy + R), fill=(0, 0, 0, 70))
    over(im, blur(sh, S * 0.025))

    def oct_pts(r, rot=22.5):
        return [(cx + math.cos(math.radians(rot + i * 45)) * r,
                 cy + math.sin(math.radians(rot + i * 45)) * r) for i in range(8)]

    om = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(om)
    d.polygon(oct_pts(R), fill=255)
    over(im, mask_fill(dilate(om, ow), OUTLINE + (255,)))
    over(im, shade_over_mask(om, GUNMETAL, light_strength=0.7))

    # hazard-stripe rim accents (8 alternating segments hugging the rim)
    d = ImageDraw.Draw(im)
    for k in range(8):
        a = math.radians(k * 45 + 22.5)
        seg = Image.new("L", (S, S), 0)
        ds = ImageDraw.Draw(seg)
        w = math.radians(13)
        p = [(cx + math.cos(a - w) * R * 0.97, cy + math.sin(a - w) * R * 0.97),
             (cx + math.cos(a + w) * R * 0.97, cy + math.sin(a + w) * R * 0.97),
             (cx + math.cos(a + w) * R * 0.83, cy + math.sin(a + w) * R * 0.83),
             (cx + math.cos(a - w) * R * 0.83, cy + math.sin(a - w) * R * 0.83)]
        ds.polygon(p, fill=255)
        if k % 2 == 0:
            over(im, shade_over_mask(seg, BRASS, light_strength=0.6))
        else:
            over(im, mask_fill(seg, (26, 28, 34, 255)))
        d.line([p[0], p[1], p[2], p[3], p[0]], fill=OUTLINE + (255,),
               width=max(1, ow // 2), joint="curve")

    # inner mounting ring
    d.ellipse((cx - R * 0.55, cy - R * 0.55, cx + R * 0.55, cy + R * 0.55),
              outline=(22, 25, 32, 255), width=max(2, int(S * 0.022)))
    d.ellipse((cx - R * 0.49, cy - R * 0.49, cx + R * 0.49, cy + R * 0.49),
              outline=(105, 113, 127, 170), width=max(1, int(S * 0.01)))

    # 8 rivets
    for i in range(8):
        a = math.radians(i * 45)
        rx = cx + math.cos(a) * R * 0.68
        ry = cy + math.sin(a) * R * 0.68
        rr = S * 0.028
        d.ellipse((rx - rr, ry - rr, rx + rr, ry + rr), fill=OUTLINE + (255,))
        d.ellipse((rx - rr * 0.72, ry - rr * 0.72, rx + rr * 0.72, ry + rr * 0.72),
                  fill=(92, 100, 114, 255))
        d.ellipse((rx - rr * 0.5, ry - rr * 0.62, rx - rr * 0.05, ry - rr * 0.18),
                  fill=(175, 185, 200, 230))
    im = gloss(im, cx - R * 0.3, cy - R * 0.38, R * 0.5, R * 0.24, alpha=34, rot=25)
    return im


# ---------------------------------------------------------------- projectiles


def draw_bomb_proj(S: int) -> Image.Image:
    """Glossy cannonball pointing right (fuse tail trails left)."""
    im = canvas(S)
    ow = max(2, round(S * 0.045))
    cx, cy, r = S * 0.58, S * 0.52, S * 0.30

    # fuse tail first (behind ball): brown cord to the left
    fx, fy = S * 0.14, S * 0.40
    mx, my = S * 0.30, S * 0.34
    jx, jy = cx - r * 0.8, cy - r * 0.45
    d = ImageDraw.Draw(im)
    for wd, col in ((int(S * 0.075), OUTLINE + (255,)),
                    (int(S * 0.045), (122, 82, 40, 255))):
        d.line((fx, fy, mx, my, jx, jy), fill=col, width=max(2, wd), joint="curve")

    over(im, mask_fill(dilate(_circle_mask(S, cx, cy, r), ow), OUTLINE + (255,)))
    over(im, shaded_disc(S, cx, cy, r, BOMB_BLACK, light_strength=0.95))
    im = gloss(im, cx - r * 0.33, cy - r * 0.38, r * 0.34, r * 0.2, alpha=200, rot=35)
    im = gloss(im, cx - r * 0.05, cy - r * 0.62, r * 0.16, r * 0.09, alpha=120)
    # faint rim light bottom-right
    rim = canvas(S)
    dr = ImageDraw.Draw(rim)
    dr.arc((cx - r * 0.85, cy - r * 0.85, cx + r * 0.85, cy + r * 0.85),
           start=30, end=120, fill=(120, 140, 170, 110), width=int(S * 0.02))
    over(im, blur(rim, S * 0.008))

    im = spark(im, fx, fy, S * 0.045)
    # spark particles
    rnd = random.Random(3)
    d = ImageDraw.Draw(im)
    for _ in range(6):
        a = rnd.uniform(0, math.pi * 2)
        dist = rnd.uniform(S * 0.08, S * 0.16)
        px, py = fx + math.cos(a) * dist, fy + math.sin(a) * dist
        pr = rnd.uniform(S * 0.008, S * 0.018)
        d.ellipse((px - pr, py - pr, px + pr, py + pr),
                  fill=(255, rnd.randint(160, 220), 60, 255))
    return im


def draw_rocket(S: int) -> Image.Image:
    """Sleek missile pointing RIGHT with exhaust trailing left."""
    im = canvas(S)
    ow = max(2, round(S * 0.04))
    cy = S * 0.5
    x0, x1 = S * 0.28, S * 0.68          # body span
    bh = S * 0.30                         # body height

    # -- exhaust flame (layered, trailing left)
    flame = [((S * 0.03, S * 0.115), (255, 120, 20, 220)),
             ((S * 0.10, S * 0.075), (255, 190, 50, 235)),
             ((S * 0.19, S * 0.038), (255, 246, 200, 255))]
    for (fx, fh), col in flame:
        lay = canvas(S)
        d = ImageDraw.Draw(lay)
        tip = fx
        base = x0 + S * 0.02
        d.polygon([(tip, cy),
                   (base - S * 0.03, cy - fh), (base, cy - fh * 0.8),
                   (base, cy + fh * 0.8), (base - S * 0.03, cy + fh)],
                  fill=col)
        over(im, blur(lay, S * 0.008))
    # nozzle
    d = ImageDraw.Draw(im)
    d.polygon([(x0 - S * 0.03, cy - bh * 0.30), (x0 + S * 0.02, cy - bh * 0.42),
               (x0 + S * 0.02, cy + bh * 0.42), (x0 - S * 0.03, cy + bh * 0.30)],
              fill=(60, 64, 74, 255), outline=OUTLINE + (255,))

    # -- rear fins (red, top & bottom)
    for sgn in (-1, 1):
        fin = [(x0 + S * 0.02, cy + sgn * bh * 0.30),
               (x0 + S * 0.14, cy + sgn * bh * 0.34),
               (x0 + S * 0.20, cy + sgn * bh * 0.30),
               (x0 + S * 0.06, cy + sgn * bh * 0.92)]
        d.polygon(fin, fill=RED + (255,), outline=OUTLINE + (255,))
        # fin highlight
        d.line((x0 + S * 0.07, cy + sgn * bh * 0.45,
                x0 + S * 0.065, cy + sgn * bh * 0.78),
               fill=(255, 140, 120, 220), width=max(2, ow // 2))

    # -- body capsule
    bm = Image.new("L", (S, S), 0)
    db = ImageDraw.Draw(bm)
    db.rounded_rectangle((x0, cy - bh / 2, x1, cy + bh / 2), radius=bh / 2, fill=255)
    over(im, mask_fill(dilate(bm, ow), OUTLINE + (255,)))
    over(im, shade_over_mask(
        bm, [(0.0, (122, 128, 140)), (0.45, (196, 203, 214)), (1.0, (252, 253, 255))],
        light_dir=(-0.3, -0.95), light_strength=0.9))
    # panel lines + rivets
    d = ImageDraw.Draw(im)
    for fx in (0.42, 0.55):
        px = S * fx
        d.line((px, cy - bh * 0.38, px, cy + bh * 0.38),
               fill=(110, 116, 128, 255), width=max(2, ow // 2))
        d.line((px + ow * 0.5, cy - bh * 0.38, px + ow * 0.5, cy + bh * 0.38),
               fill=(255, 255, 255, 90), width=max(1, ow // 3))
    # top sheen
    im = gloss(im, (x0 + x1) / 2, cy - bh * 0.28, (x1 - x0) * 0.42, bh * 0.14,
               alpha=110)

    # -- nose cone (red)
    nx1 = S * 0.90
    nm = Image.new("L", (S, S), 0)
    dn = ImageDraw.Draw(nm)
    dn.polygon([(x1 - S * 0.01, cy - bh / 2), (nx1, cy),
                (x1 - S * 0.01, cy + bh / 2)], fill=255)
    dn.ellipse((x1 - S * 0.05, cy - bh / 2, x1 + S * 0.03, cy + bh / 2), fill=255)
    over(im, mask_fill(dilate(nm, ow), OUTLINE + (255,)))
    over(im, shade_over_mask(
        nm, [(0.0, (120, 16, 14)), (0.5, (214, 48, 40)), (1.0, (255, 120, 100))],
        light_dir=(-0.3, -0.95), light_strength=0.85))
    im = gloss(im, (x1 + nx1) / 2 - S * 0.02, cy - bh * 0.24, S * 0.08, bh * 0.12,
               alpha=140)
    return im


def draw_frag(S: int) -> Image.Image:
    """Jagged orange-hot shrapnel shard (orientation-agnostic)."""
    im = canvas(S)
    cx = cy = S / 2
    rnd = random.Random(11)
    n = 9
    pts = []
    for i in range(n):
        a = i * 2 * math.pi / n + rnd.uniform(-0.2, 0.2)
        r = S * (0.20 if i % 2 else rnd.uniform(0.34, 0.44))
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    # hot glow behind
    gl = canvas(S)
    dg = ImageDraw.Draw(gl)
    dg.polygon(pts, fill=(255, 120, 20, 170))
    over(im, blur(gl, S * 0.06))
    # body
    d = ImageDraw.Draw(im)
    big = [(cx + (px - cx) * 1.08, cy + (py - cy) * 1.08) for px, py in pts]
    d.polygon(big, fill=OUTLINE + (255,))
    d.polygon(pts, fill=(96, 104, 118, 255))
    # steel facet shading
    d.polygon([(cx, cy)] + pts[:4], fill=(140, 150, 165, 255))
    d.polygon([(cx, cy)] + pts[5:8], fill=(56, 60, 72, 255))
    # orange-hot edges
    d.line(pts + [pts[0]], fill=(255, 140, 30, 255), width=max(2, int(S * 0.05)),
           joint="curve")
    d.line(pts + [pts[0]], fill=OUTLINE + (255,), width=max(1, int(S * 0.02)),
           joint="curve")
    im = gloss(im, cx - S * 0.1, cy - S * 0.12, S * 0.14, S * 0.08, alpha=120)
    return im


def draw_muzzle_flash(S: int) -> Image.Image:
    """Starburst flash pointing right, core at centre-left."""
    im = canvas(S)
    cx, cy = S * 0.30, S * 0.5
    rnd = random.Random(5)

    # outer glow
    gl = canvas(S)
    dg = ImageDraw.Draw(gl)
    dg.ellipse((cx - S * 0.2, cy - S * 0.24, cx + S * 0.28, cy + S * 0.24),
               fill=(255, 140, 30, 120))
    over(im, blur(gl, S * 0.03))

    # jagged flame petals licking right
    for scale, col in ((1.0, (255, 110, 15, 215)), (0.62, (255, 200, 60, 240))):
        lay = canvas(S)
        d = ImageDraw.Draw(lay)
        petals = []
        n = 7
        for i in range(n):
            a = (i - (n - 1) / 2) * math.radians(26)
            length = S * (0.60 if abs(i - 3) < 1 else rnd.uniform(0.34, 0.5)) * scale
            width = math.radians(15)
            tipx = cx + math.cos(a) * length
            tipy = cy + math.sin(a) * length * 0.9
            bx1 = cx + math.cos(a - width) * S * 0.10
            by1 = cy + math.sin(a - width) * S * 0.10
            bx2 = cx + math.cos(a + width) * S * 0.10
            by2 = cy + math.sin(a + width) * S * 0.10
            petals.append([(bx1, by1), (tipx, tipy), (bx2, by2)])
        for p in petals:
            d.polygon(p, fill=col)
        over(im, blur(lay, S * 0.006))

    # white-hot core
    core = canvas(S)
    dc = ImageDraw.Draw(core)
    dc.ellipse((cx - S * 0.06, cy - S * 0.11, cx + S * 0.15, cy + S * 0.11),
               fill=(255, 252, 230, 255))
    dc.ellipse((cx - S * 0.02, cy - S * 0.06, cx + S * 0.08, cy + S * 0.06),
               fill=(255, 255, 255, 255))
    over(im, blur(core, S * 0.008))

    # spark dots to the right
    d = ImageDraw.Draw(im)
    for _ in range(8):
        a = rnd.uniform(-0.6, 0.6)
        dist = rnd.uniform(S * 0.3, S * 0.62)
        px, py = cx + math.cos(a) * dist, cy + math.sin(a) * dist * 0.7
        pr = rnd.uniform(S * 0.008, S * 0.02)
        d.ellipse((px - pr, py - pr, px + pr, py + pr),
                  fill=(255, rnd.randint(180, 240), 80, 255))
    return im


# ---------------------------------------------------------------- explosion


def _jag_blob(S, cx, cy, r, jag, seed, n=16):
    rnd = random.Random(seed)
    pts = []
    for i in range(n):
        a = i * 2 * math.pi / n
        rr = r * (1 + jag * rnd.uniform(-1, 1))
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    return pts


def draw_explosion_frame(S: int, frame: int) -> Image.Image:
    im = canvas(S)
    cx = cy = S / 2
    rnd = random.Random(100 + frame)

    if frame == 0:
        # small intense white-yellow flash core
        gl = canvas(S)
        dg = ImageDraw.Draw(gl)
        dg.ellipse((cx - S * 0.20, cy - S * 0.20, cx + S * 0.20, cy + S * 0.20),
                   fill=(255, 190, 60, 160))
        over(im, blur(gl, S * 0.03))
        d = ImageDraw.Draw(im)
        for i in range(8):
            a = i * math.pi / 4
            d.line((cx + math.cos(a) * S * 0.06, cy + math.sin(a) * S * 0.06,
                    cx + math.cos(a) * S * 0.24, cy + math.sin(a) * S * 0.24),
                   fill=(255, 220, 110, 230), width=int(S * 0.03))
        over(im, shaded_disc(S, cx, cy, S * 0.13,
                             [(0.0, (255, 255, 255)), (1.0, (255, 240, 170))],
                             light_strength=0.2))
        return im

    # frame params: radius, jag, core ratio, palette stage
    P = {1: (0.30, 0.16, 0.52), 2: (0.40, 0.18, 0.46), 3: (0.46, 0.20, 0.38),
         4: (0.47, 0.22, 0.26), 5: (0.44, 0.24, 0.16), 6: (0.40, 0.26, 0.0),
         7: (0.36, 0.28, 0.0)}[frame]
    r, jag, core_r = S * P[0], P[1], P[2]

    if frame <= 5:
        # dark outline blob, then fiery layers
        pts = _jag_blob(S, cx, cy, r, jag, seed=frame * 7 + 1)
        d = ImageDraw.Draw(im)
        big = [(cx + (px - cx) * 1.045, cy + (py - cy) * 1.045) for px, py in pts]
        if frame <= 3:
            d.polygon(big, fill=(90, 18, 8, 255))
        # outer fire layer
        if frame <= 2:
            outer = [(0.0, (200, 40, 8)), (0.55, (244, 110, 10)), (1.0, (255, 190, 60))]
        elif frame == 3:
            outer = [(0.0, (170, 30, 8)), (0.55, (228, 88, 8)), (1.0, (255, 170, 40))]
        else:
            outer = [(0.0, (120, 24, 10)), (0.55, (190, 60, 12)), (1.0, (238, 120, 25))]
        fm = Image.new("L", (S, S), 0)
        dfm = ImageDraw.Draw(fm)
        dfm.polygon(pts, fill=255)
        lay = shade_over_mask(fm, outer, light_strength=0.35)
        over(im, blur(lay, S * 0.004))
        # mid + core
        if core_r > 0:
            pts2 = _jag_blob(S, cx, cy, r * (core_r + 0.22), jag * 0.8,
                             seed=frame * 13 + 5, n=12)
            d = ImageDraw.Draw(im)
            d.polygon(pts2, fill=(255, 170, 35, 255) if frame <= 3
                      else (240, 110, 20, 255))
            pts3 = _jag_blob(S, cx, cy, r * core_r, jag * 0.6,
                             seed=frame * 17 + 9, n=10)
            core_col = {1: (255, 250, 220), 2: (255, 240, 180), 3: (255, 214, 110),
                        4: (255, 160, 50), 5: (230, 100, 25)}[frame]
            d.polygon(pts3, fill=core_col + (255,))
        # flying sparks
        d = ImageDraw.Draw(im)
        nsp = {1: 4, 2: 8, 3: 12, 4: 10, 5: 6}[frame]
        for _ in range(nsp):
            a = rnd.uniform(0, math.pi * 2)
            dist = r * rnd.uniform(1.05, 1.45)
            px, py = cx + math.cos(a) * dist, cy + math.sin(a) * dist
            pr = rnd.uniform(S * 0.008, S * 0.02)
            d.ellipse((px - pr, py - pr, px + pr, py + pr),
                      fill=(255, rnd.randint(140, 220), 50, 255))

    if frame >= 4:
        # dark smoke puffs breaking through
        nsm = {4: 4, 5: 7, 6: 10, 7: 12}[frame]
        alpha0 = {4: 90, 5: 130, 6: 175, 7: 130}[frame]
        sm = canvas(S)
        dsm = ImageDraw.Draw(sm)
        for i in range(nsm):
            a = rnd.uniform(0, math.pi * 2)
            dist = r * rnd.uniform(0.35, 1.05)
            px, py = cx + math.cos(a) * dist, cy + math.sin(a) * dist
            pr = S * rnd.uniform(0.07, 0.15) * (1 + frame * 0.06)
            g = rnd.randint(70, 105) + frame * 6
            brown = int(g * 0.85)
            dsm.ellipse((px - pr, py - pr, px + pr, py + pr),
                        fill=(g, brown, int(brown * 0.9), alpha0))
        over(im, blur(sm, S * 0.02))
        if frame >= 6:
            # faint orange remnant glow
            gl = canvas(S)
            dg = ImageDraw.Draw(gl)
            rr = r * (0.5 if frame == 6 else 0.3)
            dg.ellipse((cx - rr, cy - rr, cx + rr, cy + rr),
                       fill=(255, 110, 25, 70 if frame == 6 else 40))
            over(im, blur(gl, S * 0.04))
    return im


# ---------------------------------------------------------------- icon


def draw_icon(S: int) -> Image.Image:
    """512px shop icon: badge disc + big polished cannon."""
    im = canvas(S)
    cx = S / 2
    cy = S * 0.52
    R = S * 0.44

    # soft drop shadow
    sh = canvas(S)
    d = ImageDraw.Draw(sh)
    d.ellipse((cx - R, cy - R + S * 0.03, cx + R, cy + R + S * 0.045),
              fill=(0, 0, 0, 110))
    over(im, blur(sh, S * 0.02))

    # badge disc: deep steel-blue with rim
    ow = int(S * 0.012)
    over(im, mask_fill(dilate(_circle_mask(S, cx, cy, R), ow), OUTLINE + (255,)))
    over(im, shaded_disc(S, cx, cy, R,
                         [(0.0, (16, 34, 56)), (0.55, (30, 66, 104)),
                          (1.0, (58, 110, 160))], light_strength=0.8))
    d = ImageDraw.Draw(im)
    d.ellipse((cx - R * 0.94, cy - R * 0.94, cx + R * 0.94, cy + R * 0.94),
              outline=(255, 210, 90, 255), width=int(S * 0.014))
    d.ellipse((cx - R * 0.88, cy - R * 0.88, cx + R * 0.88, cy + R * 0.88),
              outline=(12, 24, 40, 255), width=int(S * 0.008))
    im = gloss(im, cx - R * 0.3, cy - R * 0.45, R * 0.62, R * 0.3, alpha=40, rot=20)

    # cannon on top, drawn big
    cann = draw_cannon(int(S * 0.86), "idle", ow=max(3, int(S * 0.010)))
    im.alpha_composite(cann, (int((S - cann.size[0]) / 2), int(S * 0.06)))
    return im


# ---------------------------------------------------------------- main


def main():
    print("=== bomb shooter overhaul ===")

    # towers (4 frames share a union bbox -> no jitter)
    TS = 384
    frames = [draw_cannon(TS, v) for v in ("idle", "idle1", "recoil", "recover")]
    idle, idle1, atk0, atk1 = crop_shared(frames, 96, margin=0.05)
    save(idle, TOWER_DIR / "idle.png")
    save(idle1, TOWER_DIR / "idle_1.png")
    save(atk0, TOWER_DIR / "attack_0.png")
    save(atk1, TOWER_DIR / "attack_1.png")

    save(trim_center(draw_pad(288), 72, margin=0.05), TOWER_DIR / "pad.png")

    # projectiles & effects
    save(trim_center(draw_bomb_proj(256), 64, margin=0.05), PROJ_DIR / "bomb.png")
    save(trim_center(draw_rocket(256), 64, margin=0.05), PROJ_DIR / "rocket.png")
    save(trim_center(draw_frag(128), 32, margin=0.05), PROJ_DIR / "frag.png")
    save(trim_center(draw_muzzle_flash(256), 64, margin=0.05),
         FX_DIR / "muzzle_flash.png")

    # explosion: 8 frames, shared bbox
    eframes = [draw_explosion_frame(384, f) for f in range(8)]
    for i, eim in enumerate(crop_shared(eframes, 128, margin=0.05)):
        save(eim, EXPL_DIR / f"explosion_{i:02d}.png")

    # icon
    save(draw_icon(512), UI_DIR / "tower-bomb-icon.png")

    # contact sheet for review
    sheet_tiles = [
        ("idle", idle), ("idle_1", idle1), ("attack_0", atk0), ("attack_1", atk1),
        ("pad", trim_center(draw_pad(288), 72, margin=0.05)),
        ("bomb", trim_center(draw_bomb_proj(256), 64, margin=0.05)),
        ("rocket", trim_center(draw_rocket(256), 64, margin=0.05)),
        ("frag", trim_center(draw_frag(128), 32, margin=0.05)),
        ("muzzle", trim_center(draw_muzzle_flash(256), 64, margin=0.05)),
    ]
    efr = crop_shared([draw_explosion_frame(384, f) for f in range(8)], 128,
                      margin=0.05)
    sheet_tiles += [(f"expl_{i}", e) for i, e in enumerate(efr)]
    cols = 6
    cell = 140
    rows = (len(sheet_tiles) + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * cell, rows * cell + 60), (245, 245, 245, 255))
    from PIL import ImageDraw as ID
    dsheet = ID.Draw(sheet)
    for i, (name, tile) in enumerate(sheet_tiles):
        x, y = (i % cols) * cell, (i // cols) * cell
        t = tile.resize((120, 120), Image.Resampling.LANCZOS)
        sheet.paste(t, (x + 10, y + 10), t)
        dsheet.text((x + 8, y + 124), name, fill=(0, 0, 0, 255))
    icon_small = Image.open(UI_DIR / "tower-bomb-icon.png").resize(
        (240, 240), Image.Resampling.LANCZOS)
    sheet.paste(icon_small, (cols * cell - 250, rows * cell - 190), icon_small)
    save(sheet, ROOT / "tools" / "bomb_overhaul_sheet.png")
    print("done")


if __name__ == "__main__":
    main()
