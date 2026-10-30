# First Look Daily: GTA 6 in italiano

Static site for https://mpv-cmd.github.io/firstlookdaily/ and the YouTube description for every video, built from two JSON files. Python 3 only, nothing to install.

Everything in this repository is public. Keep private notes out of `content/`.

## Go live (once)

1. Create an empty **public** repository named `firstlookdaily` (no README, no licence).
2. Put these files in it: push them, or use "uploading an existing file" on the empty repo page and drag in the contents of this folder.
3. Settings → Pages → Build and deployment → Source: **Deploy from a branch** → Branch: `main`, folder: `/docs` → Save.
4. After a minute or two the site is at https://mpv-cmd.github.io/firstlookdaily/.

## Publish a video

1. In `content/videos.json`, find the video's entry (or copy one and give it a new `slug`).
2. Fill in what you verified in your own game:
   - `summary`: one or two sentences
   - `steps`: the short list shown as "In breve" (guides only)
   - `chapters`: optional, e.g. `[{"t": "0:00", "label": "Intro"}, {"t": "1:10", "label": "Le auto"}]`
3. Run `python3 build.py`, then paste `descriptions/<slug>.txt` into the YouTube description. Delete the `[PRIMA DI PUBBLICARE …]` line and any `[…]` placeholder that's left.
4. Once the video is up, set `youtube_id` (the 11 characters after `watch?v=` or `shorts/`) and `"status": "published"`.
5. Run `python3 build.py` again and push. GitHub Pages updates in about a minute.

Guides and articles get a page at `/guide/<slug>.html`; Shorts get a description and a link on the home page, no page. Draft guides show under "In arrivo". The build stops with a clear message if something is missing.

## Files

| Path | What it is |
| --- | --- |
| `content/site.json` | Channel name, links, release date and price |
| `content/videos.json` | One entry per video |
| `static/` | Stylesheet and the self-hosted Archivo font (SIL Open Font License, `static/fonts/OFL.txt`) |
| `build.py` | Builds `docs/` and `descriptions/` |
| `docs/` | The website. Generated: don't edit by hand |
| `descriptions/` | YouTube descriptions. Generated |

No cookies, no trackers, no third-party requests: the font is self-hosted and videos are links, not embeds.

## Own domain (optional)

Set `domain` and `base_url` in `content/site.json`, rebuild, push, then add the domain under Settings → Pages.

Fan site, not affiliated with Rockstar Games or Take-Two Interactive.
