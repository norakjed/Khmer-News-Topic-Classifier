"""News scraper skeleton (Member A). Check robots.txt/terms first; keep delays polite."""
import csv
import time

import requests
from bs4 import BeautifulSoup

DELAY = 2.0  # seconds between requests
HEADERS = {"User-Agent": "student-ml-project (course research)"}
FIELDS = ["id", "title", "text", "label", "source", "url", "date"]


def fetch(url: str) -> BeautifulSoup:
    time.sleep(DELAY)
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return BeautifulSoup(r.text, "lxml")


def save(rows, path="data/raw/articles.csv"):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)

# TODO: per-site functions: list section pages -> article URLs -> parse title/text/date
