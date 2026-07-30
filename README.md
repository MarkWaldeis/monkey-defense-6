# Monkey Defense 6

Bloons TD–inspired tower defense game for the browser.  
**Pro Asset Edition** — HTML5 Canvas + Kenney CC0 tiles + custom bloon sprites.

Play online (after GitHub Pages is enabled):

```text
https://<your-user>.github.io/<repo-name>/
```

Or open locally:

```bash
# from this folder
python -m http.server 8766
# then visit http://127.0.0.1:8766/
```

No build step required. Main file: `monkey-defense-6.html`.

---

## Features

- 5 maps (Meadow, Tree Stump, Frozen Lake, Lava Fields, Dark Castle)
- 8 towers with 3 upgrade tiers each
- 15 bloon types including MOAB / BFB / ZOMG
- 60 rounds, 4 difficulties
- Sprite assets, particle FX, Web Audio SFX
- Speed controls (1x–3x), auto-start, sell / targeting

## Controls

| Input | Action |
|-------|--------|
| Click tower icon | Select to place |
| Click map | Place tower |
| Click placed tower | Upgrade / sell / targeting |
| **▶ GO** or **Space** | Start next round |
| **1** / **2** / **3** | Game speed |
| **Esc** | Pause |

## Project layout

```text
monkey-defense-6.html   # full game (single HTML file)
index.html              # redirects to the game (GitHub Pages entry)
public/assets/          # sprites, tiles, UI, Kenney pack
CREDITS.md              # licenses & sources
```

## License

- Game code: free to use/modify for personal projects
- Art: see [CREDITS.md](CREDITS.md) — Kenney Tower Defense is **CC0 1.0**
