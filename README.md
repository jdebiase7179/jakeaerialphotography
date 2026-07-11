# Dragonfly Real Estate Photography — 2026 rebuild

Static site. No JavaScript, no webfonts, no build step, no dependencies.
Deploy by dropping the folder on any static host.

## Asset manifest

Push files to these exact paths. Layout holds either way — slots render as
neutral gray blocks until the file exists (`object-fit: cover`, so any
resolution works; targets below are guides).

| Path | Used for | Aspect | Target size |
|---|---|---|---|
| `assets/img/hero.jpg` | Top photo | 16:9 | 2400×1350 |
| `assets/img/work/01.jpg` … `12.jpg` | Work grid | 3:2 | 1600×1067 |
| `assets/img/portrait.jpg` | About | 4:5 | 1000×1250 |
| `assets/img/walkthrough-poster.jpg` | Video poster | 16:9 | 1600×900 |
| `assets/img/reel-poster.jpg` | Reel poster | 9:16 | 900×1600 |
| `assets/video/walkthrough.mp4` | Walkthrough sample | 16:9 | H.264, ≤ 25 MB |
| `assets/video/reel.mp4` | Reel sample | 9:16 | H.264, ≤ 15 MB |

The `alt` text on each work slot describes the intended shot type
(exterior, kitchen, drone, twilight, etc.). Reorder freely; update alts to
match the real photos when you push.

## Content notes

- All prices, packages, turnaround claims, and contact info were pulled from
  the live site (dragonflyphotomedia.com, fetched July 2026). Verify with
  Derek before launch — especially the sq-ft tiers, which had copy/paste
  errors in the descriptions on the current site (normalized here).
- Copy is deliberately plain. Rewrite at will; structure doesn't depend on it.
- "Book a shoot" currently points to `mailto:`. Swap to Derek's scheduler
  (the current site has a /book-shoot page) when you know what he uses.
- Not carried over from the old site: blog, rental investment calculator,
  Realtor Branding external link, cart/commerce. Add back if wanted.

- The head carries Open Graph tags, a canonical URL, and LocalBusiness
  JSON-LD, all pointing at `dragonflyphotomedia.com`. If the site launches on
  a different domain, update those absolute URLs. Verify the phone number and
  founding date in the JSON-LD along with the rest of the pulled content.

## SEO note

The current Squarespace site has one page per service (HDR, drone, Matterport,
virtual staging, etc.) ranking on service keywords. This rebuild is one page.
If organic matters, split `#prices` sections back into `/services/*` pages
with this same stylesheet before launch, and 301 the old URLs.
