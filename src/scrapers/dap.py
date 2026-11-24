"""DAP News scraper.

Collects Khmer news articles from public category pages of dap-news.com.
The label comes from the site's own category (see docs/class_guide.md).

Usage (from the project root):
    python -m src.scrapers.dap --per-section 20            # small test run
    python -m src.scrapers.dap --per-section 400           # full run (resumable)

Polite by design: robots.txt is checked, one request at a time, fixed delay,
raw HTML cached in data/raw/ so nothing is requested twice.
"""
import argparse
import csv
import re
import time
from pathlib import Path
from urllib import robotparser
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE = "https://dap-news.com"
DELAY = 2.0  # seconds between network requests
HEADERS = {"User-Agent": "Mozilla/5.0 (student ML course project)"}
FIELDS = ["id", "title", "text", "label", "source", "url", "date"]

RAW_DIR = Path("data/raw/dap")
OUT_CSV = Path("data/raw/dap_articles.csv")

# site category slug -> project class label
SECTIONS = {
    "politic": "politics",
    "economic": "economy",
    "sport": "sports",
    "entertianment": "entertainment",  # sic: the site's own spelling
    "technology": "technology",
    "health": "society_health",
}

ARTICLE_RE = re.compile(r"^https?://(?:www\.)?dap-news\.com/[a-z0-9-]+/\d{4}/\d{2}/\d{2}/(\d+)/?$")
MIN_TEXT_CHARS = 100
# byline / credit lines ("by:", "edited by:", "translated by:") are not article content
BYLINE_RE = re.compile(r"^\s*(?:ប្រែសម្រួល(?:ដោយ)?\s*[:៖ៈ]?|(?:ដោយ|ការផ្សាយ|ប្រភព|រូបភាព|ឯកសារ)\s*[:៖ៈ])")

_robots = robotparser.RobotFileParser(f"{BASE}/robots.txt")
_last_request = 0.0
_session = requests.Session()
_session.headers.update(HEADERS)


def allowed(url: str) -> bool:
    return _robots.can_fetch(HEADERS["User-Agent"], url)


def get(url: str) -> str:
    """GET with robots check, delay and retry. Returns HTML text."""
    global _last_request
    if not allowed(url):
        raise PermissionError(f"blocked by robots.txt: {url}")
    for attempt in range(3):
        wait = DELAY - (time.time() - _last_request)
        if wait > 0:
            time.sleep(wait)
        _last_request = time.time()
        try:
            r = _session.get(url, timeout=25)
            if r.status_code == 404:
                raise FileNotFoundError(url)
            r.raise_for_status()
            return r.text
        except requests.RequestException:
            if attempt == 2:
                raise
            time.sleep(5 * (attempt + 1))


def list_article_urls(slug: str, limit: int):
    """Yield article URLs from /category/<slug>/page/N/ until `limit` reached."""
    seen, page = set(), 1
    while len(seen) < limit:
        url = f"{BASE}/category/{slug}/" + (f"page/{page}/" if page > 1 else "")
        try:
            html = get(url)
        except FileNotFoundError:
            return  # ran out of pages
        links = []
        for a in BeautifulSoup(html, "lxml").find_all("a", href=True):
            href = urljoin(url, a["href"]).split("#")[0]
            m = ARTICLE_RE.match(href)
            if m and href not in seen and href not in links:
                links.append(href)
        if not links:
            return
        for href in links:
            if len(seen) >= limit:
                return
            seen.add(href)
            yield href
        page += 1


def parse_article(html: str):
    """Return (title, date, text) or None if the page is not a usable article."""
    soup = BeautifulSoup(html, "lxml")
    h1 = soup.find("h1", class_="post-title")
    body = soup.find(id="content-main")
    if not h1 or not body:
        return None
    for junk in body.select("script, style, iframe, figure, .advads-entity-placement, "
                            "[class*=advads], [class*=share], [class*=related]"):
        junk.decompose()
    paras = [p.get_text(" ", strip=True) for p in body.find_all("p")]
    text = "\n".join(p for p in paras if p and not BYLINE_RE.match(p))
    t = soup.find("time", attrs={"datetime": True})
    return h1.get_text(" ", strip=True), (t["datetime"] if t else ""), text


def article_html(url: str, article_id: str) -> str:
    """Fetch an article page, using the local cache when present."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    cache = RAW_DIR / f"{article_id}.html"
    if cache.exists():
        return cache.read_text(encoding="utf-8")
    html = get(url)
    cache.write_text(html, encoding="utf-8")
    return html


def load_done():
    """Return {url: label} for rows already saved."""
    if not OUT_CSV.exists():
        return {}
    with open(OUT_CSV, newline="", encoding="utf-8-sig") as f:
        return {row["url"]: row["label"] for row in csv.DictReader(f)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-section", type=int, default=20, help="articles to collect per section")
    ap.add_argument("--sections", nargs="*", default=list(SECTIONS), help="site category slugs")
    args = ap.parse_args()

    _robots.read()
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    done = load_done()
    new_file = not OUT_CSV.exists()

    with open(OUT_CSV, "a", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new_file:
            w.writeheader()
        for slug in args.sections:
            label = SECTIONS[slug]
            kept = sum(1 for v in done.values() if v == label)  # already saved (resume)
            skipped = 0
            # request extra URLs, since some pages are skipped (too short / duplicates)
            for url in list_article_urls(slug, int(args.per_section * 1.5)):
                if kept >= args.per_section:
                    break
                if url in done:  # saved earlier, or listed under another section
                    continue
                aid = ARTICLE_RE.match(url).group(1)
                try:
                    parsed = parse_article(article_html(url, aid))
                except Exception as e:  # keep going on a single bad page
                    print(f"  ! {url}: {e}")
                    skipped += 1
                    continue
                if not parsed or len(parsed[2]) < MIN_TEXT_CHARS:
                    skipped += 1
                    continue
                title, date, text = parsed
                w.writerow({"id": f"dap_{aid}", "title": title, "text": text, "label": label,
                            "source": "dap-news", "url": url, "date": date})
                f.flush()
                done[url] = label
                kept += 1
            print(f"{slug:14s} -> {label:15s} kept {kept}, skipped {skipped}")


if __name__ == "__main__":
    main()
