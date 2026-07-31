# Monkey Defense 6 — Handoff / Context Compact

## Play links
- **Live:** https://markwaldeis.github.io/monkey-defense-6/ (hard-refresh Strg+F5)
- **Local:** `cd "C:\Users\Mark Waldeis\Desktop\Game Prompt"` → `python -m http.server 8766 --bind 127.0.0.1` → http://127.0.0.1:8766/monkey-defense-6.html
- **Repo:** https://github.com/MarkWaldeis/monkey-defense-6

## Core files
- `monkey-defense-6.html` — full game (canvas + BTD DOM UI overlay)
- `public/assets/` — towers, bloons, tiles, effects, Kenney pack, `ui/btd/` portraits
- `CREDITS.md` — Kenney CC0 + project assets
- Procedural backup: `monkey-defense-6-procedural-backup.html`

## Architecture
- **Canvas game** 1280×720 logical, scaled to window
- **State machine:** LOADING → MAIN_MENU → MAP_SELECT → **DIFFICULTY_SELECT** → GAMEPLAY (PAUSE / GAME_OVER / VICTORY)
- **Map pack vs game difficulty are separate:**
  - `selectedMapTier` — Beginner/Intermediate/Advanced/Expert **tabs** (filter maps)
  - `selectedDiff` — Easy/Medium/Hard/Expert **modes** (lives, cash, rounds, hpMul, sellMul)
- Map click → difficulty panel → `startGame()`
- **BTD DOM UI** (`#btdMapSelect`, `#btdDiffSelect`, `#btdSidebar`): map carousel + difficulty cards + wood tower sidebar
- All maps unlocked for playability
- **Top-down 3D towers (BTD6-style):** fixed pad + rotating body + attack frames
- Paths end at **BASE fort**; leaks cost RBE lives with LEAK feedback
- Camo/Lead/MOAB warnings one round ahead

## Towers (order)
dart, boomer, tack, sniper, ninja, **water**, **sub**, glue, bomb, ice, wizard, farm, super

## Modes
Easy R40 · Medium R60 · Hard R100 · Expert R100 (hpMul 1.35, fewer lives, lower sell %)

## Maps
**Beginner:** Monkey Meadow · In the Loop · Logs · Candy Falls · Alpine Lake · Spa Pits  
**Intermediate:** Cracked Quarry · Twin Lanes (multi-path)  
**Advanced / Expert tabs:** Coming soon placeholder  

## Combat fixes (2026-07 polish pass)
- **Bomb Shooter visual overhaul:** custom cannon sprites (idle/recoil/pad), cannonball + rocket + frag projectiles, new 8-frame explosion art, muzzle-flash sprite, new shop icon (`ui/btd/tower-bomb-icon.png`)
- Missile path (path 2, tier 2+) renders rockets with smoke trail (`proj.sprite = 'rocket'`, logic stays `projType 'bomb'` so black-bloon immunity is intact)
- Frag path: tier 2+ spawns real shrapnel projectiles (`projType 'frag'`), tier 3+ spawns secondary cluster blasts (`spawnFrags` / `spawnClusterBlast`)
- `canPopPurple` honored for magic/laser/plasma (Archmage / Super can pop purple when flagged)
- Pierce **not** consumed on blocked hits (lead/camo/immune)
- Bomb Blitz uses `projType: 'blitz'` so black bloons are wiped too
- Sniper pierce = bounce chain to other targets
- Freeze draw no longer uses expensive `ctx.filter`
- Auto-start between-round timer scales with game speed

## Balance (same pass)
- Farm / boat trade / sniper supply / necro income nerfed
- Ice: cost 375, slower freeze, pierce 25 base
- Super: cost 3200, fireRate 0.15
- Expert: 50 lives, $400, cashMul 0.65, hpMul 1.35, sell 60%
- Ceramic cash 12; DDT slightly slower; late-game pop cash taper after R50

## Controls extras
- Shift+1–9 place · T targeting · Backspace sell · Space GO · 1–3 speed

## Next ideas
- Real Advanced/Expert maps (obstacles + shorter paths)
- Hero system, tower unlock progression
- Real ability CDs (Blitz / Sabotage / Absolute Zero) on ability button
- Module split of the monolith HTML
- Better audio samples
