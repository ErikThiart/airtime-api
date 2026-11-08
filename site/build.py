#!/usr/bin/env python3
"""Builds the static website (GitHub Pages) from this repository's Markdown. Needs Python 3.8+ and pandoc.

  python3 site/build.py                       # writes ./_site
  SITE_URL=https://example.com python3 site/build.py --out public

Every .md file becomes a page with a clean URL (README.md -> its folder, other.md -> other/). The home page
comes from site/home.html. The design follows shadcn/ui's default theme (see site/site.css). The build adds:
sidebar, on-this-page nav, previous/next links, search index, title and meta description, canonical URL,
Open Graph tags, JSON-LD (WebSite, TechArticle, BreadcrumbList, FAQPage), sitemap, robots.txt, llms.txt, 404.
Links to code and data files point to GitHub.
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
BRAND = "Airtime &amp; Electricity APIs"

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

LANG_ORDER = ["java", "csharp", "python", "go", "nodejs", "typescript", "php", "ruby", "swift", "powershell", "bash-curl", "oracle-plsql", "sap-abap"]
UC = "simcloud-mcp/use-cases/"

# (folder, sidebar heading, ordered pages). A string starting with "#" is a sub-heading.
SECTIONS = [
    ("simcloud-api", "SIMcloud API", [
        "simcloud-api/README.md", "simcloud-api/docs/getting-started.md", "simcloud-api/docs/endpoints.md",
        "simcloud-api/docs/orders-and-polling.md", "simcloud-api/docs/electricity.md", "simcloud-api/docs/errors.md",
        "simcloud-api/docs/language-notes.md", "simcloud-api/docs/security-and-operations.md", "simcloud-api/openapi/README.md"]),
    ("freepaid-api", "Freepaid API", [
        "freepaid-api/README.md", "freepaid-api/docs/getting-started.md", "freepaid-api/docs/operations.md",
        "freepaid-api/docs/pinless-vs-pinned.md", "freepaid-api/docs/error-codes.md", "freepaid-api/docs/soap-rpc-encoded.md",
        "freepaid-api/docs/language-guide.md", "freepaid-api/docs/security-and-operations.md",
        "freepaid-api/docs/go-live-checklist.md", "freepaid-api/docs/troubleshooting.md", "freepaid-api/docs/original-vendor-guide.md"]),
    ("simcloud-mcp", "SIMcloud MCP", [
        "simcloud-mcp/README.md", "simcloud-mcp/docs/connect-clients.md", "simcloud-mcp/docs/authentication.md",
        "simcloud-mcp/docs/tools-reference.md", "simcloud-mcp/docs/safety-and-guardrails.md", "simcloud-mcp/docs/build-a-client.md",
        "#Use cases", UC + "README.md"] + [UC + n for n in (
            "01-morning-wallet-check.md", "02-support-order-lookup.md", "03-reward-airtime.md", "04-bulk-recharge-from-spreadsheet.md",
            "05-data-bundle-advisor.md", "06-electricity-for-tenants.md", "07-voucher-gifts.md", "08-sms-updates.md",
            "09-month-end-reconciliation.md", "10-build-an-integration.md")] + ["#Reference", "simcloud-mcp/config/README.md"]),
    ("prepaid-electricity", "Prepaid electricity", [
        "prepaid-electricity/README.md", "prepaid-electricity/how-it-works.md", "prepaid-electricity/faq.md", "prepaid-electricity/recipes.md"]),
    ("languages", "Languages", ["languages/README.md"] + ["languages/airtime-api-%s.md" % s for s in LANG_ORDER]),
]

LABELS = {
    "simcloud-api/README.md": "Overview", "freepaid-api/README.md": "Overview", "simcloud-mcp/README.md": "Overview",
    "prepaid-electricity/README.md": "Guide", "languages/README.md": "All languages",
    "simcloud-api/docs/getting-started.md": "Getting started", "freepaid-api/docs/getting-started.md": "Getting started",
    "freepaid-api/docs/soap-rpc-encoded.md": "Hand-built SOAP envelope", "freepaid-api/docs/original-vendor-guide.md": "Original vendor guide",
    "freepaid-api/docs/troubleshooting.md": "Troubleshooting", "simcloud-api/openapi/README.md": "OpenAPI contract",
    "simcloud-api/docs/electricity.md": "Electricity", "prepaid-electricity/faq.md": "FAQ",
    "prepaid-electricity/how-it-works.md": "How it works", "prepaid-electricity/recipes.md": "Recipes",
    "simcloud-mcp/docs/build-a-client.md": "Build a client", "simcloud-mcp/config/README.md": "Client configuration",
    UC + "README.md": "All use cases",
    UC + "02-support-order-lookup.md": "2. Support order lookup", UC + "03-reward-airtime.md": "3. Reward airtime",
    UC + "04-bulk-recharge-from-spreadsheet.md": "4. Bulk recharge", UC + "06-electricity-for-tenants.md": "6. Electricity for tenants",
    UC + "08-sms-updates.md": "8. SMS updates", UC + "10-build-an-integration.md": "10. Build an integration",
}
LANG_NAMES = {"bash-curl": "Bash and cURL", "csharp": "C# and .NET", "nodejs": "Node.js", "oracle-plsql": "Oracle PL/SQL", "sap-abap": "SAP ABAP",
              "java": "Java", "python": "Python", "go": "Go", "typescript": "TypeScript", "php": "PHP", "ruby": "Ruby", "swift": "Swift", "powershell": "PowerShell"}
for _s, _n in LANG_NAMES.items():
    LABELS["languages/airtime-api-%s.md" % _s] = _n

TOP_NAV = [("Docs", "simcloud-api/docs/getting-started/", "simcloud-api"), ("Freepaid", "freepaid-api/", "freepaid-api"),
           ("MCP", "simcloud-mcp/", "simcloud-mcp"), ("Electricity", "prepaid-electricity/", "prepaid-electricity"), ("Languages", "languages/", "languages")]

SVG = 'width="%d" height="%d" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"'
ICON = {
    "search": '<svg %s><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>' % (SVG % (16, 16)),
    "menu": '<svg %s><path d="M4 6h16M4 12h16M4 18h16"/></svg>' % (SVG % (18, 18)),
    "moon": '<svg class="icon-moon" %s><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/></svg>' % (SVG % (16, 16)),
    "sun": '<svg class="icon-sun" %s><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2m-7.07-2.93 1.41-1.41m11.32-11.32 1.41-1.41M2 12h2m16 0h2M6.34 6.34 4.93 4.93m14.14 14.14-1.41-1.41"/></svg>' % (SVG % (16, 16)),
    "github": '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M12 .5a11.5 11.5 0 0 0-3.64 22.41c.58.1.79-.25.79-.56v-2c-3.2.7-3.88-1.37-3.88-1.37-.52-1.33-1.28-1.69-1.28-1.69-1.04-.71.08-.7.08-.7 1.15.08 1.76 1.19 1.76 1.19 1.03 1.76 2.69 1.25 3.35.96.1-.75.4-1.25.73-1.54-2.55-.29-5.24-1.28-5.24-5.69 0-1.26.45-2.28 1.19-3.09-.12-.29-.52-1.46.11-3.05 0 0 .97-.31 3.17 1.18a11 11 0 0 1 5.77 0c2.2-1.49 3.17-1.18 3.17-1.18.63 1.59.23 2.76.11 3.05.74.81 1.19 1.83 1.19 3.09 0 4.42-2.69 5.39-5.25 5.68.41.36.78 1.06.78 2.14v3.17c0 .31.21.67.8.56A11.5 11.5 0 0 0 12 .5Z"/></svg>',
    "bolt": '<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M13 2 4 14h7l-1 8 9-12h-7l1-8Z"/></svg>',
}


# ---------------------------------------------------------------- pages and text helpers
def collect_pages():
    pages = {}
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS and not d.startswith("."))
        for name in sorted(filenames):
            if name.endswith(".md") and name.upper() != "LICENSE.MD":
                rel = os.path.relpath(os.path.join(dirpath, name), ROOT).replace(os.sep, "/")
                pages[rel] = url_path(rel)
    return pages


def url_path(rel_md):
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
    title, desc, in_code = None, None, False
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


def relative(from_url, to_url):
    rel = posixpath.relpath("/" + to_url if to_url else "/", "/" + from_url if from_url else "/").rstrip("/")
    return (rel + "/") if rel and rel != "." else "./"


def rewrite_links(fragment, rel_md, pages):
    here_url, here_dir = pages[rel_md], posixpath.dirname(rel_md)

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
        kind = "tree" if os.path.isdir(os.path.join(ROOT, resolved)) else "blob"
        return f"{REPO_URL}/{kind}/{BRANCH}/{resolved}"

    return re.sub(r'href="([^"]*)"', lambda m: 'href="%s"' % html.escape(html.unescape(target_for(html.unescape(m.group(1)))), quote=True), fragment)


def render_markdown(md):
    out = subprocess.run(["pandoc", "-f", "gfm+gfm_auto_identifiers", "-t", "html5", "--wrap=none", "--highlight-style=pygments"],
                         input=md, capture_output=True, text=True, check=True).stdout
    out = out.replace("<table", '<div class="table-wrap"><table').replace("</table>", "</table></div>")
    # status cells become badges
    out = re.sub(r"<td>(Yes|Tested)</td>", r'<td><span class="badge badge-ok">\1</span></td>', out)
    out = re.sub(r"<td>(Yes \([^<]*\))</td>", r'<td><span class="badge badge-ok">\1</span></td>', out)
    out = re.sub(r"<td>(Tested in CI[^<]*)</td>", r'<td><span class="badge badge-ok">\1</span></td>', out)
    out = re.sub(r"<td>(?:Not executed here|Not executed|<strong>Not executed</strong>)</td>", '<td><span class="badge badge-warn">Not executed</span></td>', out)
    return out


def toc_html(body):
    items = re.findall(r'<h([23]) id="([^"]+)">(.*?)</h\1>', body, flags=re.S)
    if len(items) < 3:
        return ""
    lis = "".join('<li class="l%s"><a href="#%s">%s</a></li>' % (lvl, i, re.sub(r"<[^>]+>", "", t)) for lvl, i, t in items)
    return '<nav class="toc" aria-label="On this page"><p>On this page</p><ul>%s</ul></nav>' % lis


# ---------------------------------------------------------------- navigation model
def build_nav(pages, titles):
    """Returns sections: list of (key, heading, [(rel_md or '#', label)])."""
    listed, sections = set(), []
    for key, heading, items in SECTIONS:
        out = []
        for it in items:
            if it.startswith("#"):
                out.append(("#", it[1:]))
            elif it in pages:
                listed.add(it)
                out.append((it, LABELS.get(it) or titles[it]))
        sections.append((key, heading, out))
    for p in pages:
        if p not in listed and p != "README.md":
            print("note: page not in sidebar:", p, file=sys.stderr)
    return sections


def sidebar_html(sections, current_rel, pages, root):
    out = []
    for key, heading, items in sections:
        is_open = any(rel == current_rel for rel, _ in items if rel != "#")
        lis = []
        for rel, label in items:
            if rel == "#":
                lis.append('<li class="group-label">%s</li>' % html.escape(label))
                continue
            cur = ' aria-current="page"' if rel == current_rel else ""
            lis.append('<li><a href="%s%s"%s>%s</a></li>' % (root, pages[rel], cur, html.escape(label)))
        out.append("<details%s><summary>%s</summary><ul>%s</ul></details>" % (" open" if is_open else "", html.escape(heading), "".join(lis)))
    return '<aside class="sidebar" id="sidebar" aria-label="Documentation">%s</aside>' % "".join(out)


def section_of(rel, sections):
    for key, heading, items in sections:
        if any(r == rel for r, _ in items):
            return key, heading
    return None, None


def pager_html(rel, sections, pages, root):
    for key, heading, items in sections:
        flat = [r for r, _ in items if r != "#"]
        if rel in flat:
            i = flat.index(rel)
            label = dict(items)
            parts = []
            if i > 0:
                parts.append('<a class="prev" href="%s%s"><small>Previous</small><span>%s</span></a>' % (root, pages[flat[i - 1]], html.escape(label[flat[i - 1]])))
            if i < len(flat) - 1:
                parts.append('<a class="next" href="%s%s"><small>Next</small><span>%s</span></a>' % (root, pages[flat[i + 1]], html.escape(label[flat[i + 1]])))
            return '<nav class="pager" aria-label="Pagination">%s</nav>' % "".join(parts) if parts else ""
    return ""


# ---------------------------------------------------------------- JSON-LD
def breadcrumbs(url, heading):
    parts = [p for p in url.split("/") if p]
    crumbs = [{"@type": "ListItem", "position": 1, "name": "Home", "item": SITE_URL + "/"}]
    acc = ""
    for i, p in enumerate(parts, start=2):
        acc += p + "/"
        name = heading if i == 2 and heading else p.replace("-", " ").capitalize()
        crumbs.append({"@type": "ListItem", "position": i, "name": name, "item": f"{SITE_URL}/{acc}"})
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": crumbs}


def faq_jsonld(md):
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


# ---------------------------------------------------------------- page shell
def shell(rel_md, md, body, pages, sections, last_mod, landing=False, noindex=False, root_override=None):
    url = pages.get(rel_md, "")
    canonical = f"{SITE_URL}/{url}"
    title, desc = title_and_description(md)
    desc = DESCRIPTIONS.get(rel_md, desc)
    full_title = "South African Airtime and Prepaid Electricity APIs: Guides and Code" if rel_md == "README.md" and not noindex else (f"{title} | {TITLE_SUFFIX}" if len(title) + len(TITLE_SUFFIX) + 3 <= 66 else title)
    depth = len([p for p in url.split("/") if p])
    root = root_override or ("../" * depth or "./")
    skey, sheading = section_of(rel_md, sections)

    ld = []
    if landing:
        ld.append({"@context": "https://schema.org", "@type": "WebSite", "name": SITE_NAME, "url": SITE_URL + "/", "description": desc, "inLanguage": "en-ZA"})
    else:
        ld.append({"@context": "https://schema.org", "@type": "TechArticle", "headline": title[:110], "description": desc, "url": canonical,
                   "dateModified": last_mod, "inLanguage": "en-ZA",
                   "author": {"@type": "Person", "name": "Erik Thiart", "url": "https://github.com/ErikThiart"},
                   "isPartOf": {"@type": "WebSite", "name": SITE_NAME, "url": SITE_URL + "/"}})
        ld.append(breadcrumbs(url, sheading))
    if rel_md == "prepaid-electricity/faq.md":
        faq = faq_jsonld(md)
        if faq:
            ld.append(faq)
    ld_tags = "\n".join('<script type="application/ld+json">' + json.dumps(x, ensure_ascii=False).replace("</", "<\\/") + "</script>" for x in ld)

    nav_items = []
    for label, href, key in TOP_NAV:
        cur = ' aria-current="page"' if key == skey else ""
        nav_items.append('<a href="%s%s"%s>%s</a>' % (root, href, cur, html.escape(label)))

    e = html.escape
    robots = "noindex" if noindex else "index, follow, max-snippet:-1"
    og_type = "website" if landing else "article"
    head = f"""<!doctype html>
