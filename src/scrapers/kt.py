"""Kampuchea Thmey (kampucheathmey.com) sports scraper.

Used as a second source for the `sports` class. The site's robots.txt asks for a
10 second Crawl-delay, which the shared Fetcher applies automatically
(so about 6 requests per minute: 300 articles take roughly an hour).

Usage (from the project root):
    python -m src.scrapers.kt --per-section 20      # small test
    python -m src.scrapers.kt --per-section 300     # full run (resumable)
"""
import argparse
import csv
import re
from pathlib import Path

from bs4 import BeautifulSoup

from src.scrapers.common import FIELDS, Fetcher, load_done, log

BASE = "https://www.kampucheathmey.com"
RAW_DIR = Path("data/raw/kt")
OUT_CSV = Path("data/raw/kt_articles.csv")

# site category -> project class label (only sports is needed from this site)
SECTIONS = {"sports": "sports"}

ARTICLE_RE = re.compile(r"^https?://(?:www\.)?kampucheathmey\.com/sports/(\d+)$")
MIN_TEXT_CHARS = 100
# credit lines such as "អត្ថបទដោយ៖ <name>" (article by), edited by, photo, source
BYLINE_RE = re.compile(r"^\s*(?:អត្ថបទដោយ|អត្ថបទ|ប្រែសម្រួល(?:ដោយ)?|ដោយ|ការផ្សាយ|ប្រភព|រូបភាព|ឯកសារ)\s*[:៖ៈ]")


def list_article_urls(fetcher: Fetcher, section: str, limit: int):
    """Yield article URLs from /category/<section>/page/N."""
    seen, page = set(), 1
    while len(seen) < limit:
        url = f"{BASE}/category/{section}" + (f"/page/{page}" if page > 1 else "")
        try:
            html = fetcher.get(url)
        except FileNotFoundError:
            return
        links = []
        for a in BeautifulSoup(html, "lxml").find_all("a", href=True):
            href = a["href"].split("#")[0]
            if href.startswith("/"):
                href = BASE + href
            href = href.replace("://kampucheathmey.com", "://www.kampucheathmey.com")
            if ARTICLE_RE.match(href) and href not in seen and href not in links:
                links.append(href)
        log(f"[{section}] listing page {page}: {len(links)} new links")
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
    h1 = soup.find("h1")
    body = soup.select_one("#mvp-content-main")
    if not h1 or not body:
        return None
    paras = []
    for p in body.find_all("p"):
        if "has-text-align-center" in (p.get("class") or []):  # centred photo captions
            continue
        t = p.get_text(" ", strip=True)
        if t and not BYLINE_RE.match(t):
            paras.append(t)
    meta = soup.find("meta", property="article:published_time")
    date = meta["content"] if meta and meta.get("content") else ""
    return h1.get_text(" ", strip=True), date, "\n".join(paras)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-section", type=int, default=20, help="articles to collect per class label")
    ap.add_argument("--sections", nargs="*", default=list(SECTIONS), help="site category names")
    args = ap.parse_args()

    fetcher = Fetcher(BASE, RAW_DIR)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    done = load_done(OUT_CSV)
    new_file = not OUT_CSV.exists()

    with open(OUT_CSV, "a", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new_file:
            w.writeheader()
        for section in args.sections:
            label = SECTIONS[section]
            kept = sum(1 for v in done.values() if v == label)  # quota is per class label
            skipped = 0
            for url in list_article_urls(fetcher, section, int(args.per_section * 1.5)):
                if kept >= args.per_section:
                    break
                if url in done:
                    continue
                aid = ARTICLE_RE.match(url).group(1)
                try:
                    parsed = parse_article(fetcher.get_cached(url, aid))
                except Exception as e:
                    log(f"[{section}] ERROR {url}: {e}")
                    skipped += 1
                    continue
                if not parsed or len(parsed[2]) < MIN_TEXT_CHARS:
                    log(f"[{section}] skip (empty/too short) {url}")
                    skipped += 1
                    continue
                title, date, text = parsed
                w.writerow({"id": f"kt_{aid}", "title": title, "text": text, "label": label,
                            "source": "kampucheathmey", "url": url, "date": date})
                f.flush()
                done[url] = label
                kept += 1
                log(f"[{section}] {kept}/{args.per_section} saved (total {len(done)}): {title[:50]}")
            log(f"=== {section} -> {label}: kept {kept}, skipped {skipped}")
        log(f"DONE. {len(done)} articles in {OUT_CSV}")


if __name__ == "__main__":
    main()
