"""Merge the raw scraped CSVs and clean them into data/processed/dataset.csv.

Raw files are never modified. Every removal is logged by rule and source, and the
ids of removed rows are written to data/processed/removed.csv for auditing.

Usage (from the project root):
    python -m src.clean
"""
import csv
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

URL_RE = re.compile(r"https?://\S+|www\.\S+")
ZERO_WIDTH = dict.fromkeys((0x200B, 0x200C, 0x200D, 0xFEFF), None)  # zero-width space, joiners, BOM (code points for str.translate)
KHMER_RE = re.compile("[" + chr(0x1780) + "-" + chr(0x17FF) + "]")  # Khmer Unicode block U+1780-U+17FF

RAW = [Path("data/raw/dap_articles.csv"), Path("data/raw/cen_articles.csv"), Path("data/raw/kt_articles.csv")]
OUT_DIR = Path("data/processed")
FIELDS = ["id", "title", "text", "label", "source", "url", "date"]

# ---- rule parameters (documented in the cleaning report) ----
MIN_KHMER_SHARE = 0.5     # share of Khmer characters in the text; below = not a Khmer article
MIN_TEXT_CHARS = 250      # shorter articles carry too little signal
AD_MIN_KEYWORDS = 3       # advertorial = phone number AND at least this many promo keywords
NEAR_DUP_SAME = 0.80      # char n-gram TF-IDF cosine: same story, same label -> keep the first
NEAR_DUP_CONFLICT = 0.70  # same story but different labels -> label noise, drop both

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
# Phone numbers: ASCII or Khmer digits, optional country code, spaces/hyphens between groups.
#  1) local numbers, 9-10 digits starting with 0:   012 345 678 | ០១២ ៣៤៥ ៦៧៨ | 097 8 119 119 | (+៨៥៥) ០៨៥ ៨៨៨ ១៨១
#  2) country code followed by the number:          +(855) 96 368 0826 | +855 96 368 0826
#  3) other international numbers:                  +66 92 954 4154
_D = r"[\d០-៩]"
PHONE_RE = re.compile(
    rf"(?<!{_D})\(?\+?(?:855|៨៥៥)\)?[ \t-]?(?:{_D}[ \t-]?){{8,9}}(?!{_D}|:)"
    rf"|(?<!{_D})(?:\(?\+?(?:855|៨៥៥)\)?[ \t-]?)?[0០]{_D}(?:[ \t-]?{_D}){{7,8}}(?!{_D}|:)"
    rf"|(?<!{_D})\+{_D}{{2,3}}(?:[ \t-]?{_D}){{8,10}}(?!{_D})")
LEFTOVER_SEP_RE = re.compile(r"(?:^|\s)[/|,]+(?=\s|$)")  # lone "/" left between two removed phone numbers
BYLINE_RE = re.compile(r"^(?:ប្រែសម្រួល(?:ដោយ)?\s*[:៖ៈ]?|(?:អត្ថបទដោយ|អត្ថបទ|ដោយ|ការផ្សាយ|ប្រភព|រូបភាព|ឯកសារ)\s*[:៖ៈ])")
FOOTER_RE = re.compile(r"\s*រក្សាសិទ្ធិ[^\n]{0,100}$")
COPYRIGHT_LINE_RE = re.compile(r"^(?:©|Copyright\b)")
AD_KEYWORDS = ["បញ្ចុះតម្លៃ", "ទំនាក់ទំនង", "ដាក់លក់", "លក់ដី", "កក់ប្រាក់", "ឱកាសដ៏ល្អ", "ប្រូម៉ូសិន", "Promotion",
               "ទូរស័ព្ទ", "ជួល", "ដីឡូ", "ផ្ទះ", "អាផាតមិន", "Vietjet", "ទិញ-លក់", "តម្លៃ", "ប្រាក់កក់",
               "Telegram", "Facebook Page", "ទំនិញ", "សាខា", "ចុះឈ្មោះ"]


