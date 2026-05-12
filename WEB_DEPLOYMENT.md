# Web Version — Setup & Deployment Guide

The game has both a terminal version (run `python main.py`) and a **web version**
that runs in any modern browser via PyScript. This document walks you through
testing it locally and deploying it free on GitHub Pages.

---

## Quick test on your own laptop

The web version is a static site (HTML + CSS + JS + Python files). Browsers
block `file://` access to neighbouring files for security, so **double-clicking
`index.html` will not work** — you need a local web server.

The simplest way:

```bash
cd usyd_survival
python -m http.server 8000
```

Then open `http://localhost:8000` in Chrome, Firefox, or Safari.

The first load takes 5–10 seconds (downloading Pyodide, the Python WebAssembly
runtime). After that, the game is fully cached and instant.

---

## Deploy free on GitHub Pages

GitHub Pages gives you a public URL like `https://yourname.github.io/usyd-survival/`
that you can paste directly into your Padlet post.

### Step 1 — Create the GitHub repo

1. Go to https://github.com/new while logged in.
2. Repository name: `usyd-survival` (or whatever you like).
3. Set it **Public** (Pages on free accounts requires public).
4. **Don't** initialise with a README (you have one already).
5. Click "Create repository".

### Step 2 — Push your code

GitHub will show you commands. From inside `usyd_survival/`:

```bash
git init
git add .
git commit -m "Initial COMP9001 final project"
git branch -M main
git remote add origin https://github.com/<your-username>/usyd-survival.git
git push -u origin main
```

If `git` isn't installed, see https://git-scm.com/downloads.

### Step 3 — Enable GitHub Pages

1. On your new repo, click **Settings** → **Pages** (left sidebar).
2. Under "Source", choose **Deploy from a branch**.
3. Branch: `main`, Folder: `/ (root)`. Save.
4. Wait 30–60 seconds. GitHub gives you a URL at the top of the Pages settings,
   typically `https://<username>.github.io/usyd-survival/`.

That URL is your live game. Paste it into your Padlet post!

### Step 4 — Iterate

Any time you push new commits to `main`, GitHub Pages rebuilds within a minute.

```bash
# After making changes to events.json or game balance:
git add -A
git commit -m "Tune cafe job pay rate"
git push
```

---

## Padlet integration tips

When you create your Padlet post:

- **Title:** "USYD Survival Simulator — Click to Play in Browser!"
- **Image:** Take a screenshot of the running game (the title screen or a
  filled-in mid-semester dashboard look great).
- **Description (~100 words):** see `PADLET_AND_PRESENTATION.md`.
- **Link / Attachment:** paste your GitHub Pages URL. Padlet will turn it
  into a clickable preview card.

This is a **huge** advantage over Padlet posts that just show static images of
their projects — yours is the only one anyone can play with one click. Highly
likely to win the tutorial vote.

---

## Troubleshooting

### "Python failed to load" after 30 seconds
- Confirm you're serving via HTTP (`python -m http.server`), not opening
  the file directly with `file://...`.
- Check your browser console (F12 → Console tab) for errors.
- Try a fresh tab — sometimes Pyodide caches break.

### Save file won't load
- Saves are stored in `localStorage`, scoped to the URL. If you switch from
  `localhost:8000` to GitHub Pages, your local saves don't transfer.
- Clear `localStorage` via DevTools → Application → Local Storage if a
  save becomes corrupted.

### Game looks different on GitHub Pages vs local
- This usually means the browser is showing a stale cached `style.css` or
  `app.js`. Hard-refresh with **Ctrl+F5** / **Cmd+Shift+R**.

### Tutor's laptop is corporate / blocks PyScript CDN
- Some institutional networks block `pyscript.net` or `pyodide` CDN. As a
  fallback, you can still demo the **terminal version** (`python main.py`).
- Or: download PyScript locally and host it alongside your files. See
  https://pyscript.net for the offline bundle option.

---

## Submission checklist (combined Ed + Padlet)

- [ ] **Ed Code Submission slide**: zip the `usyd_survival/` folder (excluding
      `saves/` and `__pycache__/`) and upload. Include:
      - `main.py` (terminal entry)
      - `index.html`, `style.css`, `app.js`, `pyscript.toml` (web entry)
      - `game/` (all Python modules — terminal + web engine)
      - `data/events.json`
      - `requirements.txt`, `README.md`
- [ ] **Padlet post**: title + image + ~100-word description + GitHub Pages URL
- [ ] **3-min presentation rehearsed** (see `PADLET_AND_PRESENTATION.md`)
- [ ] **Tutor approval received** (week 8 deadline)
