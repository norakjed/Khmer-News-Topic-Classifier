"""Shared helpers for the site scrapers (polite fetching, cache, resumable CSV)."""
import csv
import time
from pathlib import Path
from urllib import robotparser

import requests

HEADERS = {"User-Agent": "Mozilla/5.0 (student ML course project)"}
FIELDS = ["id", "title", "text", "label", "source", "url", "date"]
LOG_FILE = Path("data/raw/scraper.log")  # temporary progress log (git-ignored)


def log(msg: str):
    line = f"{time.strftime('%H:%M:%S')} {msg}"
    try:
        print(line, flush=True)
    except UnicodeEncodeError:  # console cannot show Khmer; the log file still gets the full line
        print(line.encode("ascii", "replace").decode(), flush=True)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


class Fetcher:
    """GET with robots.txt check, fixed delay, retries and an on-disk HTML cache."""

    def __init__(self, base: str, cache_dir: Path, delay: float = 2.0):
        self.base, self.cache_dir, self.delay = base.rstrip("/"), Path(cache_dir), delay
        self.robots = robotparser.RobotFileParser(f"{self.base}/robots.txt")
        # fetch robots.txt ourselves with our User-Agent: urllib's default one is 403-blocked by some
        # sites, and RobotFileParser.read() then treats the 403 as "disallow everything"
        r = requests.get(f"{self.base}/robots.txt", headers=HEADERS, timeout=25)
        if r.status_code == 200:
            self.robots.parse(r.text.splitlines())
        elif r.status_code in (404, 410):
            self.robots.parse([])  # no robots.txt: nothing is disallowed
        else:
            raise RuntimeError(f"cannot read robots.txt of {self.base} (HTTP {r.status_code})")
        # obey the site's own Crawl-delay if it is longer than ours
        site_delay = self.robots.crawl_delay(HEADERS["User-Agent"])
        if site_delay:
            self.delay = max(self.delay, float(site_delay))
            log(f"robots.txt Crawl-delay {site_delay}s -> using {self.delay}s between requests")
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self._last = 0.0

    def allowed(self, url: str) -> bool:
        return self.robots.can_fetch(HEADERS["User-Agent"], url)

    def get(self, url: str) -> str:
        """Return page HTML. Raises FileNotFoundError on 404, PermissionError if robots disallows."""
        if not self.allowed(url):
            raise PermissionError(f"blocked by robots.txt: {url}")
        for attempt in range(3):
            wait = self.delay - (time.time() - self._last)
            if wait > 0:
                time.sleep(wait)
            self._last = time.time()
            try:
                r = self.session.get(url, timeout=25)
                if r.status_code == 404:
                    raise FileNotFoundError(url)
                r.raise_for_status()
                return r.text
            except requests.RequestException:
                if attempt == 2:
                    raise
                time.sleep(5 * (attempt + 1))

    def get_cached(self, url: str, key: str) -> str:
        """Article page: read from cache if present, otherwise download and cache."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        path = self.cache_dir / f"{key}.html"
        if path.exists():
            return path.read_text(encoding="utf-8")
        html = self.get(url)
        path.write_text(html, encoding="utf-8")
        return html


def load_done(csv_path: Path) -> dict:
    """Return {url: label} for rows already saved."""
    if not Path(csv_path).exists():
        return {}
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        return {row["url"]: row["label"] for row in csv.DictReader(f)}
