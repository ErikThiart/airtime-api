#!/usr/bin/env python3
"""Checks every internal link and anchor in the built site. Usage: python3 site/check_links.py [_site]"""
import html
import os
import re
import sys

site = sys.argv[1] if len(sys.argv) > 1 else "_site"
ids = {}


def page_ids(path):
    if path not in ids:
        with open(path, encoding="utf-8") as fh:
            ids[path] = set(re.findall(r'\sid="([^"]+)"', fh.read()))
    return ids[path]


pages = [os.path.join(dp, f) for dp, _, fn in os.walk(site) for f in fn if f.endswith(".html")]
bad = total = 0
for p in pages:
    with open(p, encoding="utf-8") as fh:
        text = fh.read()
    for m in re.finditer(r'href="([^"]*)"', text):
        href = html.unescape(m.group(1))
        total += 1
        if re.match(r"^(https?:|mailto:|tel:)", href):
            continue
        path, _, anchor = href.partition("#")
        target = os.path.normpath(os.path.join(os.path.dirname(p), path)) if path else p
        if os.path.isdir(target):
            target = os.path.join(target, "index.html")
        if not os.path.exists(target):
            bad += 1
            print("MISSING", p, "->", href)
        elif anchor and target.endswith(".html") and anchor not in page_ids(target):
            bad += 1
            print("BAD ANCHOR", p, "->", href)
print("pages %d, links %d, problems %d" % (len(pages), total, bad))
sys.exit(1 if bad else 0)
