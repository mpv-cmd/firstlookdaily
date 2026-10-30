#!/usr/bin/env python3
"""Build the First Look Daily GTA 6 site and the YouTube descriptions from content/*.json.

  python3 build.py            -> docs/ (the website, served by GitHub Pages) and descriptions/ (one .txt per video)

One entry in content/videos.json per video. To publish a guide: fill summary, steps and
chapters with what you verified in your game, add youtube_id, set status to "published",
run the build and push docs/. Drafts never get a page; draft guides show under "In arrivo".
No cookies, no trackers, no third-party requests: fonts are self-hosted and videos are
links, not embeds.
"""
import html
import json
import os
import re
import shutil
import sys
from datetime import date
from urllib.parse import urlparse

ROOT = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(ROOT, "docs")
DESC = os.path.join(ROOT, "descriptions")
MESI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio",
        "agosto", "settembre", "ottobre", "novembre", "dicembre"]
GIORNI = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"]
FORMAT_LABEL = {"guida": "Guida", "short": "Short", "articolo": "Articolo"}

MARK = ('<svg class="mark" viewBox="0 0 48 48" aria-hidden="true"><path d="M4 16V4h12M32 4h12v12M44 32v12H32M16 44H4V32" '
        'fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="square"/><circle cx="24" cy="24" r="6" fill="#FF2E43"/></svg>')
FAVICON = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'%3E%3Crect width='48' height='48' rx='8' fill='%230D0E14'/%3E"
           "%3Cpath d='M9 19V9h10M29 9h10v10M39 29v10H29M19 39H9V29' fill='none' stroke='%23F5F7FF' stroke-width='4'/%3E"
           "%3Ccircle cx='24' cy='24' r='6' fill='%23FF2E43'/%3E%3C/svg%3E")


def die(msg):
    print("build: " + msg, file=sys.stderr)
    sys.exit(1)


def e(s):
    return html.escape(str(s), quote=True)


def handle(url):
    """'https://www.tiktok.com/@name' or 'https://www.instagram.com/name/' -> '@name'."""
    h = urlparse(url).path.strip("/").split("/")[0]
    return h if h.startswith("@") else "@" + h


def load():
    with open(os.path.join(ROOT, "content", "site.json"), encoding="utf-8") as f:
        site = json.load(f)
    with open(os.path.join(ROOT, "content", "videos.json"), encoding="utf-8") as f:
        videos = json.load(f)
    seen = set()
    for v in videos:
        slug = v.get("slug", "")
        if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", slug):
            die("bad slug: %r" % slug)
        if slug in seen:
            die("duplicate slug: " + slug)
        seen.add(slug)
        if v.get("format") not in FORMAT_LABEL:
            die(slug + ": format must be guida, short or articolo")
        if v.get("date") and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", v["date"]):
            die(slug + ": date must be YYYY-MM-DD or empty")
        yid = v.get("youtube_id", "")
        if yid and not re.fullmatch(r"[A-Za-z0-9_-]{11}", yid):
            die(slug + ": youtube_id must be the 11-character id from the video link")
        if v.get("status") == "published":
            if not v.get("date"):
                die(slug + ": a published entry needs a date")
            if v["format"] != "short" and (not v.get("summary") or not v.get("steps")):
                die(slug + ": a published guide or article needs a summary and steps")
            if v["format"] != "articolo" and not yid:
                die(slug + ": a published video needs its youtube_id")
    return site, videos


def it_date(d, weekday=False):
    if not d:
        return "dopo la storia"
    y, m, dd = (int(x) for x in d.split("-"))
    txt = "%d %s %d" % (dd, MESI[m - 1], y)
    if weekday:
        txt = GIORNI[date(y, m, dd).weekday()] + " " + txt
    return txt


def seconds(ts):
    parts = [int(p) for p in ts.split(":")]
    total = 0
    for p in parts:
        total = total * 60 + p
    return total


