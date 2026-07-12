# Jake DeBiase — Aerial Photography

Portfolio + booking site. Static HTML/CSS/JS, deployed to GitHub Pages by a
GitHub Action that also builds the photo gallery automatically.

## How Jake adds photos & videos (no code, ever)

Drop image or video files into a category folder and get them onto `main`:

```
photos/
  aerial/
  real-estate/
  events/
  automotive/
```

Within ~2 minutes of a push, the site rebuilds itself: images are resized
for web (originals can be full-size drone shots, even iPhone HEIC), thumbnails
are generated, and the gallery updates with category filter buttons.

Easiest paths, in order:

1. **Tell Claude** — "add these photos to events" with the files. Done.
2. **GitHub web upload** — open the repo → `photos/` → the category folder →
   `Add file → Upload files` → drag images in → `Commit changes`.
3. **Locally** — copy files into `photos/<category>/`, commit, push.

Notes:
- **Videos work too**: `.mp4` / `.mov` clips dropped in the same folders show
  in the gallery with a play button and play in the lightbox. `.mov` is
  auto-converted for browsers. Keep clips under 90 MB (GitHub's limit) —
  export short highlight cuts, not full flights.
- Filenames become captions: `sunset-over-marina.jpg` → "Sunset over marina".
  Camera prefixes like `DJI_0231` are stripped automatically.
- Delete a file from `photos/` and it disappears from the site the same way.
- New folder under `photos/` = new category, automatically.
- Placeholder images show until the first real photo lands, then they're
  dropped from the build automatically.

## Hosting (done — July 2026)

Live at `https://jdebiase7179.github.io/jakeaerialphotography/`.
Repo is public, Pages serves the `gh-pages` branch, and every push to
`main` rebuilds and republishes automatically. If the repo is ever
renamed again, update the URLs in `index.html` (canonical/og),
`sitemap.xml`, and `robots.txt` to match.

## Content TODOs (placeholders in place, swap when known)

- **Email** — `hello@example.com` in `index.html` (2 places). Replace with
  Jake's real booking email.
- **Hero photo** — drop Jake's best shot at `assets/img/hero.jpg` (16:9-ish,
  ~2400px wide). Gradient placeholder shows until then.
- **Portrait** — `assets/img/portrait.jpg` (4:5). Same deal.
- **Location** — copy avoids naming a city. Once Jake knows his service
  area, add it to the hero lede + title/meta description for local SEO.
- ~~FAA Part 107~~ — confirmed July 2026: Jake holds the cert, claim stays.
  (The "insured" claim was removed — Jake isn't insured.)
- **Custom domain** — later, if wanted: buy domain → repo Settings → Pages →
  Custom domain. Then add proper `og:url`/`og:image` absolute URLs.

## Local development

```
pip install pillow && python3 scripts/build_gallery.py
python3 -m http.server -d _site
```

`_site/` is the build output (gitignored). The site itself is just
`index.html`, `styles.css`, `app.js` — no framework, no npm.
