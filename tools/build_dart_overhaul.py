"""
Dart Monkey visual overhaul — procedurally drawn BTD6-style sprites with PIL.

Generates (all RGBA, transparent bg):
  public/assets/towers/dart_monkey/{idle,idle_1,attack_0,attack_1,pad}.png
  public/assets/effects/projectiles/{dart,spike}.png
  public/assets/ui/btd/tower-dart-monkey.png

Towers face UP (12 o'clock); projectiles point RIGHT (3 o'clock).
Run:  python tools/build_dart_overhaul.py
"""
from __future__ import annotations

import math
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(r"C:\Users\Mark Waldeis\Desktop\Game Prompt")
ASSETS = ROOT / "public" / "assets"
TOWER_DIR = ASSETS / "towers" / "dart_monkey"
PROJ_DIR = ASSETS / "effects" / "projectiles"
UI_DIR = ASSETS / "ui" / "btd"

OUTLINE = (28, 18, 12)

# ---------------------------------------------------------------- helpers


def canvas(S: int) -> Image.Image:
    return Image.new("RGBA", (S, S), (0, 0, 0, 0))


def over(base: Image.Image, lay: Image.Image) -> Image.Image:
    base.alpha_composite(lay)
    return base


def blur(im: Image.Image, r: float) -> Image.Image:
    return im.filter(ImageFilter.GaussianBlur(r))


def _grad_rgb(t: np.ndarray, stops: list[tuple[float, tuple[int, int, int]]]) -> np.ndarray:
    ts = np.array([s[0] for s in stops], np.float32)
    cs = np.array([s[1] for s in stops], np.float32)
    idx = np.clip(np.searchsorted(ts, t) - 1, 0, len(stops) - 2)
    t0, t1 = ts[idx], ts[idx + 1]
    c0, c1 = cs[idx], cs[idx + 1]
    u = np.clip((t - t0) / np.maximum(t1 - t0, 1e-6), 0, 1)[..., None]
    return c0 + (c1 - c0) * u


def shaded_disc(S, cx, cy, r, stops, light_dir=(-0.45, -0.89), aa=1.6,
                light_strength=0.75):
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
    S = base.size[0]
    lay = canvas(S)
    d = ImageDraw.Draw(lay)
    d.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=(255, 255, 255, alpha))
    if rot:
        lay = lay.rotate(rot, center=(cx, cy), resample=Image.Resampling.BICUBIC)
    lay = blur(lay, blur_r if blur_r is not None else max(rx, ry) * 0.45)
    return over(base, lay)


def _circle_mask(S, cx, cy, r) -> Image.Image:
    m = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(m)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=255)
    return m


def _ellipse_mask(S, bbox) -> Image.Image:
    m = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(m)
    d.ellipse(bbox, fill=255)
    return m


def _poly_mask(S, pts) -> Image.Image:
    m = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(m)
    d.polygon(pts, fill=255)
    return m


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

FUR_BROWN = [(0.0, (78, 42, 22)), (0.45, (140, 82, 42)), (1.0, (196, 132, 78))]
FUR_DARK = [(0.0, (52, 28, 14)), (0.5, (96, 54, 28)), (1.0, (140, 88, 50))]
SKIN = [(0.0, (170, 100, 55)), (0.45, (228, 162, 100)), (1.0, (255, 210, 155))]
RED_SHIRT = [(0.0, (120, 14, 18)), (0.45, (210, 42, 38)), (1.0, (255, 110, 95))]
BANDANA = [(0.0, (150, 12, 18)), (0.5, (220, 36, 32)), (1.0, (255, 95, 80))]
WOOD = [(0.0, (78, 48, 22)), (0.45, (150, 100, 48)), (1.0, (210, 158, 88))]
WOOD_DARK = [(0.0, (48, 30, 12)), (0.5, (96, 62, 28)), (1.0, (148, 100, 52))]
STEEL = [(0.0, (70, 78, 92)), (0.45, (150, 162, 178)), (1.0, (230, 238, 250))]
STEEL_DARK = [(0.0, (40, 46, 56)), (0.5, (88, 96, 110)), (1.0, (150, 160, 175))]
LEAF = [(0.0, (34, 88, 28)), (0.5, (72, 160, 48)), (1.0, (140, 210, 90))]
BRASS = [(0.0, (140, 92, 22)), (0.5, (219, 168, 62)), (1.0, (255, 228, 140))]
FLIGHT_BLUE = [(0.0, (20, 70, 150)), (0.5, (50, 130, 220)), (1.0, (140, 200, 255))]


# ---------------------------------------------------------------- monkey


def _draw_limb_ellipse(im, S, bbox, stops, ow, light_dir=(-0.45, -0.89)):
    m = _ellipse_mask(S, bbox)
    over(im, mask_fill(dilate(m, ow), OUTLINE + (255,)))
    over(im, shade_over_mask(m, stops, light_dir=light_dir, light_strength=0.8))
    return m