def page(site, title, desc, path, body, rel, jsonld=None, og_image=None):
    """rel = the prefix from this page back to the site root ("" at the root, "../" one level down)."""
    url = site["base_url"] + path
    head = [
        '<!doctype html>',
        '<html lang="it">',
        '<head>',
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        '<title>%s</title>' % e(title),
        '<meta name="description" content="%s">' % e(desc),
        '<link rel="canonical" href="%s">' % e(url),
        '<meta property="og:type" content="website">',
        '<meta property="og:locale" content="it_IT">',
        '<meta property="og:site_name" content="%s">' % e(site["name"]),
        '<meta property="og:title" content="%s">' % e(title),
        '<meta property="og:description" content="%s">' % e(desc),
        '<meta property="og:url" content="%s">' % e(url),
    ]
    if og_image:
        head.append('<meta property="og:image" content="%s">' % e(og_image))
    head += [
        '<meta name="theme-color" content="#0D0E14">',
        '<link rel="icon" href="%s">' % FAVICON,
        '<link rel="preload" href="%sstatic/fonts/archivo.woff2" as="font" type="font/woff2" crossorigin>' % rel,
        '<link rel="stylesheet" href="%sstatic/style.css">' % rel,
    ]
    if jsonld:
        head.append('<script type="application/ld+json">%s</script>'
                    % json.dumps(jsonld, ensure_ascii=False).replace("</", "<\\/"))
    head.append('</head>')
    top = ('<body>\n<header class="top"><div class="wrap top-in">'
           '<a class="brand" href="%s">%s<span>%s</span></a><span class="ita">ITA</span></div></header>\n'
           % (rel or "./", MARK, e(site["name"])))
    foot = (
        '<footer class="foot"><div class="wrap">'
        '<p class="foot-links"><a href="%s">YouTube</a> · <a href="%s">TikTok</a> · <a href="%s">Instagram</a></p>'
        '<p>%s è un sito di fan, non affiliato a Rockstar Games o Take-Two Interactive. '
        'Grand Theft Auto e GTA sono marchi dei rispettivi proprietari.</p>'
        '<p>Nessun cookie, nessun tracciamento. Carattere: Archivo (<a href="%sstatic/fonts/OFL.txt">SIL Open Font License</a>).</p>'
        '</div></footer>\n</body>\n</html>\n'
    ) % (e(site["youtube"]), e(site["tiktok"]), e(site["instagram"]), e(site["name"]), rel)
    return "\n".join(head) + "\n" + top + '<main class="wrap">\n' + body + '\n</main>\n' + foot


def entry_card(v, link=True):
    label = FORMAT_LABEL[v["format"]]
    inner = ('<span class="card-date">%s</span><span class="card-title">%s</span><span class="pill pill-%s">%s</span>'
             % (e(it_date(v["date"])), e(v["title"]), e(v["format"]), label))
    if link:
        if v["format"] == "short":
            return '<li><a class="card" href="https://www.youtube.com/shorts/%s">%s</a></li>' % (e(v["youtube_id"]), inner)
        return '<li><a class="card" href="guide/%s.html">%s</a></li>' % (e(v["slug"]), inner)
    return '<li><div class="card card-soon">%s</div></li>' % inner


