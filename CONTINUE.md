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
- Towers aim/rotate toward bloons, recoil + muzzle flash; no floating bob
- Bomb = Kenney cannon; Tack = multi-barrel machine; other monkeys character art
- Paths end at **BASE fort**; leaks cost RBE lives with LEAK feedback
- Camo/Lead warnings one round ahead

## Towers (order)
dart, sniper, bomb, ice, wizard, farm, super, tack — 3 upgrades each

## Known UX
- Difficulty tabs set `selectedDiff` before map click
- Sidebar drag-or-click to place; leave margin for right sidebar (`x < W-120`)
- Upgrade panel draws left of sidebar when a placed tower is selected

## Recent fixes
- Map select soft-lock: cards rebuilt every frame → fixed; now rebuild only on enter
- Map click: delegated handler + all maps unlocked
- Explicit `display`/`pointer-events` on map UI show/hide

## Next ideas (if continuing)
- Real map thumbnails per map
- Hero picker, locked tower progression, more BTD polish
- Favicon, better audio files
- Balance / more maps