def norm(s: str) -> str:
    """Unicode NFC, drop zero-width characters, URLs and e-mail addresses."""
    s = unicodedata.normalize("NFC", s or "").translate(ZERO_WIDTH)
    s = URL_RE.sub(" ", s)
    return EMAIL_RE.sub(" ", s)


def clean_body(text: str):
    """Return (cleaned text, had_phone_number)."""
    lines = []
    had_phone = False
    for line in norm(text).split("\n"):
        line = re.sub(r"[ \t]+", " ", line).strip()
        if not line or BYLINE_RE.match(line) or COPYRIGHT_LINE_RE.match(line):
            continue
        line = FOOTER_RE.sub("", line)
        if PHONE_RE.search(line):
            had_phone = True
            line = LEFTOVER_SEP_RE.sub(" ", PHONE_RE.sub(" ", line))
            line = re.sub(r"[ \t]+", " ", line).strip()
        if line:
            lines.append(line)
    return "\n".join(lines), had_phone


def khmer_share(text: str) -> float:
    return len(KHMER_RE.findall(text)) / max(1, len(text))


def load():
    rows = []
    for path in RAW:
        with open(path, newline="", encoding="utf-8-sig") as f:
            rows += list(csv.DictReader(f))
    return rows


def main():
    rows = load()
    removed = []  # (id, source, rule)
    stats = Counter()

    def drop(r, rule):
        removed.append((r["id"], r["source"], rule))

    # ---- 1. normalise + per-row flags ------------------------------------------------
    for r in rows:
        r["title"] = re.sub(r"\s+", " ", norm(r["title"])).strip()
        r["text"], r["_phone"] = clean_body(r["text"])
        r["date"] = (r["date"] or "")[:10]
        r["_kw"] = sum(k in r["text"] for k in AD_KEYWORDS)
    n_raw = len(rows)
    raw_counts = Counter((r["label"], r["source"]) for r in rows)

    # ---- 2. rule filters (in order) ---------------------------------------------------
    kept = []
    for r in rows:
        if not r["title"] or not r["text"]:
            drop(r, "empty title/text")
        elif khmer_share(r["text"]) < MIN_KHMER_SHARE:
            drop(r, f"not Khmer (Khmer share < {MIN_KHMER_SHARE})")
        elif r["_phone"] and r["_kw"] >= AD_MIN_KEYWORDS:
            drop(r, f"advertorial (phone number + >= {AD_MIN_KEYWORDS} promo keywords)")
        elif len(r["text"]) < MIN_TEXT_CHARS:
            drop(r, f"too short (< {MIN_TEXT_CHARS} chars)")
        else:
            kept.append(r)
    rows = kept

    # ---- 3. exact duplicates (same title or same text), same label: keep first ----------
    seen_title, seen_text, kept = {}, {}, []
    conflict_ids = set()
    for r in rows:
        t, x = re.sub(r"\s+", "", r["title"]).lower(), re.sub(r"\s+", "", r["text"]).lower()
        prev = seen_title.get(t) or seen_text.get(x)
        if prev is None:
            seen_title[t] = seen_text[x] = r
            kept.append(r)
        elif prev["label"] != r["label"]:
            conflict_ids.update({prev["id"], r["id"]})
        else:
            drop(r, "exact duplicate (title or text)")
    for r in kept:
        if r["id"] in conflict_ids:
            drop(r, "same article under different labels")
    rows = [r for r in kept if r["id"] not in conflict_ids]

    # ---- 4. near duplicates (char n-gram TF-IDF cosine) ----------------------------------
    docs = [(r["title"] + "\n" + r["text"])[:1500] for r in rows]
    X = TfidfVectorizer(analyzer="char", ngram_range=(3, 4), sublinear_tf=True, min_df=2, max_df=0.5).fit_transform(docs)
    n = X.shape[0]
    dead, near_pairs, conflict_pairs = set(), 0, 0
    for i0 in range(0, n, 500):
        S = (X[i0:i0 + 500] @ X.T).toarray()
        for k in range(S.shape[0]):
            i = i0 + k
            for j in np.nonzero(S[k] >= NEAR_DUP_CONFLICT)[0]:
                if j <= i or i in dead or j in dead:
                    continue
                if rows[i]["label"] != rows[j]["label"]:
                    dead.update({i, j}); conflict_pairs += 1
                    drop(rows[i], "near-duplicate under different labels"); drop(rows[j], "near-duplicate under different labels")
                elif S[k, j] >= NEAR_DUP_SAME:
                    dead.add(j); near_pairs += 1
                    drop(rows[j], f"near duplicate (similarity >= {NEAR_DUP_SAME})")
    final = [r for i, r in enumerate(rows) if i not in dead]

    # ---- 5. write outputs -----------------------------------------------------------------
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUT_DIR / "dataset.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for r in final:
            w.writerow({k: r[k] for k in FIELDS})
    with open(OUT_DIR / "removed.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["id", "source", "rule"])
        w.writerows(removed)

    # ---- 6. report -------------------------------------------------------------------------
    classes = sorted({r["label"] for r in final} | {l for l, _ in raw_counts})
    sources = sorted({s for _, s in raw_counts})
    rule_src = defaultdict(Counter)
    for _, src, rule in removed:
        rule_src[rule][src] += 1
    # a row can be recorded twice if it is part of both a conflict pair and another rule; report unique ids
    removed_ids = {i for i, _, _ in removed}
    promo_kept = sum(1 for r in final if r["_kw"] >= 4 and not r["_phone"])
    L = []
    L.append("# Cleaning report\n")
    L.append(f"Raw rows: {n_raw}. Removed: {len(removed_ids)}. Final: {len(final)} (kept {len(final) / n_raw:.1%}).\n")
    L.append("## Rows removed by rule\n")
    L.append("| Rule | " + " | ".join(sources) + " | Total |\n|---|" + "---|" * (len(sources) + 1))
    for rule, c in sorted(rule_src.items(), key=lambda kv: -sum(kv[1].values())):
        L.append(f"| {rule} | " + " | ".join(str(c[s]) for s in sources) + f" | {sum(c.values())} |")
    L.append("\n## Class x source counts: raw -> final\n")
    L.append("| Class | " + " | ".join(sources) + " | Total |\n|---|" + "---|" * (len(sources) + 1))
    fin_counts = Counter((r["label"], r["source"]) for r in final)
    for c in classes:
        cells = [f"{raw_counts[(c, s)]} -> {fin_counts[(c, s)]}" for s in sources]
        L.append(f"| {c} | " + " | ".join(cells) + f" | {sum(raw_counts[(c, s)] for s in sources)} -> {sum(fin_counts[(c, s)] for s in sources)} |")
    L.append("\n## Final dataset\n")
    L.append("| Class | Articles | Largest source share | Date range |\n|---|---|---|---|")
    for c in classes:
        rr = [r for r in final if r["label"] == c]
        sc = Counter(r["source"] for r in rr)
        ds = sorted(r["date"] for r in rr if r["date"])
        L.append(f"| {c} | {len(rr)} | {max(sc.values()) / len(rr):.0%} ({sc.most_common(1)[0][0]}) | {ds[0]} .. {ds[-1]} |")
    L.append(f"\nText length (chars): median {int(np.median([len(r['text']) for r in final]))}, "
             f"min {min(len(r['text']) for r in final)}, max {max(len(r['text']) for r in final)}.")
    L.append(f"Phone numbers were removed from the text of every kept article. Possible promotional articles kept "
             f"(>= 4 promo keywords, no phone number; judged on-topic): {promo_kept}.")
    L.append(f"Near-duplicate pairs merged: {near_pairs}. Cross-label conflict pairs dropped: {conflict_pairs}.")
    report = "\n".join(L)
    (OUT_DIR / "cleaning_report.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
