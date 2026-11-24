"""Load the dataset with the fixed split. Everyone should use this instead of splitting again.

    from src.data import load_split, load_cv_folds, LABELS

    train = load_split("train")      # DataFrame: id, title, text, label, source, url, date, split, fold
    val   = load_split("val")
    test  = load_split("test")       # use ONCE, at the very end

    for k, (tr, va) in enumerate(load_cv_folds()):   # 5 folds inside the training set
        ...

Rules:
  * Fit TF-IDF, scalers, vocabularies and anything else learned from data on the TRAIN rows only.
  * Never use the `source`, `url`, `id` or `date` columns as model inputs (source style is a shortcut to the label).
  * Do not re-split. The split is fixed (seed 42) and shared by the whole team.
"""
from pathlib import Path

import pandas as pd

DATA = Path("data/processed/dataset.csv")
SPLITS = Path("data/splits/splits.csv")
LABELS = ["politics", "economy", "technology", "sports", "society_health", "entertainment"]
MAX_CHARS = 5000  # suggested cap for the text length (see EDA: median ~1,700, longest 21,338)


def load_all() -> pd.DataFrame:
    df = pd.read_csv(DATA, encoding="utf-8-sig", keep_default_na=False)
    sp = pd.read_csv(SPLITS, keep_default_na=False)
    out = df.merge(sp, on="id", validate="one_to_one")
    if len(out) != len(df):
        raise ValueError("splits.csv does not match dataset.csv; re-run `python -m src.split` only if the dataset changed on purpose")
    return out


def load_split(name: str) -> pd.DataFrame:
    if name not in ("train", "val", "test"):
        raise ValueError("split must be 'train', 'val' or 'test'")
    d = load_all()
    return d[d["split"] == name].reset_index(drop=True)


def load_cv_folds(n_folds: int = 5):
    """Yield (train_part, validation_part) DataFrames for each fold of the TRAIN split."""
    tr = load_split("train")
    for k in range(n_folds):
        yield tr[tr["fold"] != k].reset_index(drop=True), tr[tr["fold"] == k].reset_index(drop=True)
