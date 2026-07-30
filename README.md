# Monkey Defense 6

Bloons TD–inspired tower defense for the browser.  
**Pro Asset Edition** — HTML5 Canvas + Kenney CC0 tiles + custom bloon sprites + BTD-style DOM UI.

## Play

- **Live:** https://markwaldeis.github.io/monkey-defense-6/ (hard-refresh Ctrl+F5 after updates)
- **Local:**

```bash
cd "Desktop/Game Prompt"
python -m http.server 8766 --bind 127.0.0.1
# open http://127.0.0.1:8766/monkey-defense-6.html
```

No build step. Main file: `monkey-defense-6.html`.

---

## Features

- **8 maps** — Beginner (6) + Intermediate (2); Advanced/Expert packs coming soon
- **13 towers** with BTD6-style **3×5 upgrade paths** and crosspath rules
- Full bloon hierarchy including **MOAB / BFB / ZOMG / DDT / BAD**
- Difficulties: **Easy (R40) · Medium (R60) · Hard (R100) · Expert (R100 + boss HP)**
- **Map pack tabs independent of game difficulty** — play Meadow on Expert
- Targeting (First / Last / Strong / Close), sell refund, auto-start, 1–3× speed
- Camo / lead / MOAB threat banners one round ahead
- Water-only Boat & Sub placement

## Controls

| Input | Action |
|-------|--------|
| Click / drag tower icon | Place tower |
| Click placed tower | Upgrades / sell / targeting |
| **▶ GO** or **Space** | Start next round |
| **1** / **2** / **3** | Game speed |
| **Shift+1…9** | Select tower type to place |
| **T** | Cycle targeting (selected tower) |
| **Backspace / Delete** | Sell selected tower |
| **Esc** | Cancel place · deselect · pause |
| Right-click / long-press | Cancel placement |

## Project layout

```text
monkey-defense-6.html   # full game (canvas + BTD DOM UI)
index.html              # redirects to the game
public/assets/          # towers, bloons, tiles, UI, Kenney pack
CREDITS.md              # licenses
CONTINUE.md             # handoff notes
```

## License

- Game code: free to use/modify for personal projects
- Art: see [CREDITS.md](CREDITS.md) — Kenney Tower Defense is **CC0 1.0**
