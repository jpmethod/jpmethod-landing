#!/usr/bin/env python3
"""Generate the static workbook product pages and sitemap from the catalogue.

Each workbook in assets/catalog.json gets a thin shell at
workbooks/<slug>/index.html carrying its own title, meta description,
canonical URL and OpenGraph tags; the page body is rendered client-side by
assets/workbook.js from the same catalogue. Shell directories for workbooks
no longer in the catalogue are removed.

Run from anywhere with any Python 3 after each catalogue update:

    python scripts/generate_workbook_pages.py
"""

import json
import re
import shutil
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://jpmethod.org"
DEFAULT_OG_IMAGE = SITE + "/assets/samples/european-geography/sample_1.png"
FAVICON = "/assets/favicon.svg"

PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en" data-workbook="{slug}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{meta_description}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="website">
<meta property="og:url" content="{canonical}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{meta_description}">
<meta property="og:image" content="{og_image}">
<meta name="theme-color" content="#0b5cad">
<link rel="icon" href="{favicon}">
<link rel="stylesheet" href="/assets/site.css">
</head>
<body>

<header class="band slim">
  <div class="wrap">
    <div class="top">
      <a href="/" class="brandlogo" aria-label="JP Method — home"></a>
    </div>
  </div>
</header>

<main class="wrap" id="workbookMain">
  <p class="loading">Loading the workbook&hellip;</p>
  <noscript>
    <header class="prodhead">
      <h1>{name}</h1>
      <p class="desc">{description}</p>
    </header>
    <p style="margin-top:18px">{noscript_links}</p>
    <p style="margin-top:10px"><a href="/">&larr; All workbooks</a></p>
  </noscript>
</main>

<footer>
  <div class="wrap">
    <span>&copy; <span id="year"></span> JP Method &middot; Free to print and share for home and classroom use.</span>
    <span class="stamp">Catalogue updated <span id="lastUpdated"></span></span>
  </div>
</footer>

<div class="modal" id="imageModal" role="dialog" aria-modal="true" aria-label="Worksheet preview">
  <button class="mclose" id="mClose" type="button" aria-label="Close preview">&times;</button>
  <button class="mprev" id="mPrev" type="button" aria-label="Previous page">&lsaquo;</button>
  <img id="modalImage" alt="Worksheet sample page">
  <button class="mnext" id="mNext" type="button" aria-label="Next page">&rsaquo;</button>
  <div class="mcount" id="mCount"></div>
</div>

<script src="/assets/workbook.js"></script>
</body>
</html>
"""

SITEMAP_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{urls}
</urlset>
"""


def slugify(name):
    """Mirror of the site's JS slug(): lowercase, non-alphanumerics to dashes."""
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def all_domains(catalog):
    domains = []
    for section in catalog.get("sections", []) + catalog.get("special_sections", []):
        domains.extend(section.get("domains", []))
    domains.extend(catalog.get("domains", []))
    return domains


def noscript_links(domain):
    links = []
    if domain.get("pdf_path_a4"):
        links.append('<a href="/%s" download>Download the A4 booklet (%s MB)</a>'
                     % (escape(domain["pdf_path_a4"], quote=True),
                        domain.get("pdf_size_a4_mb", "?")))
    links.append('<a href="/%s" download>Download the sequential PDF (%s MB)</a>'
                 % (escape(domain["pdf_path"], quote=True),
                    domain.get("pdf_size_mb", "?")))
    return " &middot; ".join(links)


def build_page(domain, slug):
    name = domain["name"]
    description = domain.get("description", "")
    meta = ("%s. Free printable PDF workbook with answer keys — download the "
            "whole book as an A4 booklet, or single chapters." % description)
    return PAGE_TEMPLATE.format(
        slug=escape(slug, quote=True),
        title=escape("%s — free printable workbook | JP Method" % name),
        meta_description=escape(meta, quote=True),
        canonical="%s/workbooks/%s/" % (SITE, slug),
        og_image=(SITE + "/" + domain["samples"][0]) if domain.get("samples")
                 else DEFAULT_OG_IMAGE,
        favicon=FAVICON,
        name=escape(name),
        description=escape(description),
        noscript_links=noscript_links(domain),
    )


def main():
    with open(ROOT / "assets" / "catalog.json", encoding="utf-8") as f:
        catalog = json.load(f)

    workbooks_dir = ROOT / "workbooks"
    workbooks_dir.mkdir(exist_ok=True)

    slugs = set()
    for domain in all_domains(catalog):
        slug = domain.get("slug") or slugify(domain["name"])
        slugs.add(slug)
        page_dir = workbooks_dir / slug
        page_dir.mkdir(exist_ok=True)
        (page_dir / "index.html").write_text(build_page(domain, slug),
                                             encoding="utf-8", newline="\n")
        print("  + workbooks/%s/" % slug)

    for stale in sorted(workbooks_dir.iterdir()):
        if stale.is_dir() and stale.name not in slugs:
            shutil.rmtree(stale)
            print("  - removed stale workbooks/%s/" % stale.name)

    urls = ["  <url><loc>%s/</loc></url>" % SITE]
    urls += ["  <url><loc>%s/workbooks/%s/</loc></url>" % (SITE, s)
             for s in sorted(slugs)]
    (ROOT / "sitemap.xml").write_text(
        SITEMAP_TEMPLATE.format(urls="\n".join(urls)), encoding="utf-8", newline="\n")
    print("  + sitemap.xml (%d URLs)" % (len(slugs) + 1))


if __name__ == "__main__":
    main()