<html lang="en-ZA" data-root="{root}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(full_title)}</title>
<meta name="description" content="{e(desc, quote=True)}">
<link rel="canonical" href="{e(canonical)}">
<meta name="robots" content="{robots}">
<meta name="theme-color" content="#ffffff" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#0a0a0a" media="(prefers-color-scheme: dark)">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{e(SITE_NAME)}">
<meta property="og:title" content="{e(title, quote=True)}">
<meta property="og:description" content="{e(desc, quote=True)}">
<meta property="og:url" content="{e(canonical)}">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{e(title, quote=True)}">
<meta name="twitter:description" content="{e(desc, quote=True)}">
<link rel="icon" href="{root}assets/favicon.svg" type="image/svg+xml">
<script>try{{var t=localStorage.getItem('theme');if(t==='dark'||(!t&&matchMedia('(prefers-color-scheme: dark)').matches))document.documentElement.classList.add('dark')}}catch(e){{}}</script>
<link rel="stylesheet" href="{root}assets/site.css">
<script src="{root}assets/site.js" defer></script>
{ld_tags}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="site-header">
  <div class="header-inner">
    <button class="btn btn-ghost btn-icon menu-btn" id="menu-btn" type="button" aria-label="Toggle menu" aria-controls="sidebar" aria-expanded="false">{ICON['menu']}</button>
    <a class="brand" href="{root}"><span class="brand-mark">{ICON['bolt']}</span><span class="brand-name">{BRAND}</span></a>
    <nav class="top-nav" aria-label="Main">{"".join(nav_items)}</nav>
    <span class="header-spacer"></span>
    <div class="header-actions">
      <button class="btn btn-search" type="button" data-search aria-label="Search documentation">{ICON['search']}<span class="label">Search…</span><kbd>⌘K</kbd></button>
      <a class="btn btn-ghost btn-icon" href="{REPO_URL}" aria-label="GitHub repository">{ICON['github']}</a>
      <button class="btn btn-ghost btn-icon" id="theme-toggle" type="button" aria-label="Toggle theme">{ICON['moon']}{ICON['sun']}</button>
    </div>
  </div>
