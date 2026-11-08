#!/usr/bin/env python3
"""Builds the static website (GitHub Pages) from this repository's Markdown. Needs Python 3.8+ and pandoc.

  python3 site/build.py                       # writes ./_site
  SITE_URL=https://example.com python3 site/build.py --out public

Every .md file becomes a page with a clean URL (README.md -> its folder, other.md -> other/). The build adds:
title and meta description, canonical URL, Open Graph tags, JSON-LD (WebSite, TechArticle, BreadcrumbList and
FAQPage), a sitemap, robots.txt, llms.txt and a 404 page. Links to code and data files point to GitHub.
"""
import argparse
import datetime
import html
import json
import os
import posixpath
import re
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE_URL = os.environ.get("SITE_URL", "https://erikthiart.github.io/airtime-api").rstrip("/")
REPO_URL = "https://github.com/ErikThiart/airtime-api"
BRANCH = "master"
SKIP_DIRS = {".git", ".github", "site", "_site", "node_modules"}
SITE_NAME = "South African Airtime and Prepaid Electricity API Guides"
TITLE_SUFFIX = "Airtime & Electricity APIs"

# Hand-written meta descriptions for the pages people land on from search (about 155 characters each).
DESCRIPTIONS = {
    "README.md": "Guides, references and tested sample code in 13 languages for South African airtime, data, SMS and prepaid electricity APIs: Freepaid, SIMcloud and MCP.",
    "prepaid-electricity/README.md": "Buy prepaid electricity from code in South Africa: check a meter, place an order, poll for the token. Working examples in 12 languages, tested on a mock server.",
    "prepaid-electricity/how-it-works.md": "How prepaid electricity vending works through an API: STS tokens, key-change tokens, the service fee formula, order states and safe handling of uncertain results.",
    "prepaid-electricity/faq.md": "Answers about buying prepaid electricity through an API in South Africa: meter checks, R55 to R1000 limits, fees, key-change tokens, timeouts and duplicate purchases.",
    "prepaid-electricity/recipes.md": "Practical designs for prepaid electricity: landlord and tenant tools, estate portals, support desks, WooCommerce and month-end reconciliation.",
    "freepaid-api/README.md": "Freepaid SOAP airtime API guide: PINLESS and PINNED airtime and data for Vodacom, MTN, Cell C and Telkom, with samples in 13 languages and a local mock server.",
    "simcloud-api/README.md": "SIMcloud REST API guide: airtime, data bundles, SMS, VAS vouchers and prepaid electricity in South Africa, with samples in 13 languages and a mock server.",
    "simcloud-mcp/README.md": "Connect Claude, ChatGPT, Codex, Cursor or VS Code to SIMcloud with MCP: send airtime, data, SMS and electricity from an AI assistant, with safe approval rules.",
    "languages/README.md": "Pick your language for working South African airtime, data, SMS and prepaid electricity API examples: Java, C#, Python, Go, Node.js, PHP, Ruby, Swift and more.",
}

NAV = [
    ("Home", "", ""),
    ("Freepaid API", "freepaid-api/", "freepaid-api"),
    ("SIMcloud API", "simcloud-api/", "simcloud-api"),
    ("SIMcloud MCP", "simcloud-mcp/", "simcloud-mcp"),
    ("Prepaid electricity", "prepaid-electricity/", "prepaid-electricity"),
    ("Languages", "languages/", "languages"),
]


def collect_pages():
    pages = {}
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS and not d.startswith("."))
        for name in sorted(filenames):
            if not name.endswith(".md"):
                continue
            rel = os.path.relpath(os.path.join(dirpath, name), ROOT).replace(os.sep, "/")
            if rel.upper() == "LICENSE.MD":
                continue
            pages[rel] = url_path(rel)
    return pages


def url_path(rel_md):
    """README.md -> '' or 'dir/'; docs/x.md -> 'docs/x/'."""
    d, base = posixpath.split(rel_md)
    if base.lower() == "readme.md":
        return d + "/" if d else ""
    return posixpath.join(d, base[:-3]) + "/"


def strip_md(text):
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"[`*_]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def title_and_description(md):
    title = None
    desc = None
    in_code = False
    for line in md.splitlines():
        if line.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        if title is None and line.startswith("# "):
            title = strip_md(line[2:])
            continue
        if title and desc is None:
            s = line.strip()
            if len(s) > 60 and not s.startswith(("[", "|", "-", ">", "#", "`", "<", "!", "1.", "*")):
                desc = strip_md(s)
                break
    desc = desc or title or SITE_NAME
    if len(desc) > 158:
        desc = desc[:155].rsplit(" ", 1)[0].rstrip(",;:") + "..."
    return title or SITE_NAME, desc


