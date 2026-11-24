"""CEN (cen.com.kh) scraper.

The label comes from the site's own category (see docs/class_guide.md).

Usage (from the project root):
    python -m src.scrapers.cen --per-section 20                  # small test
    python -m src.scrapers.cen --per-section 300                 # full run (resumable)
    python -m src.scrapers.cen --per-section 300 --sections entertainment heal-beauty
"""
import argparse
import csv
import re
from pathlib import Path

from bs4 import BeautifulSoup

from src.scrapers.common import FIELDS, Fetcher, load_done, log

BASE = "https://cen.com.kh"
RAW_DIR = Path("data/raw/cen")
OUT_CSV = Path("data/raw/cen_articles.csv")

# site category path -> project class label
SECTIONS = {
    "national/politics": "politics",
    "national/business-2": "economy",
    "entertainment": "entertainment",
    "science-and-technology": "technology",
    "heal-beauty": "society_health",
    # "national/social" (security / society) also exists but shares the society_health label
    # with heal-beauty, and the quota is per label, so it is not in the default run.
}

ARTICLE_RE = re.compile(r"^https?://cen\.com\.kh/archives/(\d+)\.html$")
MIN_TEXT_CHARS = 100
BYLINE_RE = re.compile(r"^\s*(?:ប្រែសម្រួល(?:ដោយ)?\s*[:៖ៈ]?|(?:ដោយ|ការផ្សាយ|ប្រភព|រូបភាព|ឯកសារ)\s*[:៖ៈ])")


FOOTER_RE = re.compile(r"\s*រក្សាសិទ្ធិ[^\n]{0,80}$")


def list_article_urls(fetcher: Fetcher, section: str, limit: int):
    """Yield article URLs from the main listing of /category/<section>/page/N."""
    seen, page = set(), 1
    while len(seen) < limit:
        url = f"{BASE}/category/{section}" + (f"/page/{page}" if page > 1 else "")
        try:
            html = fetcher.get(url)
        except FileNotFoundError:
            return  # past the last page
        links = []
        # only the main loop; sidebars/trending blocks belong to other categories
        for a in BeautifulSoup(html, "lxml").select(".tdb_module_loop a[href]"):
            href = a["href"].split("#")[0]
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
    h1 = soup.find("h1", class_="tdb-title-text")
    body = soup.select_one(".tdb_single_content .tdb-block-inner")
    if not h1 or not body:
        return None
    for junk in body.select("script, style, iframe, figure, [class*=advads], [class*=share], [class*=related]"):
        junk.decompose()
    paras = [p.get_text(" ", strip=True) for p in body.find_all("p")]
    text = "\n".join(p for p in paras if p and not BYLINE_RE.match(p))
    # trailing copyright / author footer ("រក្សាសិទ្ធិដោយ ៖<author>", "...ដោយ CEN"): site fingerprint + names
    text = FOOTER_RE.sub("", text).strip()
    t = soup.select_one(".tdb_single_date time[datetime]")
    return h1.get_text(" ", strip=True), (t["datetime"] if t else ""), text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-section", type=int, default=20, help="articles to collect per section")
    ap.add_argument("--sections", nargs="*", default=list(SECTIONS), help="site category paths")
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
            # resume: the quota is per class label, so count what is already saved for it
            kept = sum(1 for v in done.values() if v == label)
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
                w.writerow({"id": f"cen_{aid}", "title": title, "text": text, "label": label,
                            "source": "cen", "url": url, "date": date})
                f.flush()
                done[url] = label
                kept += 1
                log(f"[{section}] {kept}/{args.per_section} saved (total {len(done)}): {title[:50]}")
            log(f"=== {section} -> {label}: kept {kept}, skipped {skipped}")
        log(f"DONE. {len(done)} articles in {OUT_CSV}")


if __name__ == "__main__":
    main()