def draw_dart_weapon(im, S, cx, tip_y, base_y, variant, ow, show_flights=True):
    """Dart held pointing UP. tip_y near tip (smaller y), base_y near flights."""
    span = max(base_y - tip_y, S * 0.2)
    # shaft wood
    sw = S * 0.062
    sm = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(sm)
    shaft_top = tip_y + S * 0.075
    d.rounded_rectangle((cx - sw / 2, shaft_top, cx + sw / 2, base_y - S * 0.01),
                        radius=sw * 0.45, fill=255)
    over(im, mask_fill(dilate(sm, max(2, ow * 2 // 3)), OUTLINE + (255,)))
    over(im, shade_over_mask(sm, WOOD, light_dir=(-0.9, -0.2), light_strength=0.85))
    d = ImageDraw.Draw(im)
    for gy in (0.25, 0.45, 0.65):
        y = shaft_top + (base_y - shaft_top) * gy
        d.line((cx - sw * 0.3, y, cx + sw * 0.3, y),
               fill=(90, 55, 22, 110), width=max(1, ow // 3))

    # metal tip — longer, brighter chrome point
    tip_h = S * 0.125
    tip_pts = [
        (cx, tip_y),
        (cx - S * 0.062, tip_y + tip_h),
        (cx + S * 0.062, tip_y + tip_h),
    ]
    tm = _poly_mask(S, tip_pts)
    d = ImageDraw.Draw(tm)
    d.ellipse((cx - S * 0.05, tip_y + tip_h * 0.48,
               cx + S * 0.05, tip_y + tip_h * 1.12), fill=255)
    over(im, mask_fill(dilate(tm, max(2, ow * 2 // 3)), OUTLINE + (255,)))
    over(im, shade_over_mask(
        tm, [(0.0, (90, 100, 118)), (0.4, (180, 192, 210)), (1.0, (250, 252, 255))],
        light_dir=(-0.35, -0.92), light_strength=0.95))
    im = gloss(im, cx - S * 0.01, tip_y + tip_h * 0.3, S * 0.02, S * 0.045, alpha=200)
    # sharp edge line
    d = ImageDraw.Draw(im)
    d.line((cx - S * 0.01, tip_y + tip_h * 0.15, cx + S * 0.04, tip_y + tip_h * 0.7),
           fill=(255, 255, 255, 140), width=max(1, ow // 2))
    # brass collar
    cy_c = tip_y + tip_h * 0.98
    cm = _ellipse_mask(S, (cx - S * 0.05, cy_c - S * 0.016,
                           cx + S * 0.05, cy_c + S * 0.016))
    over(im, mask_fill(dilate(cm, max(1, ow // 2)), OUTLINE + (255,)))
    over(im, shade_over_mask(cm, BRASS, light_strength=0.7))

    if show_flights:
        # flights at base — compact vanes so they don't swallow the silhouette
        fy0 = base_y - S * 0.015
        fy1 = base_y + S * 0.085
        for side in (-1, 1):
            pts = [
                (cx, fy0),
                (cx + side * S * 0.10, fy0 + S * 0.018),
                (cx + side * S * 0.115, fy1),
                (cx + side * S * 0.018, fy1 - S * 0.008),
            ]
            fm = _poly_mask(S, pts)
            over(im, mask_fill(dilate(fm, max(1, ow // 2)), OUTLINE + (255,)))
            over(im, shade_over_mask(fm, FLIGHT_BLUE, light_dir=(-0.3, -0.9)))
            d = ImageDraw.Draw(im)
            d.line((cx + side * S * 0.01, fy0 + S * 0.01,
                    cx + side * S * 0.075, fy1 - S * 0.02),
                   fill=(20, 50, 120, 180), width=max(1, ow // 3))
        # yellow center vane
        pts = [
            (cx - S * 0.028, fy0 + S * 0.008),
            (cx + S * 0.028, fy0 + S * 0.008),
            (cx + S * 0.018, fy1 - S * 0.015),
            (cx - S * 0.018, fy1 - S * 0.015),
        ]
        fm = _poly_mask(S, pts)
        over(im, mask_fill(dilate(fm, max(1, ow // 2)), OUTLINE + (255,)))
        over(im, shade_over_mask(
            fm, [(0.0, (180, 160, 20)), (0.5, (255, 220, 60)), (1.0, (255, 245, 160))],
            light_strength=0.6))

    if variant == "recover":
        # speed lines ahead of tip (throwing forward / up)
        st = canvas(S)
        ds = ImageDraw.Draw(st)
        for i in range(5):
            y = tip_y - S * 0.01 - i * S * 0.028
            a = 170 - i * 28
            half = S * (0.05 + i * 0.008)
            ds.line((cx - half, y, cx + half, y),
                    fill=(255, 245, 190, a), width=max(2, ow))
        over(im, blur(st, S * 0.008))
    return im


def draw_monkey(S: int, variant: str = "idle") -> Image.Image:
    """Top-down BTD Dart Monkey facing UP. variant: idle|idle1|recoil|recover.

    Weapon is held on the RIGHT of the body pointing UP so the face stays clear
    (pass-1 bug: centered dart flights read as a face-visor).
    """
    im = canvas(S)
    ow = max(2, round(S * 0.032))
    cx = S * 0.5

    bob = 0.0
    lean = 0.0
    if variant == "idle1":
        bob = -S * 0.012
    elif variant == "recoil":
        lean = S * 0.035          # wind-up: sit back
    elif variant == "recover":
        lean = -S * 0.028         # follow-through: lean forward

    body_cy = S * 0.60 + bob + lean * 0.4
    head_cy = S * 0.34 + bob + lean * 0.55
    br = S * 0.205
    hr = S * 0.155

    # ground shadow
    sh = canvas(S)
    d = ImageDraw.Draw(sh)
    d.ellipse((cx - br * 1.1, body_cy + br * 0.4, cx + br * 1.1, body_cy + br * 1.0),
              fill=(0, 0, 0, 78))
    over(im, blur(sh, S * 0.022))

    # ---- feet
    for side in (-1, 1):
        fx = cx + side * br * 0.52
        fy = body_cy + br * 0.78
        _draw_limb_ellipse(
            im, S,
            (fx - S * 0.068, fy - S * 0.04, fx + S * 0.068, fy + S * 0.05),
            FUR_DARK, ow, light_dir=(-0.3, -0.9))
        d = ImageDraw.Draw(im)
        for t in (-0.55, 0, 0.55):
            tx = fx + t * S * 0.028
            d.ellipse((tx - S * 0.012, fy + S * 0.008, tx + S * 0.012, fy + S * 0.035),
                      fill=(60, 32, 16, 210))

    # ---- hips
    for side in (-1, 1):
        lx = cx + side * br * 0.40
        ly = body_cy + br * 0.48
        _draw_limb_ellipse(
            im, S,
            (lx - S * 0.07, ly - S * 0.08, lx + S * 0.07, ly + S * 0.09),
            FUR_BROWN, ow)

    # ---- back (left) arm resting at side
    left_x = cx - br * 0.82
    left_y = body_cy + br * 0.02
    if variant == "recover":
        left_y = body_cy - br * 0.05
    _draw_limb_ellipse(
        im, S,
        (left_x - S * 0.075, left_y - S * 0.08, left_x + S * 0.085, left_y + S * 0.1),
        FUR_BROWN, ow, light_dir=(0.5, -0.7))
    _draw_limb_ellipse(
        im, S,
        (left_x - S * 0.05, left_y + S * 0.02, left_x + S * 0.04, left_y + S * 0.1),
        SKIN, ow)

    # ---- torso + red shirt
    body_m = _circle_mask(S, cx, body_cy, br)
    over(im, mask_fill(dilate(body_m, ow), OUTLINE + (255,)))
    over(im, shaded_disc(S, cx, body_cy, br, FUR_BROWN, light_strength=0.78))
    shirt_r = br * 0.80
    shirt_cy = body_cy - br * 0.05
    over(im, shade_over_mask(_circle_mask(S, cx, shirt_cy, shirt_r),
                             RED_SHIRT, light_strength=0.75))
    d = ImageDraw.Draw(im)
    d.ellipse((cx - shirt_r * 0.9, shirt_cy - shirt_r * 0.9,
               cx + shirt_r * 0.9, shirt_cy + shirt_r * 0.9),
              outline=(90, 12, 14, 170), width=max(1, int(S * 0.011)))
    belly = _ellipse_mask(S, (cx - shirt_r * 0.4, shirt_cy - shirt_r * 0.12,
                              cx + shirt_r * 0.4, shirt_cy + shirt_r * 0.52))
    over(im, shade_over_mask(
        belly, [(0.0, (180, 70, 50)), (0.5, (240, 120, 95)), (1.0, (255, 170, 140))],
        light_strength=0.5))
    im = gloss(im, cx - br * 0.28, body_cy - br * 0.32, br * 0.38, br * 0.2,
               alpha=40, rot=25)

    # ---- head (clean face — no weapon overlap)
    for side in (-1, 1):
        ex = cx + side * hr * 0.98
        ey = head_cy + hr * 0.08
        er = hr * 0.40
        em = _circle_mask(S, ex, ey, er)
        over(im, mask_fill(dilate(em, max(2, ow * 2 // 3)), OUTLINE + (255,)))
        over(im, shaded_disc(S, ex, ey, er, FUR_BROWN, light_strength=0.7))
        over(im, shaded_disc(
            S, ex, ey, er * 0.5,
            [(0.0, (150, 80, 70)), (0.5, (220, 140, 120)), (1.0, (255, 190, 170))],
            light_strength=0.5))

    head_m = _circle_mask(S, cx, head_cy, hr)
    over(im, mask_fill(dilate(head_m, ow), OUTLINE + (255,)))
    over(im, shaded_disc(S, cx, head_cy, hr, FUR_BROWN, light_strength=0.8))

    face_cy = head_cy - hr * 0.10
    face_rx, face_ry = hr * 0.70, hr * 0.66
    face_m = _ellipse_mask(S, (cx - face_rx, face_cy - face_ry,
                               cx + face_rx, face_cy + face_ry))
    over(im, shade_over_mask(face_m, SKIN, light_strength=0.72))
    im = gloss(im, cx - hr * 0.22, face_cy - hr * 0.25, hr * 0.28, hr * 0.16,
               alpha=55, rot=20)

    # red bandana across crown
    bm = Image.new("L", (S, S), 0)
    db = ImageDraw.Draw(bm)
    db.chord((cx - hr * 1.05, head_cy - hr * 1.05, cx + hr * 1.05, head_cy + hr * 1.05),
             start=205, end=335, fill=255)
    clip = Image.new("L", (S, S), 0)
    ImageDraw.Draw(clip).rectangle(
        (0, head_cy - hr * 0.95, S, head_cy - hr * 0.22), fill=255)
    bm = Image.composite(bm, Image.new("L", (S, S), 0), clip)
    over(im, mask_fill(dilate(bm, max(1, ow // 2)), OUTLINE + (255,)))
    over(im, shade_over_mask(bm, BANDANA, light_strength=0.65))
    # bandana tails left
    d = ImageDraw.Draw(im)
    d.polygon([
        (cx - hr * 0.82, head_cy - hr * 0.32),
        (cx - hr * 1.28, head_cy - hr * 0.52),
        (cx - hr * 1.18, head_cy - hr * 0.12),
        (cx - hr * 0.72, head_cy - hr * 0.18),
    ], fill=(200, 30, 28, 255), outline=OUTLINE + (255,))
    d.polygon([
        (cx - hr * 0.78, head_cy - hr * 0.25),
        (cx - hr * 1.22, head_cy - hr * 0.02),
        (cx - hr * 0.98, head_cy + hr * 0.08),
        (cx - hr * 0.68, head_cy - hr * 0.10),
    ], fill=(175, 22, 20, 255), outline=OUTLINE + (255,))

    # eyes
    eye_y = face_cy - hr * 0.06
    eye_dx = hr * 0.30
    for side in (-1, 1):
        ex = cx + side * eye_dx
        ew, eh = hr * 0.20, hr * 0.24
        d.ellipse((ex - ew, eye_y - eh, ex + ew, eye_y + eh),
                  fill=(255, 255, 255, 255), outline=OUTLINE + (255,),
                  width=max(1, ow // 2))
        ir = hr * 0.10
        iy = eye_y - hr * 0.035
        d.ellipse((ex - ir, iy - ir, ex + ir, iy + ir), fill=(46, 125, 68, 255))
        d.ellipse((ex - ir * 0.5, iy - ir * 0.5, ex + ir * 0.5, iy + ir * 0.5),
                  fill=(18, 38, 22, 255))
        d.ellipse((ex - ir * 0.35, iy - ir * 0.55, ex - ir * 0.05, iy - ir * 0.18),
                  fill=(255, 255, 255, 230))
    for side in (-1, 1):
        ex = cx + side * eye_dx
        d.arc((ex - hr * 0.18, eye_y - hr * 0.40, ex + hr * 0.18, eye_y),
              start=200, end=340, fill=OUTLINE + (255,), width=max(2, ow))

    # snout
    sn_cy = face_cy + hr * 0.34
    sn_rx, sn_ry = hr * 0.36, hr * 0.26
    sn_m = _ellipse_mask(S, (cx - sn_rx, sn_cy - sn_ry, cx + sn_rx, sn_cy + sn_ry))
    over(im, shade_over_mask(
        sn_m, [(0.0, (160, 95, 55)), (0.5, (220, 150, 95)), (1.0, (255, 200, 145))],
        light_strength=0.6))
    nw, nh = hr * 0.17, hr * 0.11
    d.ellipse((cx - nw, sn_cy - nh * 1.15, cx + nw, sn_cy + nh * 0.35),
              fill=(70, 35, 22, 255), outline=OUTLINE + (255,), width=max(1, ow // 2))
    d.ellipse((cx - nw * 0.55, sn_cy - nh * 0.95, cx - nw * 0.08, sn_cy - nh * 0.3),
              fill=(120, 70, 50, 200))
    d.arc((cx - hr * 0.2, sn_cy - hr * 0.02, cx + hr * 0.2, sn_cy + hr * 0.26),
          start=15, end=165, fill=(90, 40, 25, 255), width=max(2, ow))

    # ---- throwing arm (RIGHT) + dart held clear of face ----
    # Pose table: hand position and dart tip/base
    if variant == "recoil":
        # wind-up: arm low-right, dart cocked beside hip, tip still up
        hx, hy = cx + br * 0.98, body_cy + br * 0.22
        dart_cx = hx + S * 0.015
        tip_y = hy - S * 0.24
        base_y = hy + S * 0.13
        arm_mid = (cx + br * 0.72, body_cy + br * 0.12)
    elif variant == "recover":
        # follow-through: arm high-forward, dart released upward
        hx, hy = cx + br * 0.42, head_cy - hr * 0.85
        dart_cx = hx + S * 0.01
        tip_y = max(S * 0.02, hy - S * 0.28)
        base_y = hy + S * 0.06
        arm_mid = (cx + br * 0.68, body_cy - br * 0.45)
    else:
        # idle: dart upright to the RIGHT of the head (face fully visible)
        hx = cx + br * 0.92
        hy = head_cy + hr * 0.22 + bob
        if variant == "idle1":
            hx += S * 0.012
            hy -= S * 0.012
        dart_cx = hx + S * 0.012
        tip_y = hy - S * 0.34
        base_y = hy + S * 0.10
        arm_mid = (cx + br * 0.70, body_cy - br * 0.12)

    # slim limbs via oriented capsules (less "blob arm")
    def _capsule(x0, y0, x1, y1, thick, stops, ld=(-0.5, -0.8)):
        # approximate with ellipse around segment midpoint, stretched
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        length = math.hypot(x1 - x0, y1 - y0) + thick
        ang = math.degrees(math.atan2(y1 - y0, x1 - x0))
        m = Image.new("L", (S, S), 0)
        dm = ImageDraw.Draw(m)
        # draw thick line as capsule
        dm.line([(x0, y0), (x1, y1)], fill=255, width=max(2, int(thick * 2)))
        dm.ellipse((x0 - thick, y0 - thick, x0 + thick, y0 + thick), fill=255)
        dm.ellipse((x1 - thick, y1 - thick, x1 + thick, y1 + thick), fill=255)
        over(im, mask_fill(dilate(m, max(1, ow // 2)), OUTLINE + (255,)))
        over(im, shade_over_mask(m, stops, light_dir=ld, light_strength=0.8))

    sx, sy = cx + br * 0.50, body_cy - br * 0.08
    _capsule(sx, sy, arm_mid[0], arm_mid[1], S * 0.055, FUR_BROWN)
    _capsule(arm_mid[0], arm_mid[1], hx, hy, S * 0.048, FUR_BROWN, ld=(-0.45, -0.85))
    # hand
    _draw_limb_ellipse(
        im, S,
        (hx - S * 0.042, hy - S * 0.04, hx + S * 0.042, hy + S * 0.045),
        SKIN, ow)

    # dart ON TOP of hand, clear of face
    draw_dart_weapon(im, S, dart_cx, tip_y, base_y, variant, ow, show_flights=True)

    # fingers over shaft (compact so shaft still reads)
    d = ImageDraw.Draw(im)
    for ox in (-0.018, 0.0, 0.018):
        d.ellipse((hx + ox * S - S * 0.01, hy - S * 0.006,
                   hx + ox * S + S * 0.01, hy + S * 0.022),
                  fill=(210, 140, 90, 245), outline=OUTLINE + (200,))

    if variant == "recoil":
        sm = canvas(S)
        dsm = ImageDraw.Draw(sm)
        for i in range(3):
            wx = cx + (i - 1) * S * 0.055
            wy = body_cy + br * 0.9
            wr = S * (0.038 + i * 0.01)
            dsm.ellipse((wx - wr, wy - wr * 0.45, wx + wr, wy + wr * 0.45),
                        fill=(180, 150, 100, 95))
        over(im, blur(sm, S * 0.014))

    return im



# ---------------------------------------------------------------- pad


def draw_pad(S: int) -> Image.Image:
    """Wooden circular platform with rope rim — organic companion to dart monkey."""
    im = canvas(S)
    ow = max(2, round(S * 0.038))
    cx = cy = S / 2
    R = S * 0.44

    sh = canvas(S)
    d = ImageDraw.Draw(sh)
    d.ellipse((cx - R, cy - R * 0.82, cx + R, cy + R * 0.95), fill=(0, 0, 0, 72))
    over(im, blur(sh, S * 0.025))

    # outer wood disc
    om = _circle_mask(S, cx, cy, R)
    over(im, mask_fill(dilate(om, ow), OUTLINE + (255,)))
    over(im, shaded_disc(S, cx, cy, R, WOOD_DARK, light_strength=0.7))

    # plank stripes (vertical grain segments)
    d = ImageDraw.Draw(im)
    for i, t in enumerate((-0.55, -0.28, 0, 0.28, 0.55)):
        px = cx + t * R * 0.85
        d.line((px, cy - R * 0.78, px, cy + R * 0.78),
               fill=(40, 24, 10, 90 if i % 2 else 140), width=max(1, int(S * 0.012)))
    # wood rings
    for rr, a in ((0.78, 100), (0.55, 80), (0.32, 70)):
        d.ellipse((cx - R * rr, cy - R * rr, cx + R * rr, cy + R * rr),
                  outline=(60, 36, 14, a), width=max(1, int(S * 0.01)))

    # rope rim (braided look via alternating beads)
    for i in range(24):
        a = math.radians(i * 15)
        rx = cx + math.cos(a) * R * 0.92
        ry = cy + math.sin(a) * R * 0.92
        rr = S * 0.028
        col = (180, 150, 70, 255) if i % 2 == 0 else (140, 110, 50, 255)
        d.ellipse((rx - rr, ry - rr, rx + rr, ry + rr),
                  fill=col, outline=OUTLINE + (255,))
        d.ellipse((rx - rr * 0.4, ry - rr * 0.55, rx + rr * 0.15, ry - rr * 0.1),
                  fill=(230, 210, 140, 180))

    # inner mounting ring (lighter wood)
    inner = _circle_mask(S, cx, cy, R * 0.58)
    over(im, shade_over_mask(inner, WOOD, light_strength=0.65))
    d.ellipse((cx - R * 0.58, cy - R * 0.58, cx + R * 0.58, cy + R * 0.58),
              outline=OUTLINE + (255,), width=max(2, int(S * 0.02)))
    d.ellipse((cx - R * 0.52, cy - R * 0.52, cx + R * 0.52, cy + R * 0.52),
              outline=(200, 160, 90, 160), width=max(1, int(S * 0.01)))

    # 4 brass studs
    for i in range(4):
        a = math.radians(i * 90 + 45)
        rx = cx + math.cos(a) * R * 0.72
        ry = cy + math.sin(a) * R * 0.72
        rr = S * 0.032
        d.ellipse((rx - rr, ry - rr, rx + rr, ry + rr), fill=OUTLINE + (255,))
        d.ellipse((rx - rr * 0.72, ry - rr * 0.72, rx + rr * 0.72, ry + rr * 0.72),
                  fill=(200, 150, 50, 255))
        d.ellipse((rx - rr * 0.45, ry - rr * 0.55, rx - rr * 0.05, ry - rr * 0.1),
                  fill=(255, 230, 140, 220))

    # leaf accent (dart monkey jungle vibe)
    leaf_m = _poly_mask(S, [
        (cx + R * 0.15, cy - R * 0.15),
        (cx + R * 0.38, cy - R * 0.42),
        (cx + R * 0.22, cy - R * 0.05),
    ])
    over(im, mask_fill(dilate(leaf_m, max(1, ow // 2)), OUTLINE + (255,)))
    over(im, shade_over_mask(leaf_m, LEAF, light_strength=0.55))

    im = gloss(im, cx - R * 0.25, cy - R * 0.32, R * 0.4, R * 0.2, alpha=36, rot=25)
    return im


# ---------------------------------------------------------------- projectiles


def draw_dart_proj(S: int) -> Image.Image:
    """Classic dart pointing RIGHT: tip → shaft → flights."""
    im = canvas(S)
    ow = max(2, round(S * 0.04))
    cy = S * 0.5

    # flights (left / trailing)
    for side in (-1, 1):
        pts = [
            (S * 0.08, cy),
            (S * 0.28, cy + side * S * 0.22),
            (S * 0.38, cy + side * S * 0.06),
            (S * 0.36, cy),
        ]
        fm = _poly_mask(S, pts)
        over(im, mask_fill(dilate(fm, max(1, ow // 2)), OUTLINE + (255,)))
        over(im, shade_over_mask(fm, FLIGHT_BLUE, light_dir=(0, -1), light_strength=0.7))
        d = ImageDraw.Draw(im)
        d.line((S * 0.12, cy + side * S * 0.02, S * 0.30, cy + side * S * 0.14),
               fill=(20, 50, 120, 180), width=max(1, ow // 3))
    # yellow top flight
    pts = [
        (S * 0.10, cy - S * 0.04),
        (S * 0.10, cy + S * 0.04),
        (S * 0.36, cy + S * 0.03),
        (S * 0.36, cy - S * 0.03),
    ]
    fm = _poly_mask(S, pts)
    over(im, mask_fill(dilate(fm, max(1, ow // 2)), OUTLINE + (255,)))
    over(im, shade_over_mask(
        fm, [(0.0, (160, 120, 10)), (0.5, (255, 210, 50)), (1.0, (255, 245, 160))],
        light_dir=(0, -1)))

    # wooden shaft
    sm = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(sm)
    d.rounded_rectangle((S * 0.30, cy - S * 0.055, S * 0.72, cy + S * 0.055),
                        radius=S * 0.03, fill=255)
    over(im, mask_fill(dilate(sm, ow), OUTLINE + (255,)))
    over(im, shade_over_mask(sm, WOOD, light_dir=(0, -1), light_strength=0.9))
    d = ImageDraw.Draw(im)
    for gx in (0.40, 0.50, 0.60):
        d.line((S * gx, cy - S * 0.035, S * gx, cy + S * 0.035),
               fill=(80, 48, 18, 100), width=max(1, ow // 3))
    im = gloss(im, S * 0.48, cy - S * 0.03, S * 0.14, S * 0.02, alpha=100)

    # brass band
    bm = Image.new("L", (S, S), 0)
    db = ImageDraw.Draw(bm)
    db.rectangle((S * 0.68, cy - S * 0.07, S * 0.74, cy + S * 0.07), fill=255)
    over(im, mask_fill(dilate(bm, max(1, ow // 2)), OUTLINE + (255,)))
    over(im, shade_over_mask(bm, BRASS, light_dir=(0, -1)))

    # steel tip (pointing right)
    tip = [
        (S * 0.72, cy - S * 0.09),
        (S * 0.95, cy),
        (S * 0.72, cy + S * 0.09),
    ]
    tm = _poly_mask(S, tip)
    over(im, mask_fill(dilate(tm, ow), OUTLINE + (255,)))
    over(im, shade_over_mask(tm, STEEL, light_dir=(0, -1), light_strength=0.95))
    im = gloss(im, S * 0.82, cy - S * 0.025, S * 0.06, S * 0.018, alpha=180)
    # tip edge highlight
    d = ImageDraw.Draw(im)
    d.line((S * 0.74, cy - S * 0.05, S * 0.90, cy),
           fill=(255, 255, 255, 120), width=max(1, ow // 2))
    return im


def draw_spike_proj(S: int) -> Image.Image:
    """Spiked ball for Spike-o-pult / Juggernaut path (orientation free)."""
    im = canvas(S)
    ow = max(2, round(S * 0.04))
    cx = cy = S / 2
    r = S * 0.28
    rnd = random.Random(21)

    # outer glow
    gl = canvas(S)
    dg = ImageDraw.Draw(gl)
    dg.ellipse((cx - r * 1.3, cy - r * 1.3, cx + r * 1.3, cy + r * 1.3),
               fill=(180, 100, 40, 70))
    over(im, blur(gl, S * 0.03))

    # spikes
    n = 10
    for i in range(n):
        a = i * 2 * math.pi / n + 0.15
        length = r * 1.55
        tip = (cx + math.cos(a) * length, cy + math.sin(a) * length)
        w = 0.28
        p1 = (cx + math.cos(a - w) * r * 0.85, cy + math.sin(a - w) * r * 0.85)
        p2 = (cx + math.cos(a + w) * r * 0.85, cy + math.sin(a + w) * r * 0.85)
        sm = _poly_mask(S, [p1, tip, p2])
        over(im, mask_fill(dilate(sm, max(1, ow // 2)), OUTLINE + (255,)))
        over(im, shade_over_mask(sm, STEEL_DARK, light_dir=(-math.cos(a), -math.sin(a)),
                                 light_strength=0.85))
        # hot edge
        d = ImageDraw.Draw(im)
        d.line([p1, tip, p2], fill=(200, 120, 60, 160), width=max(1, ow // 3))

    # core ball
    over(im, mask_fill(dilate(_circle_mask(S, cx, cy, r), ow), OUTLINE + (255,)))
    over(im, shaded_disc(
        S, cx, cy, r,
        [(0.0, (60, 40, 20)), (0.45, (140, 95, 45)), (1.0, (200, 150, 80))],
        light_strength=0.85))
    # rivets
    d = ImageDraw.Draw(im)
    for i in range(6):
        a = i * math.pi / 3 + 0.4
        rx = cx + math.cos(a) * r * 0.55
        ry = cy + math.sin(a) * r * 0.55
        rr = S * 0.035
        d.ellipse((rx - rr, ry - rr, rx + rr, ry + rr), fill=OUTLINE + (255,))
        d.ellipse((rx - rr * 0.7, ry - rr * 0.7, rx + rr * 0.7, ry + rr * 0.7),
                  fill=(90, 95, 105, 255))
    im = gloss(im, cx - r * 0.3, cy - r * 0.35, r * 0.35, r * 0.2, alpha=130, rot=30)
    return im


# ---------------------------------------------------------------- UI icon


def draw_icon(S: int = 512) -> Image.Image:
    """BTD-style circular badge with dart monkey portrait."""
    im = canvas(S)
    cx = cy = S / 2

    # soft drop shadow
    sh = canvas(S)
    d = ImageDraw.Draw(sh)
    d.ellipse((S * 0.12, S * 0.14, S * 0.90, S * 0.92), fill=(0, 0, 0, 90))
    over(im, blur(sh, S * 0.025))

    # badge disc — leaf green like classic dart theme
    badge_stops = [(0.0, (28, 72, 30)), (0.5, (56, 130, 48)), (1.0, (120, 190, 80))]
    R = S * 0.40
    over(im, mask_fill(dilate(_circle_mask(S, cx, cy, R), max(3, S // 80)),
                       (20, 30, 16, 255)))
    over(im, shaded_disc(S, cx, cy, R, badge_stops, light_strength=0.55))

    # gold ring
    d = ImageDraw.Draw(im)
    for w, col in ((S * 0.028, (100, 70, 10, 255)),
                   (S * 0.018, (230, 185, 50, 255)),
                   (S * 0.008, (255, 240, 150, 220))):
        d.ellipse((cx - R, cy - R, cx + R, cy + R),
                  outline=col, width=max(2, int(w)))

    # inner vignette
    vig = canvas(S)
    dv = ImageDraw.Draw(vig)
    dv.ellipse((cx - R * 0.88, cy - R * 0.88, cx + R * 0.88, cy + R * 0.88),
               fill=(0, 0, 0, 50))
    over(im, blur(vig, S * 0.02))

    # render monkey at high res and composite
    monkey = draw_monkey(int(S * 0.72), "idle")
    # scale monkey to fit badge
    target = int(S * 0.72)
    monkey = trim_center(monkey, target, margin=0.04)
    ox = (S - target) // 2
    oy = (S - target) // 2 + int(S * 0.02)
    im.paste(monkey, (ox, oy), monkey)

    # tiny dart accent on ring edge
    dart = draw_dart_proj(int(S * 0.22))
    dart = dart.rotate(-35, expand=True, resample=Image.Resampling.BICUBIC)
    dx = int(S * 0.68)
    dy = int(S * 0.62)
    im.paste(dart, (dx, dy), dart)

    return im


# ---------------------------------------------------------------- contact sheet


def contact_sheet(imgs: list[tuple[str, Image.Image]], cell=140, cols=5) -> Image.Image:
    rows = math.ceil(len(imgs) / cols)
    pad = 12
    W = cols * cell + (cols + 1) * pad
    H = rows * (cell + 22) + (rows + 1) * pad
    sheet = Image.new("RGBA", (W, H), (245, 245, 250, 255))
    d = ImageDraw.Draw(sheet)
    for i, (name, im) in enumerate(imgs):
        r, c = divmod(i, cols)
        x = pad + c * (cell + pad)
        y = pad + r * (cell + 22 + pad)
        # checkerboard bg for alpha
        for yy in range(0, cell, 8):
            for xx in range(0, cell, 8):
                col = (230, 230, 235, 255) if (xx // 8 + yy // 8) % 2 == 0 else (255, 255, 255, 255)
                d.rectangle((x + xx, y + yy, x + xx + 8, y + yy + 8), fill=col)
        thumb = im.copy()
        thumb.thumbnail((cell, cell), Image.Resampling.LANCZOS)
        ox = x + (cell - thumb.size[0]) // 2
        oy = y + (cell - thumb.size[1]) // 2
        sheet.paste(thumb, (ox, oy), thumb)
        d.text((x + 4, y + cell + 2), name, fill=(30, 30, 40, 255))
    return sheet


# ---------------------------------------------------------------- main


def main():
    print("Dart Monkey overhaul — generating sprites…")
    SS = 384  # supersample
    OUT = 96
    PAD_OUT = 72
    PROJ_OUT = 64
    SPIKE_OUT = 56

    # tower frames
    raw = {
        "idle": draw_monkey(SS, "idle"),
        "idle_1": draw_monkey(SS, "idle1"),
        "attack_0": draw_monkey(SS, "recoil"),
        "attack_1": draw_monkey(SS, "recover"),
    }
    frames = crop_shared(list(raw.values()), OUT, margin=0.08)
    names = list(raw.keys())
    for name, fr in zip(names, frames):
        save(fr, TOWER_DIR / f"{name}.png")

    pad = trim_center(draw_pad(SS), PAD_OUT, margin=0.04)
    save(pad, TOWER_DIR / "pad.png")

    dart = trim_center(draw_dart_proj(SS), PROJ_OUT, margin=0.06)
    save(dart, PROJ_DIR / "dart.png")

    spike = trim_center(draw_spike_proj(SS), SPIKE_OUT, margin=0.05)
    save(spike, PROJ_DIR / "spike.png")

    icon = draw_icon(512)
    save(icon, UI_DIR / "tower-dart-monkey.png")

    # verify alpha corners
    for p in [TOWER_DIR / "idle.png", PROJ_DIR / "dart.png", UI_DIR / "tower-dart-monkey.png"]:
        a = np.array(Image.open(p))
        corners = [a[0, 0, 3], a[0, -1, 3], a[-1, 0, 3], a[-1, -1, 3]]
        print(f"  alpha corners {p.name}: {corners}")

    sheet_imgs = [
        ("idle", frames[0]),
        ("idle_1", frames[1]),
        ("atk0", frames[2]),
        ("atk1", frames[3]),
        ("pad", pad),
        ("dart", dart),
        ("spike", spike),
        ("icon/4", icon.resize((128, 128), Image.Resampling.LANCZOS)),
    ]
    sheet = contact_sheet(sheet_imgs, cell=120, cols=4)
    sheet_path = ROOT / "tools" / "dart_overhaul_sheet.png"
    sheet.convert("RGB").save(sheet_path, "PNG")
    print("  wrote", sheet_path.relative_to(ROOT))
    print("Done.")


if __name__ == "__main__":
    main()
