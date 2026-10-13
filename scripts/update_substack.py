"""Refresh _data/substack.json from the Epsilon Aligned RSS feed.

Eyebrow labels and tint hues come from scripts/substack_labels.json, keyed by
post slug. Posts missing from it get the fallback label and a cycled hue.
"""
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from pathlib import Path

FEED = "https://epsilonaligned.substack.com/feed"
ROOT = Path(__file__).resolve().parent.parent
LABELS = ROOT / "scripts" / "substack_labels.json"
OUT = ROOT / "_data" / "substack.json"
SKIP = {"coming-soon"}
LIMIT = 4
HUES = ["indigo", "sash", "straw", "tint"]

# Substack rejects non-browser user agents from cloud IPs.
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36",
    "Accept": "application/rss+xml, application/xml;q=0.9, */*;q=0.8",
}
req = urllib.request.Request(FEED, headers=HEADERS)
root = ET.fromstring(urllib.request.urlopen(req, timeout=30).read())
labels = json.loads(LABELS.read_text())

posts = []
for item in root.iter("item"):
    url = item.findtext("link")
    slug = url.rstrip("/").rsplit("/", 1)[-1]
    if slug in SKIP:
        continue
    enclosure = item.find("enclosure")
    # Keep only the original S3 URL so the template can request its own size.
    image = None
    if enclosure is not None:
        match = re.search(r"/(https%3A%2F%2F.+)$", enclosure.get("url", ""))
        image = match.group(1) if match else None
    meta = labels.get(slug, {})
    posts.append({
        "slug": slug,
        "title": item.findtext("title").strip(),
        "subtitle": (item.findtext("description") or "").strip(),
        "url": url,
        "date": parsedate_to_datetime(item.findtext("pubDate")).date().isoformat(),
        "image": image,
        "label": meta.get("label", "Epsilon Aligned"),
        "hue": meta.get("hue", HUES[len(posts) % len(HUES)]),
    })
    if len(posts) == LIMIT:
        break

OUT.write_text(json.dumps(posts, indent=2, ensure_ascii=False) + "\n")
print(f"Wrote {len(posts)} posts to {OUT.relative_to(ROOT)}")
