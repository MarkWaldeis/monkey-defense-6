# Deploy Monkey Defense 6 to GitHub Pages

## Already done in this folder

- Git repository initialized (`master` branch)
- Initial commit with game + assets (~1.8 MB pack, no `node_modules`)
- `index.html` redirects to the game
- Asset paths work on GitHub Pages

## Option A — GitHub website (easiest)

1. Open https://github.com/new  
2. Create a **public** repo, e.g. `monkey-defense-6` (do **not** add README/license)  
3. In PowerShell:

```powershell
cd "C:\Users\Mark Waldeis\Desktop\Game Prompt"
git remote add origin https://github.com/YOUR_USERNAME/monkey-defense-6.git
git branch -M main
git push -u origin main
```

4. On GitHub: **Settings → Pages → Source: Deploy from a branch → `main` / root → Save**  
5. After ~1 minute open:  
   `https://YOUR_USERNAME.github.io/monkey-defense-6/`

## Option B — GitHub CLI (after `winget install GitHub.cli`)

```powershell
cd "C:\Users\Mark Waldeis\Desktop\Game Prompt"
gh auth login
gh repo create monkey-defense-6 --public --source=. --remote=origin --push
gh api -X PUT repos/:owner/monkey-defense-6/pages -f build_type=legacy -f source[branch]=main -f source[path]=/
```

## Local test (any device on your LAN)

```powershell
cd "C:\Users\Mark Waldeis\Desktop\Game Prompt"
python -m http.server 8766
```

Then: `http://127.0.0.1:8766/` or `http://<your-pc-ip>:8766/`

## After Playwright-Control MCP is connected

Tell Grok: **„Playwright ist verbunden — push auf GitHub und teste das Spiel“**  
Then the agent can drive the browser for login, create the repo, enable Pages, and click-test the game.