def build_home(site, videos):
    rel = site["release"]
    published = sorted([v for v in videos if v["status"] == "published"], key=lambda v: v["date"], reverse=True)
    pages_ = [v for v in published if v["format"] != "short"]
    shorts = [v for v in published if v["format"] == "short"]
    soon = [v for v in videos if v["status"] == "draft" and v["format"] == "guida"]
    soon.sort(key=lambda v: v["date"] or "9999")
    body = [
        '<section class="hero">',
        '<p class="kicker">GTA 6 in italiano</p>',
        '<h1>Guide di GTA 6 in italiano, ogni sera.</h1>',
        '<div class="lightbar" aria-hidden="true"></div>',
        '<p class="lede">Soldi, auto, armi e segreti di Vice City. Solo cose provate in gioco, niente spoiler della storia nei titoli.</p>',
        '<p class="cta"><a class="btn btn-main" href="%s">Iscriviti su YouTube</a>'
        '<a class="btn btn-ghost" href="%s">TikTok</a><a class="btn btn-ghost" href="%s">Instagram</a></p>'
        % (e(site["youtube"]), e(site["tiktok"]), e(site["instagram"])),
        '</section>',
        '<a class="release" href="guide/%s.html">' % e(rel["page"]),
        '<span class="release-label">Esce</span>',
        '<span class="release-date">%s</span>' % e(it_date(rel["date"], weekday=True)),
        '<span class="release-meta">%s · %s</span>' % (e(rel["platforms"]), e(rel["price"])),
        '</a>',
        '<h2>Guide</h2>',
        '<ul class="cards">%s</ul>' % "".join(entry_card(v) for v in pages_),
    ]
    if shorts:
        body += ['<h2>Ultimi Shorts</h2>', '<ul class="cards">%s</ul>' % "".join(entry_card(v) for v in shorts[:6])]
    if soon:
        body += ['<h2>In arrivo</h2>', '<ul class="cards">%s</ul>' % "".join(entry_card(v, link=False) for v in soon)]
    jsonld = {"@context": "https://schema.org", "@type": "WebSite", "name": site["name"],
              "url": site["base_url"] + "/", "inLanguage": "it-IT"}
    return page(site, "%s · %s" % (site["name"], site["tagline"]),
                "Guide di GTA 6 in italiano: soldi, auto, armi e segreti di Vice City, provati in gioco. Un video nuovo ogni sera.",
                "/", "\n".join(body), "", jsonld)


def build_entry(site, v):
    yid = v.get("youtube_id", "")
    watch = "https://www.youtube.com/watch?v=" + yid if yid else ""
    body = ['<p class="back"><a href="../">← Tutte le guide</a></p>',
            '<article class="entry">',
            '<p class="meta"><span class="pill pill-%s">%s</span> %s</p>' % (e(v["format"]), FORMAT_LABEL[v["format"]], e(it_date(v["date"]))),
            '<h1>%s</h1>' % e(v["title"]),
            '<div class="lightbar" aria-hidden="true"></div>',
            '<p class="lede">%s</p>' % e(v["summary"])]
    if watch:
        body.append('<a class="watch" href="%s"><span class="play" aria-hidden="true"></span>'
                    '<span><strong>Guarda il video su YouTube</strong><br>Si apre su youtube.com</span></a>' % e(watch))
    body.append('<h2>In breve</h2><ol class="steps">%s</ol>' % "".join("<li>%s</li>" % e(s) for s in v["steps"]))
    if v.get("chapters") and watch:
        items = "".join('<li><a href="%s&amp;t=%ds"><span class="ts">%s</span> %s</a></li>'
                        % (e(watch), seconds(c["t"]), e(c["t"]), e(c["label"])) for c in v["chapters"])
        body.append('<h2>Capitoli</h2><ul class="chapters">%s</ul>' % items)
    if v.get("sources"):
        items = "".join('<li><a href="%s">%s</a></li>' % (e(s["url"]), e(s["label"])) for s in v["sources"])
        body.append('<h2>Fonti</h2><ul class="sources">%s</ul>' % items)
    body.append('<p class="updated">Aggiornato il %s</p>' % e(it_date(v["date"])))
    body.append('<p class="cta"><a class="btn btn-main" href="%s">Un video nuovo ogni sera: iscriviti</a></p>' % e(site["youtube"]))
    body.append('</article>')
    jsonld = None
    og = None
    if yid:
        og = "https://i.ytimg.com/vi/%s/hqdefault.jpg" % yid
        jsonld = {"@context": "https://schema.org", "@type": "VideoObject", "name": v["title"],
                  "description": v["summary"], "thumbnailUrl": og, "uploadDate": v["date"] + "T20:00:00+01:00",
                  "embedUrl": "https://www.youtube.com/embed/" + yid, "inLanguage": "it-IT"}
    else:
        jsonld = {"@context": "https://schema.org", "@type": "Article", "headline": v["title"],
                  "datePublished": v["date"], "inLanguage": "it-IT", "author": {"@type": "Organization", "name": site["name"]}}
    return page(site, "%s · %s" % (v["title"], site["name"]), v["summary"], "/guide/%s.html" % v["slug"],
                "\n".join(body), "../", jsonld, og)