</header>
<dialog class="search" id="search-dialog" aria-label="Search">
  <input class="search-input" id="search-input" type="search" placeholder="Search guides, endpoints, error codes…" autocomplete="off" aria-label="Search documentation">
  <ul class="search-list" id="search-list" role="listbox"></ul>
</dialog>
"""
    footer = f"""<footer class="site-footer">
  <div class="footer-inner">
    <p>Guides and sample code for the Freepaid airtime API, the SIMcloud API and the SIMcloud MCP server, maintained by <a href="https://github.com/ErikThiart">Erik Thiart</a>. MIT licence. Freepaid and SIMcloud are products of FREEPAID (PTY) LTD. The mock servers are not the real services: confirm behaviour with the provider.</p>
    <p><a href="{REPO_URL}">GitHub</a> · <a href="{REPO_URL}/blob/{BRANCH}/{e(rel_md)}">Edit this page</a></p>
  </div>
</footer>
</body>
</html>
"""
    if landing:
        return head + f'<main id="main">\n{body}\n</main>\n' + footer

    toc = toc_html(body)
    crumb = '<div class="breadcrumb"><a href="%s">Home</a><span class="sep">/</span><span>%s</span></div>' % (root, e(sheading or "Docs"))
    pager = pager_html(rel_md, sections, pages, root)
    main = f"""<div class="shell{' has-toc' if toc else ''}">
{sidebar_html(sections, rel_md, pages, root)}
<main class="content" id="main">
<article class="article">
{crumb}
<div class="prose">
{body}
</div>
{pager}
</article>
</main>
{toc}
</div>
"""
    return head + main + footer


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
    for name in ("site.css", "site.js", "favicon.svg"):
        shutil.copy(os.path.join(ROOT, "site", name), os.path.join(out, "assets", name))
    open(os.path.join(out, ".nojekyll"), "w").close()

    pages = collect_pages()
    mds, titles = {}, {}
    for rel in pages:
        with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
            mds[rel] = fh.read()
        titles[rel] = title_and_description(mds[rel])[0]
    sections = build_nav(pages, titles)

    sitemap, listing, search = [], [], []
    for rel_md, url in sorted(pages.items(), key=lambda kv: kv[1]):
        md = mds[rel_md]
        mod = last_modified(rel_md)
        landing = rel_md == "README.md"
        depth = len([p for p in url.split("/") if p])
        root = "../" * depth or "./"
        if landing:
            with open(os.path.join(ROOT, "site", "home.html"), encoding="utf-8") as fh:
                body = fh.read().replace("{{root}}", root)
        else:
            body = rewrite_links(render_markdown(md), rel_md, pages)
        dest = os.path.join(out, url, "index.html")
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "w", encoding="utf-8") as fh:
            fh.write(shell(rel_md, md, body, pages, sections, mod, landing=landing))
        title, desc = title_and_description(md)
        desc = DESCRIPTIONS.get(rel_md, desc)
        sitemap.append((SITE_URL + "/" + url, mod))
        listing.append((title, SITE_URL + "/" + url, desc))
        _, heading = section_of(rel_md, sections)
        heads = " ".join(re.sub(r"<[^>]+>", "", t) for _, _, t in re.findall(r"<h([23]) id=\"([^\"]+)\">(.*?)</h\1>", body, flags=re.S))
        search.append({"title": title, "url": url, "description": desc, "section": heading or "Home", "headings": html.unescape(heads)})

    with open(os.path.join(out, "search.json"), "w", encoding="utf-8") as fh:
        json.dump(search, fh, ensure_ascii=False, separators=(",", ":"))
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
    body404 = ('<div class="landing"><section class="hero"><h1>Page not found</h1><p class="lead">That page does not exist. Try the home page or search the guides.</p>'
               '<div class="cta"><a class="btn btn-primary btn-lg" href="%s/">Home</a><a class="btn btn-outline btn-lg" href="%s">GitHub</a></div></section></div>' % (SITE_URL, REPO_URL))
    with open(os.path.join(out, "404.html"), "w", encoding="utf-8") as fh:
        fh.write(shell("README.md", "# Page not found\n\nThat page does not exist.\n", body404, pages, sections, datetime.date.today().isoformat(),
                       landing=True, noindex=True, root_override=SITE_URL + "/"))
    print(f"built {len(pages)} pages into {out}")


if __name__ == "__main__":
    main()
