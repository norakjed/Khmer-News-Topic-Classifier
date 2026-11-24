# Khmer News Topic Classifier

Classify Khmer news headlines/articles into topics (politics, economy, sports, entertainment, technology, society/health) using logistic regression, SVM and a small ANN.
ML course project, 2026-2027 (4 weeks). Lecturer: Soklay HENG.
Full description: `docs/Project_Description.pdf`

## Structure
```
data/raw/        Scraped pages and CSVs (local only, git-ignored)
data/processed/  dataset.csv (cleaned articles), cleaning_report.md, removed.csv
data/splits/     splits.csv (fixed train/val/test + CV folds), split_report.md
docs/            Project description, data card, class guide, source survey
notebooks/       01_eda.ipynb (add the model notebooks here)
reports/         EDA figures and tables
src/scrapers/    dap.py, cen.py, kt.py (one per website) and common.py (shared helpers)
src/             clean.py, split.py, data.py (loader), eda.py
```
New model code goes in new files under `src/` (for example `features.py`, `classical.py`, `ann.py`, `evaluate.py`), one file per person to avoid merge conflicts.

## Roles
- **Chhorn Norakjed (Data):** sources, scrapers, cleaning, EDA, split, data card
- **Hak Kimly (Classical models):** TF-IDF, logistic regression, SVM, cross-validation
- **Seoum Reaseychanbopich (ANN and evaluation):** ANN, metrics, learning curves, error analysis, demo

## Data format
`data/processed/dataset.csv`: `id, title, text, label, source, url, date` (3,138 articles, 6 classes).
Classes: politics, economy, technology, sports, society_health, entertainment.

## Using the data and the fixed split
```python
from src.data import load_split, load_cv_folds, LABELS

train = load_split("train")   # 2,196 articles (70%)
val   = load_split("val")     #   471 articles (15%)
test  = load_split("test")    #   471 articles (15%), use ONCE at the very end

for fold_train, fold_val in load_cv_folds():   # 5 cross-validation folds inside train
    ...
```
- The split is stratified by **class and source**, seed 42, and is stored in `data/splits/splits.csv` (`id, split, fold`). Counts per split are in `data/splits/split_report.md`.
- Do **not** re-split. If the dataset ever changes, tell the team first.
- Suggested text cap for models: `MAX_CHARS = 5000` in `src/data.py` (median article is about 1,700 characters, the longest 21,338).
- Reproduce the pipeline:
  ```
  python -m src.scrapers.dap --per-section 400      # collect (raw pages stay local, about an hour per site)
  python -m src.scrapers.cen --per-section 300
  python -m src.scrapers.kt --per-section 300
  python -m src.clean                                # raw CSVs to data/processed/dataset.csv
  python -m src.split                                # fixed split (do not re-run after the team started)
  python -m src.eda                                  # EDA figures and tables
  ```
  Websites change, so re-scraping gives different articles: use the committed `dataset.csv` and `splits.csv` as the reference.

## Setup (Windows)
```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Rules
- Fit TF-IDF and any learned preprocessing on the training set only.
- The test set is used once, at the end.
- Do not change the split.
- Never use `source`, `url`, `id` or `date` as model inputs: the source of an article can be recognised from its text with 0.83 to 0.99 accuracy (see `reports/eda_summary.md`), so source style is a shortcut to the label.
- Report metrics overall **and per source**, and run one cross-source experiment (train on DAP, test on CEN).
- Known data limitations: society_health has no 2026 articles while sports, economy and politics are mostly 2026; technology contains an estimated 10 to 20% culture and heritage articles from CEN.