def build_description(site, v):
    lines = []
    if v["status"] == "draft" and v.get("check"):
        lines += ["[PRIMA DI PUBBLICARE: %s Cancella questa riga.]" % v["check"], ""]
    lines += [v["summary"] or "[Una o due frasi: cosa scopre chi guarda.]", ""]
    if v["format"] != "short":
        lines.append("In breve:")
        steps = v["steps"] or ["[Primo passo, verificato nel tuo gioco]", "[Secondo passo]", "[Terzo passo]"]
        lines += ["%d. %s" % (i, s) for i, s in enumerate(steps, 1)]
        lines += ["", "Capitoli:"]
        chapters = v["chapters"] or [{"t": "0:00", "label": "Intro"}, {"t": "[0:20]", "label": "[Primo punto]"},
                                     {"t": "[1:10]", "label": "[Secondo punto]"}]
        lines += ["%s %s" % (c["t"], c["label"]) for c in chapters]
        lines += ["", "Guida scritta: %s/guide/%s.html" % (site["base_url"], v["slug"])]
    if lines[-1]:
        lines.append("")
    lines += ["Ogni sera un video nuovo su GTA 6 in italiano: iscriviti!",
              "TikTok %s · Instagram %s" % (handle(site["tiktok"]), handle(site["instagram"])), "",
              "Canale di fan, non affiliato a Rockstar Games.", "#GTA6 #GTA6ITA"]
    return "\n".join(lines) + "\n"


def main():
    site, videos = load()
    if os.path.isdir(DIST):
        shutil.rmtree(DIST)
    os.makedirs(os.path.join(DIST, "guide"))
    shutil.copytree(os.path.join(ROOT, "static"), os.path.join(DIST, "static"))
    pages = {"/": build_home(site, videos)}
    for v in videos:
        if v["status"] == "published" and v["format"] != "short":
            pages["/guide/%s.html" % v["slug"]] = build_entry(site, v)
    base_path = urlparse(site["base_url"]).path.rstrip("/") + "/"   # 404 is served at any depth: absolute links
    pages["/404.html"] = page(site, "Pagina non trovata · " + site["name"], "Pagina non trovata.", "/404.html",
                              '<section class="hero"><h1>Questa pagina non esiste.</h1>'
                              '<div class="lightbar" aria-hidden="true"></div><p class="lede">'
                              '<a href="%s">Torna alle guide</a></p></section>' % base_path, base_path)
    for path, src in pages.items():
        out = os.path.join(DIST, "index.html" if path == "/" else path.lstrip("/"))
        with open(out, "w", encoding="utf-8") as f:
            f.write(src)
    urls = [p for p in pages if p != "/404.html"]
    with open(os.path.join(DIST, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        for p in urls:
            f.write("  <url><loc>%s%s</loc></url>\n" % (site["base_url"], p))
        f.write("</urlset>\n")
    with open(os.path.join(DIST, "robots.txt"), "w", encoding="utf-8") as f:
        f.write("User-agent: *\nAllow: /\nSitemap: %s/sitemap.xml\n" % site["base_url"])
    if site.get("domain"):                                           # only for a custom domain
        with open(os.path.join(DIST, "CNAME"), "w", encoding="utf-8") as f:
            f.write(site["domain"] + "\n")
    with open(os.path.join(DIST, ".nojekyll"), "w") as f:
        f.write("")
    if os.path.isdir(DESC):
        shutil.rmtree(DESC)
    os.makedirs(DESC)
    for v in videos:
        if v["format"] == "articolo":
            continue
        with open(os.path.join(DESC, v["slug"] + ".txt"), "w", encoding="utf-8") as f:
            f.write(build_description(site, v))
    print("built %d pages, %d descriptions" % (len(pages), len(os.listdir(DESC))))


if __name__ == "__main__":
    main()