def rewrite_links(fragment, rel_md, pages, dir_urls):
    here_url = pages[rel_md]
    here_dir = posixpath.dirname(rel_md)

    def target_for(href):
        if re.match(r"^(https?:|mailto:|tel:|#)", href):
            return href
        path, _, anchor = href.partition("#")
        anchor = "#" + anchor if anchor else ""
        if not path:
            return href
        resolved = posixpath.normpath(posixpath.join(here_dir, path))
        if resolved in pages:
            return relative(here_url, pages[resolved]) + anchor
        if resolved + "/README.md" in pages:
            return relative(here_url, pages[resolved + "/README.md"]) + anchor
        full = os.path.join(ROOT, resolved)
        kind = "tree" if os.path.isdir(full) else "blob"
        return f"{REPO_URL}/{kind}/{BRANCH}/{resolved}"

    def sub(m):
        return f'href="{html.escape(html.unescape(target_for(html.unescape(m.group(1)))), quote=True)}"'

    return re.sub(r'href="([^"]*)"', sub, fragment)


def relative(from_url, to_url):
    rel = posixpath.relpath("/" + to_url if to_url else "/", "/" + from_url if from_url else "/")
    rel = rel.rstrip("/")
    return (rel + "/") if rel and rel != "." else "./"


def render_markdown(md):
    result = subprocess.run(
        ["pandoc", "-f", "gfm+gfm_auto_identifiers", "-t", "html5", "--wrap=none", "--no-highlight"],
        input=md, capture_output=True, text=True, check=True)
    out = result.stdout
    out = re.sub(r"<table", '<div class="table-wrap"><table', out)
    out = out.replace("</table>", "</table></div>")
    return out


def breadcrumbs(url):
    parts = [p for p in url.split("/") if p]
    crumbs = [{"@type": "ListItem", "position": 1, "name": "Home", "item": SITE_URL + "/"}]
    acc = ""
    for i, p in enumerate(parts, start=2):
        acc += p + "/"
        crumbs.append({"@type": "ListItem", "position": i, "name": p.replace("-", " ").capitalize(), "item": f"{SITE_URL}/{acc}"})
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": crumbs}


def faq_jsonld(md):
    """Questions are '## ' headings, answers the text until the next heading. Code blocks are skipped."""
    items, q, buf, in_code = [], None, [], False
    for line in md.splitlines() + ["## END"]:
        if line.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        if line.startswith("## "):
            if q and buf:
                answer = strip_md(" ".join(buf))
                if answer:
                    items.append({"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": answer}})
            q, buf = strip_md(line[3:]), []
        elif q:
            buf.append(line)
    return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": items} if items else None


def page_html(rel_md, md, body, pages, last_mod):
    url = pages[rel_md]
    canonical = f"{SITE_URL}/{url}"
    title, desc = title_and_description(md)
    desc = DESCRIPTIONS.get(rel_md, desc)
    full_title = f"{title} | {TITLE_SUFFIX}" if len(title) + len(TITLE_SUFFIX) + 3 <= 66 else title
    root = "../" * len([p for p in url.split("/") if p]) or "./"
    top = url.split("/")[0] if url else ""

    ld = []
    if not url:
        ld.append({"@context": "https://schema.org", "@type": "WebSite", "name": SITE_NAME, "url": SITE_URL + "/", "description": desc})
    else:
        ld.append({"@context": "https://schema.org", "@type": "TechArticle", "headline": title[:110], "description": desc, "url": canonical,
                   "dateModified": last_mod, "inLanguage": "en-ZA",
                   "author": {"@type": "Person", "name": "Erik Thiart", "url": "https://github.com/ErikThiart"},
                   "isPartOf": {"@type": "WebSite", "name": SITE_NAME, "url": SITE_URL + "/"}})
        ld.append(breadcrumbs(url))
    if rel_md == "prepaid-electricity/faq.md":
        faq = faq_jsonld(md)
        if faq:
            ld.append(faq)
    ld_tags = "\n".join('<script type="application/ld+json">' + json.dumps(x, ensure_ascii=False).replace("</", "<\\/") + "</script>" for x in ld)

    nav_items = []
    for label, href, key in NAV:
        current = ' aria-current="page"' if (key == top and (key or not url)) else ""
        nav_items.append('<a href="%s%s"%s>%s</a>' % (root, href, current, html.escape(label)))
    nav = "".join(nav_items)
    e = html.escape
    return f"""<!doctype html>
<html lang="en-ZA">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(full_title)}</title>
<meta name="description" content="{e(desc, quote=True)}">
<link rel="canonical" href="{e(canonical)}">
<meta name="robots" content="index, follow, max-snippet:-1">
<meta property="og:type" content="article">
<meta property="og:site_name" content="{e(SITE_NAME)}">
<meta property="og:title" content="{e(title, quote=True)}">
<meta property="og:description" content="{e(desc, quote=True)}">
<meta property="og:url" content="{e(canonical)}">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{e(title, quote=True)}">
<meta name="twitter:description" content="{e(desc, quote=True)}">
<link rel="icon" href="{root}assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{root}assets/site.css">
{ld_tags}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="site-header">
  <a class="brand" href="{root}">Airtime &amp; electricity API guides</a>
  <nav aria-label="Main">{nav}<a href="{REPO_URL}">GitHub</a></nav>
</header>
<main id="main">
<article>
{body}
</article>
</main>
<footer class="site-footer">
  <p>Guides and sample code for the Freepaid airtime API, the SIMcloud API and the SIMcloud MCP server, maintained by <a href="https://github.com/ErikThiart">Erik Thiart</a>. MIT licence. Freepaid and SIMcloud are products of FREEPAID (PTY) LTD. The mock servers are not the real services: confirm behaviour with the provider.</p>
  <p><a href="{REPO_URL}">View on GitHub</a> · <a href="{REPO_URL}/blob/{BRANCH}/{e(rel_md)}">Edit this page</a></p>
</footer>
</body>
</html>
"""


