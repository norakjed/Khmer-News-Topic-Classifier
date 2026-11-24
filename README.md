# Khmer News Topic Classifier

A labelled dataset of Khmer news articles and the code to build it, for classifying articles into six topics with machine learning.

Public Khmer datasets are scarce, and most text-classification tools are built for English. Khmer is also written without spaces between words, which makes standard word-based pipelines harder to apply. This project collects and cleans Khmer news articles from public websites, documents the dataset openly (including its flaws), and provides a fixed evaluation split so that different models can be compared fairly. Features are character n-grams, so no Khmer word segmenter is needed.

## The dataset

`data/processed/dataset.csv` contains **3,138 articles** in six classes, collected from three public Khmer news websites.

| Class | DAP News | CEN | Kampuchea Thmey | Total |
|---|---|---|---|---|
| politics | 373 | 241 | - | 614 |
| technology | 313 | 243 | - | 556 |
| economy | 304 | 242 | - | 546 |
| sports | 381 | - | 161 | 542 |
| society_health | 164 | 297 | - | 461 |
| entertainment | 123 | 296 | - | 419 |

| Column | Description |
|---|---|
| `id` | Unique article id |
| `title`, `text` | Headline and cleaned article body (Khmer, with some Latin-letter names) |
| `label` | One of `politics, economy, technology, sports, society_health, entertainment` |
| `source` | Website the article came from |
| `url` | Original article address |
| `date` | Publication date |

Labels come from each website's own section for the article (weak labels, not human-annotated); the mapping is in [`docs/class_guide.md`](docs/class_guide.md). Phone numbers, e-mail addresses and URLs were removed from the text, and duplicates, advertisements and non-Khmer articles were filtered out. The full description is in the **[data card](docs/data_card.md)**.

### Fixed train / validation / test split

`data/splits/splits.csv` assigns every article to a split: 70% train (2,196), 15% validation (471), 15% test (471). The split is stratified by class **and** source with a fixed seed, and the training set is divided into 5 cross-validation folds. Counts are in [`data/splits/split_report.md`](data/splits/split_report.md).

## Getting started

```
git clone https://github.com/norakjed/Khmer-News-Topic-Classifier.git
cd Khmer-News-Topic-Classifier
python -m venv .venv
.venv\Scripts\activate            # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

Load the data with the fixed split (run from the repository root):

```python
from src.data import load_split, load_cv_folds, LABELS

train = load_split("train")   # pandas DataFrames: id, title, text, label, source, url, date, split, fold
val   = load_split("val")
test  = load_split("test")    # keep for the final evaluation only

for fold_train, fold_val in load_cv_folds():   # 5 cross-validation folds inside the training set
    ...
```

`MAX_CHARS = 5000` in `src/data.py` is a suggested cap for the text length (the median article has about 1,700 characters; the longest has 21,338).

## Recommended evaluation protocol

If you use this data, these practices keep results honest:

1. Fit TF-IDF, vocabularies and anything else learned from data on the **training set only**, and use the **test set once**, at the end.
2. Do not use `source`, `url`, `id` or `date` as model inputs. A plain character n-gram model can tell the source of an article from its text with 0.83 to 0.99 balanced accuracy (see [`reports/eda_summary.md`](reports/eda_summary.md)), so source style is a shortcut to the label.
3. Report metrics overall **and per source**, and consider a cross-source experiment (train on one website, test on another).
4. Keep the provided split rather than re-splitting, so results are comparable.

## Known limitations

- **Weak labels.** Labels are website sections, not annotations. A manual check of a small random sample found high agreement, but CEN's science-and-technology section contains an estimated 10% to 20% culture and heritage articles, and `society_health` merges several sections (health, lifestyle, society).
- **Time differences between classes.** `society_health` has no 2026 articles (mostly 2022), while sports, economy and politics are mostly 2026, so publication year can leak the topic.
- **Source and class are correlated.** For example, entertainment is 71% CEN and sports is 70% DAP.
- **Narrow register.** Three Cambodian news websites in a formal news style: no social-media Khmer, slang or heavy spelling variation.

## Reproducing the pipeline

```
python -m src.scrapers.dap --per-section 400     # collect (raw pages stay local; about an hour per site)
python -m src.scrapers.cen --per-section 300
python -m src.scrapers.kt --per-section 300
python -m src.clean                              # raw CSVs to data/processed/dataset.csv
python -m src.split                              # create the fixed split (seed 42)
python -m src.eda                                # EDA figures and tables
```

Websites change, so a new scrape produces different articles; treat the committed `dataset.csv` and `splits.csv` as the reference. The scrapers read public pages only, check `robots.txt`, wait at least 2 seconds between requests (longer when a site asks) and keep only the title, text, URL and date. If you run them, follow each website's terms and keep the delays.

## Repository structure

```
data/processed/  dataset.csv, cleaning_report.md, removed.csv (every removed article and the reason)
data/splits/     splits.csv, split_report.md
docs/            data_card.md, class_guide.md, source_survey.md, Project_Description.pdf
notebooks/       01_eda.ipynb
reports/         EDA summary, tables and figures
src/scrapers/    one scraper per website (dap.py, cen.py, kt.py) and shared helpers
src/             clean.py, split.py, data.py (loader), eda.py
```

Raw downloaded pages are kept locally in `data/raw/` and are not part of the repository.

## Ethics and data use

- Only public web pages were collected, at low request rates, respecting `robots.txt`. Websites that forbid AI training in `robots.txt` or block crawlers were not used.
- Personal contact details were removed and author names are not stored. Names of public figures that appear in the news text itself remain.
- **The article texts belong to their publishers.** The dataset is shared for research and education, and each row links to its original article. Please do not use the texts for purposes the publishers have not allowed, and respect the sites' terms.

## Authors

Chhorn Norakjed, Hak Kimly and Seoum Reaseychanbopich. Created as a Machine Learning course project, academic year 2026-2027.
