# Khmer News Topic Classifier

Classify Khmer news headlines/articles into topics (politics, economy, sports, entertainment, technology, society/health) using logistic regression, SVM and a small ANN.
ML course project, 2026-2027 (4 weeks). Lecturer: Soklay HENG.
Full description: `docs/Project_Description.pdf`

## Structure
```
data/raw/        Scraped articles (local only, git-ignored)
data/processed/  Cleaned dataset.csv
data/splits/     Fixed train/val/test splits (seeded, stratified)
notebooks/       EDA and experiments
src/             scraper.py, preprocess.py, features, models, evaluation
docs/            Project description, data card, class guide
reports/         Figures and final report
```

## Roles
- **Chhorn Norakjed (Data):** sources, scraper, cleaning, EDA, preprocessing, split, segmentation test
- **Hak Kimly (Classical models):** TF-IDF, logistic regression, SVM, cross-validation
- **Seoum Reaseychanbopich (ANN and evaluation):** ANN, metrics, learning curves, error analysis, demo

## Data format
`data/processed/dataset.csv`: `id, title, text, label, source, url, date`

## Setup (Windows)
```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Rules
- Fit TF-IDF and any learned preprocessing on the training set only.
- The test set is used once, at the end.
- Do not change the split after Week 1 agreement.