def last_modified(rel_md):
    try:
        out = subprocess.run(["git", "-C", ROOT, "log", "-1", "--format=%cs", "--", rel_md], capture_output=True, text=True).stdout.strip()
        if out:
            return out
    except OSError:
        pass
    return datetime.date.today().isoformat()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "_site"))
    args = ap.parse_args()
    if shutil.which("pandoc") is None:
        sys.exit("pandoc is required (https://pandoc.org/installing.html)")

    out = os.path.abspath(args.out)
    if os.path.isdir(out):
        shutil.rmtree(out)
    os.makedirs(os.path.join(out, "assets"))
    shutil.copy(os.path.join(ROOT, "site", "site.css"), os.path.join(out, "assets", "site.css"))
    shutil.copy(os.path.join(ROOT, "site", "favicon.svg"), os.path.join(out, "assets", "favicon.svg"))
    open(os.path.join(out, ".nojekyll"), "w").close()

    pages = collect_pages()
    dir_urls = set(pages.values())
    sitemap, listing = [], []
    for rel_md, url in sorted(pages.items(), key=lambda kv: kv[1]):
        with open(os.path.join(ROOT, rel_md), encoding="utf-8") as fh:
            md = fh.read()
        body = rewrite_links(render_markdown(md), rel_md, pages, dir_urls)
        mod = last_modified(rel_md)
        dest = os.path.join(out, url, "index.html")
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "w", encoding="utf-8") as fh:
            fh.write(page_html(rel_md, md, body, pages, mod))
        sitemap.append((SITE_URL + "/" + url, mod))
        title, desc = title_and_description(md)
        listing.append((title, SITE_URL + "/" + url, DESCRIPTIONS.get(rel_md, desc)))

    with open(os.path.join(out, "sitemap.xml"), "w") as fh:
        fh.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        for loc, mod in sitemap:
            fh.write(f"  <url><loc>{html.escape(loc)}</loc><lastmod>{mod}</lastmod></url>\n")
        fh.write("</urlset>\n")
    with open(os.path.join(out, "robots.txt"), "w") as fh:
        fh.write(f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n")
    with open(os.path.join(out, "llms.txt"), "w") as fh:
        fh.write(f"# {SITE_NAME}\n\n> Guides, references and tested sample code in 13 languages for the Freepaid SOAP airtime API, the SIMcloud REST API (airtime, data, SMS, VAS vouchers, prepaid electricity) and the SIMcloud MCP server, for South Africa.\n\n## Pages\n\n")
        for title, loc, desc in listing:
            fh.write(f"- [{title}]({loc}): {desc}\n")
    with open(os.path.join(out, "404.html"), "w", encoding="utf-8") as fh:
        fh.write(page_html("README.md", "# Page not found\n\nThat page does not exist. Try the [home page](./) or search the [repository](" + REPO_URL + ").\n",
                           '<h1>Page not found</h1><p>That page does not exist. Try the <a href="' + SITE_URL + '/">home page</a> or the <a href="' + REPO_URL + '">repository on GitHub</a>.</p>',
                           {"README.md": ""}, datetime.date.today().isoformat()).replace('<meta name="robots" content="index, follow, max-snippet:-1">', '<meta name="robots" content="noindex">'))
    print(f"built {len(pages)} pages into {out}")


if __name__ == "__main__":
    main()
