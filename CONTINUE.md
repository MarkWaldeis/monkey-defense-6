# Monkey Defense 6 — Handoff / Context Compact

## Play links
- **Live:** https://markwaldeis.github.io/monkey-defense-6/ (hard-refresh Strg+F5)
- **Local:** `cd "C:\Users\Mark Waldeis\Desktop\Game Prompt"` → `python -m http.server 8766` → http://127.0.0.1:8766/monkey-defense-6.html
- **Repo:** https://github.com/MarkWaldeis/monkey-defense-6

## Core files
- `monkey-defense-6.html` — full game (canvas + BTD DOM UI overlay)
- `public/assets/` — towers, bloons, tiles, effects, Kenney pack, `ui/btd/` portraits
- `CREDITS.md` — Kenney CC0 + project assets
- Procedural backup: `monkey-defense-6-procedural-backup.html`

## Architecture
- **Canvas game** 1280×720 logical, scaled to window
- **State machine:** LOADING → MAIN_MENU → MAP_SELECT → GAMEPLAY (PAUSE / GAME_OVER / VICTORY)
- **BTD DOM UI** (`#btdMapSelect`, `#btdSidebar`): map carousel + wood tower sidebar
- Map click uses **event delegation** on `#btdMapTrack` (`data-map` index) → `startGame()`
- All maps unlocked for playability
- **Top-down 3D towers (BTD6-style):**
  - Fixed **pad** at `(x,y)` (never rotates)
  - **Body** sprite faces UP; rotates with `aim + π/2` around same point
  - Shoot: `attack_0/1` frames + body recoil + muzzle flash (pad stays put)
  - Bomb/tack: Kenney top-down turrets; monkeys: original top-down art
- Paths end at **BASE fort**; leaks cost RBE lives with LEAK feedback
- Camo/Lead warnings one round ahead

## Towers (order)
dart, boomer, tack, sniper, ninja, **water**, glue, bomb, ice, wizard, farm, super  
- **Water Monkey** (Buccaneer-style): water shots, pierce, late AoE  
- **Glue Gunner**: slows bloons  
- **Boomerang**: high pierce  
- **Ninja**: camo from start  
## Modes
Easy R40 · Medium R60 · Hard R100 · Expert R100 (harder stats)  
Difficulty tabs on map select stay (BTD-style). Current maps are **Beginner/Easy** pack only.  
## Maps (Beginner)
Monkey Meadow · In the Loop · Logs · Candy Falls · Alpine Lake · Spa Pits  
(BTD6-inspired easy layouts; stone/road/candy path styles; water zones for boat/sub)  
## Enemies
MOAB → BFB → ZOMG → DDT (camo+lead) → BAD; high HP BTD6-style bosses

## Known UX
- Difficulty tabs set `selectedDiff` before map click
- **Large tower sidebar** (~220px): **fixed right** unless actively placing a tower; only while `placingTower` is set, auto-flips opposite the cursor (hysteresis 42%/58%) so the free side is placeable; cancels → snaps back right
- `canPlace` / drag-drop use `overSidebar()` + `sidebarGameW()` (scale-aware)
- Upgrade panel (`towerPanelX()`) sits next to the free edge of the docked sidebar
- Sidebar drag-or-click to place

## Recent fixes
- Map select soft-lock: cards rebuilt every frame → fixed; now rebuild only on enter
- Map click: delegated handler + all maps unlocked
- Explicit `display`/`pointer-events` on map UI show/hide
- Bigger tower menu + auto left/right dock opposite cursor
- Sidebar full viewport height; HUD pause/speed/GO shifted left of dock
- Ninja Monkey (camo detect) + shuriken assets
- Full top-down tower rebuild (pads + rotating bodies + attack frames for all 9)

## Next ideas (if continuing)
- Real map thumbnails per map
- Hero picker, locked tower progression, more BTD polish
- Favicon, better audio files
- Balance / more maps
