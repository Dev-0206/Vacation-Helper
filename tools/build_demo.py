"""Build a static, GitHub Pages friendly demo of Vacation Helper.

    python tools/build_demo.py <output-dir>

The demo shows the real trip math and scenes. It has no server, so there is no live weather.
"""
import json
import os
import shutil
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, ROOT)
from app import DESTINATIONS, VIBES, app  # noqa: E402

out = os.path.abspath(sys.argv[1])
os.makedirs(out, exist_ok=True)
shutil.rmtree(os.path.join(out, "static"), ignore_errors=True)
shutil.copytree(os.path.join(ROOT, "static"), os.path.join(out, "static"))

with app.test_client() as c:
    home = c.get("/").get_data(as_text=True)

home = (home.replace("/static/", "static/").replace('action="/results"', 'action="results.html"')
        .replace('href="/"', 'href="index.html"'))
# vibe chips and counts are filled by demo.js
import re
home = re.sub(r'(<div class="chips">).*?(</div>\s*</fieldset>)', r'<div class="chips" id="vibes">\2', home, flags=re.S)
home = home.replace("We rank 15 US destinations", 'We rank <span id="count-lede">15</span> US destinations')
home = re.sub(r'<script id="dest-data" type="application/json">.*?</script>', '<script id="dest-data" type="application/json">[]</script>', home, flags=re.S)
home = home.replace("<body class=\"home\">", '<body class="home" data-page="home">')
home = home.replace('<script src="static/js/app.js" defer></script>',
                    '<script>window.VH_DEMO=1</script><script src="static/js/data.js"></script><script src="static/js/demo.js"></script><script src="static/js/app.js" defer></script>')
open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(home)

data = {"vibes": VIBES, "dest": [{k: d[k] for k in ("name", "slug", "airport", "hotel", "flight", "best_for", "notes", "vibes")} for d in DESTINATIONS]}
open(os.path.join(out, "static", "js", "data.js"), "w", encoding="utf-8").write("window.VH_DATA=" + json.dumps(data) + ";")

SHELL = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Vacation Helper (demo)</title><meta name="robots" content="noindex">
<link rel="stylesheet" href="static/css/app.css"></head>
<body class="%(cls)s" data-page="%(page)s"><a class="skip" href="#main">Skip to content</a>
<header class="top"><a class="logo" href="index.html"><span class="logo-mark" aria-hidden="true"></span>Vacation Helper</a></header>
<main id="main"></main>
<footer class="foot">Demo: prices are estimates from a sample list, and live weather is only in the full app. Built by Dev Gandhi.</footer>
<script>window.VH_DEMO=1</script><script src="static/js/data.js"></script><script src="static/js/demo.js"></script><script src="static/js/app.js" defer></script></body></html>"""
open(os.path.join(out, "results.html"), "w", encoding="utf-8").write(SHELL % {"cls": "", "page": "results"})
open(os.path.join(out, "destination.html"), "w", encoding="utf-8").write(SHELL % {"cls": "dest", "page": "dest"})
print("built", out)
