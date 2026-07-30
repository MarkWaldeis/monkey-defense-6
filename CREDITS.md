# Monkey Defense 6 — Credits & Licenses

## Game

Original tower-defense game inspired by the Bloons TD genre.
**Pro Asset Edition** uses free 2D sprites instead of pure procedural Canvas art.

---

## Assets

### Kenney — Tower Defense (Top-Down)

| Field | Value |
|-------|--------|
| **Author** | Kenney (www.kenney.nl) |
| **License** | [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/) |
| **URL** | https://kenney.nl/assets/tower-defense |
| **Mirror** | https://opengameart.org/content/tower-defense-300-tilessprites |
| **Local path** | `public/assets/kenney/` |
| **Archive** | `public/assets/kenney-tower-defense-top-down.zip` |

**Used for:**

- Map terrain tiles (grass, dirt/path, sand, water edges)
- Tower sprites (turrets, rocket launchers, tanks, crystal pads)
- MOAB-class enemies (planes / tanks recolored as aerial blimps)
- Projectiles (bullets, rockets, flames)
- Some decorations (trees, bushes, rocks, circular pads)

CC0: free for commercial and non-commercial use; attribution optional but appreciated.

### Project-generated sprites (CC0)

| Category | Path | Notes |
|----------|------|--------|
| Regular bloons | `public/assets/bloons/*.png` | Flat cartoon balloons matching Kenney palette |
| Pop animation | `public/assets/bloons/pop_animation/` | Expanding particle frames |
| Explosion / freeze / magic FX | `public/assets/effects/` | Animated effect frames |
| Magic / laser / plasma / ice orbs | `public/assets/effects/projectiles/` | Energy projectiles |
| UI buttons, panels, icons, HP bars | `public/assets/ui/` | HUD chrome |
| Recolored terrain variants | `public/assets/tiles/snow*.png`, `lava_base.png`, `dark*.png` | Kenney tiles recolored for Frozen Lake / Lava Fields / Dark Castle |

These were created for this project and released under **CC0 1.0**.

---

## Manifest

See `public/assets/assets.json` for the full key → path mapping used by the game loader.

---

## Inspiration

Gameplay is an original implementation inspired by publicly known tower-defense conventions (paths, layers, upgrades, economy). It does **not** use Ninja Kiwi source code, trademarks, or official Bloons TD artwork.
