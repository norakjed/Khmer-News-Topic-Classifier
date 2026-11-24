# Data card: Khmer News Topic Dataset

Version of 2026-11-24. File: `data/processed/dataset.csv` (3,138 articles, about 19 MB, UTF-8).
Built for a university machine-learning course project (classification of Khmer news articles into six topics).

## 1. Summary

| Item | Value |
|---|---|
| Task | Multi-class text classification (6 topics) |
| Language | Khmer, with some Latin-letter names and terms (code-switching) |
| Articles | 3,138 (from 3,327 collected; 189 removed by cleaning) |
| Sources | DAP News, CEN, Kampuchea Thmey (public news websites) |
| Publication dates | 2019-10-11 to 2026-11-24 (most from 2022 to 2026) |
| Text length | median 1,684 characters, 5th to 95th percentile 576 to 4,281, longest 21,338 |
| Collected on | 2026-11-23 and 2026-11-24 |
| Fields | `id, title, text, label, source, url, date` |

## 2. Composition

Articles per class and source (after cleaning):

| Class | DAP News | CEN | Kampuchea Thmey | Total | Published in 2026 |
|---|---|---|---|---|---|
| politics | 373 | 241 | - | 614 | 41% |
| technology | 313 | 243 | - | 556 | 6% |
| economy | 304 | 242 | - | 546 | 49% |
| sports | 381 | - | 161 | 542 | 57% |
| society_health | 164 | 297 | - | 461 | 0% |
| entertainment | 123 | 296 | - | 419 | 7% |
| **Total** | **1,658** | **1,319** | **161** | **3,138** | |

Every class has two sources. Fixed split (seed 42, stratified by class and source): train 2,196, validation 471, test 471 (see `data/splits/split_report.md`).

## 3. How the data was collected

- **Method:** custom Python scrapers (`src/scrapers/dap.py`, `src/scrapers/cen.py`, `src/scrapers/kt.py`) reading public category listing pages and article pages. No login, no private content.
- **Politeness:** `robots.txt` checked before every request; one request at a time; at least 2 seconds between requests; the site's own `Crawl-delay` is obeyed (10 seconds for Kampuchea Thmey). Downloaded pages are cached locally, so nothing is requested twice.
- **Sources chosen** after a `robots.txt` survey (`docs/source_survey.md`). Sites were **excluded** when they forbade AI training in `robots.txt` (Post Khmer, Thmey Thmey, Cambodianess), blocked crawlers (Fresh News, AKP), had no usable archive pagination (Koh Santepheap Daily) or had no topic structure (VOA Khmer).
- **Fields kept:** title, article text, URL, publication date. Author names are not stored.
- **Coverage depends on the site's archive,** not on the site's size: Kampuchea Thmey exposes only about 160 sports articles (about six weeks), and DAP exposes few entertainment and health articles.

## 4. Labels

- **Source of labels:** the news site's own section for each article (weak, "distant" labels), mapped to six classes in `docs/class_guide.md`. No human annotated the whole dataset.
- Sections that mix topics (national, international) and non-news sections (advertising, fortune telling and similar) were not used.
- An article listed under two sections keeps only the first label.
- **Label quality check:** a 110-article random sample was checked by one team member: 97% to 98% agreement with the site label (per class: economy, entertainment and sports 100%; politics and technology 94%; society_health 96% to 100%). Cohen's kappa 0.98. This is a small, single-annotator, non-blind check; there is no inter-annotator agreement.

## 5. Cleaning (`src/clean.py`)

Raw files are never modified. Every removed article is listed with its reason in `data/processed/removed.csv`.

| Step | Rows removed |
|---|---|
| Text shorter than 250 characters | 54 |
| Not Khmer (Khmer characters under 50% of the text) | 51 |
| Advertorial (a phone number plus at least 3 promotional keywords) | 46 |
| Near duplicate (character n-gram TF-IDF similarity 0.80 or more, same label) | 24 |
| Exact duplicate (same title or text) | 14 |

Text changes applied to every kept article: Unicode NFC normalisation; zero-width characters removed (one source inserted invisible word separators, which would have identified it); URLs and e-mail addresses removed; **phone numbers removed** (ASCII and Khmer digits, local and international formats); credit lines ("by", "edited by", photo, source) and copyright footers removed; empty lines and repeated spaces removed. Capitalisation, punctuation and paragraph breaks are kept.

## 6. Known limitations and biases

1. **Label noise from site sections.** CEN's science-and-technology section contains an estimated 10% to 20% culture and heritage articles (Ministry of Culture, UNESCO, temples). They were kept under `technology` by team decision. society_health merges different site sections (health, lifestyle, society, safety).
2. **Time confound.** The classes cover different periods: society_health has no 2026 articles (mostly 2022), technology and entertainment are mostly older, sports, economy and politics are mostly 2026. Year numbers can act as a shortcut feature.
3. **Source style is detectable.** A text-only model recognises the source of an article with 0.83 to 0.99 balanced accuracy within a class, and class and source are correlated (Cramer's V 0.45). Use the stratified split, report scores per source, never use `source`, `url`, `id` or `date` as features, and consider a cross-source test (see `reports/eda_summary.md`).
4. **Uneven source mix.** entertainment is 71% CEN, society_health 64% CEN, sports 70% DAP. The smallest cells are DAP entertainment (123) and Kampuchea Thmey sports (161).
5. **Promotional content remains.** About 50 company or telecom promotions without a phone number were kept (they are on-topic for economy or technology).
6. **Three sites only,** all Cambodian news websites in a formal news register. The dataset does not represent social-media Khmer, slang or spelling variants.
7. **Very long articles.** A few articles are far longer than the median; models should cap the text length (suggested 5,000 characters).

## 7. Intended use and not-intended use

- **Intended:** training and comparing text classifiers (logistic regression, SVM, small neural networks) for Khmer topic classification in this course project, and studying shortcut and label-noise effects.
- **Not intended:** production news classification without re-checking; any use that needs verified human labels; inferring anything about authors or readers.

## 8. Ethics, privacy and legal notes

- Only public web pages were collected, at low request rates, respecting `robots.txt` and the sites' AI-training signals.
- Personal contact details were removed (phone numbers, e-mail addresses, URLs); author names are not stored. Names of public figures that appear in the news text itself remain.
- **Copyright:** the article texts belong to the publishers. They were collected for coursework only. Do not republish or redistribute the full texts outside the course; if the repository is public, consider keeping only titles, URLs and labels, or making the repository private. The article URLs allow anyone to retrieve the originals.
- No consent was needed for public news articles, but the data was not collected for general release.

## 9. Reproducing and updating

```
python -m src.scrapers.dap --per-section 400             # DAP News
python -m src.scrapers.cen --per-section 300             # CEN
python -m src.scrapers.kt --per-section 300              # Kampuchea Thmey (about an hour, 10 s delay)
python -m src.clean                                      # raw to data/processed/dataset.csv
python -m src.split                                      # fixed split (seed 42)
python -m src.eda                                        # figures and tables
```
Raw scraped files are kept locally in `data/raw/` and are not part of the repository. Websites change, so a new scrape will give different articles; the processed dataset and the split are the fixed reference for the team's results. Re-collecting data would require a new split and a new version of this card.

## 10. Related files

`docs/source_survey.md` (source survey), `docs/class_guide.md` (section to class mapping), `data/processed/cleaning_report.md`, `data/splits/split_report.md`, `reports/eda_summary.md`.
