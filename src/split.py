"""Create the fixed train / validation / test split (70 / 15 / 15).

Stratified by class AND source, so every split has the same source mix inside every class.
The training set is also divided into 5 cross-validation folds (same stratification), so all
team members tune on the same folds. Validation and test rows get fold = -1.

Output: data/splits/splits.csv with columns id, split, fold, and data/splits/split_report.md.
The split is deterministic (seed 42). Do NOT change it after the team has started training.

Usage (from the project root):
    python -m src.split
"""
from pathlib import Path

import pandas as pd
from sklearn.model_selection import StratifiedKFold, train_test_split

DATA = Path("data/processed/dataset.csv")
OUT = Path("data/splits")
SEED = 42
TEST_FRAC, VAL_FRAC, N_FOLDS = 0.15, 0.15, 5


def make_split(df: pd.DataFrame) -> pd.DataFrame:
    strata = df["label"] + "|" + df["source"]
    idx = df.index.values
    rest, test = train_test_split(idx, test_size=TEST_FRAC, stratify=strata, random_state=SEED)
    train, val = train_test_split(rest, test_size=VAL_FRAC / (1 - TEST_FRAC), stratify=strata.loc[rest], random_state=SEED)
    out = pd.DataFrame({"id": df["id"], "split": "", "fold": -1})
    out.loc[train, "split"] = "train"
    out.loc[val, "split"] = "val"
    out.loc[test, "split"] = "test"
    skf = StratifiedKFold(N_FOLDS, shuffle=True, random_state=SEED)
    for k, (_, te) in enumerate(skf.split(train, strata.loc[train])):
        out.loc[train[te], "fold"] = k
    return out


def report(df: pd.DataFrame, sp: pd.DataFrame) -> str:
    m = df.merge(sp, on="id")
    L = [f"# Split report\n\nSeed {SEED}; {len(m):,} articles; train/val/test = {1 - TEST_FRAC - VAL_FRAC:.0%}/{VAL_FRAC:.0%}/{TEST_FRAC:.0%}; "
         f"{N_FOLDS} cross-validation folds inside train. Stratified by class x source.\n"]
    sizes = m["split"].value_counts()
    L.append("## Split sizes\n\n| split | articles | share |\n|---|---|---|")
    for s in ["train", "val", "test"]:
        L.append(f"| {s} | {sizes[s]} | {sizes[s] / len(m):.1%} |")
    for title, col in [("Articles per class", "label"), ("Articles per source", "source")]:
        ct = pd.crosstab(m[col], m["split"])[["train", "val", "test"]]
        L.append(f"\n## {title}\n\n| {col} | train | val | test | total |\n|---|---|---|---|---|")
        for k, r in ct.iterrows():
            L.append(f"| {k} | {r['train']} | {r['val']} | {r['test']} | {r.sum()} |")
    ct = pd.crosstab([m["label"], m["source"]], m["split"])[["train", "val", "test"]]
    L.append("\n## Class x source\n\n| class | source | train | val | test |\n|---|---|---|---|---|")
    for (c, s), r in ct.iterrows():
        L.append(f"| {c} | {s} | {r['train']} | {r['val']} | {r['test']} |")
    tr = m[m["split"] == "train"]
    ft = pd.crosstab(tr["label"], tr["fold"])
    L.append("\n## Cross-validation folds (train only): articles per class\n\n| class | " + " | ".join(f"fold {k}" for k in ft.columns) + " |\n|---|" + "---|" * len(ft.columns))
    for k, r in ft.iterrows():
        L.append(f"| {k} | " + " | ".join(str(v) for v in r) + " |")
    return "\n".join(L)


def main():
    df = pd.read_csv(DATA, encoding="utf-8-sig", keep_default_na=False)
    sp = make_split(df)
    OUT.mkdir(parents=True, exist_ok=True)
    sp.to_csv(OUT / "splits.csv", index=False)
    (OUT / "split_report.md").write_text(report(df, sp), encoding="utf-8")
    print(f"Wrote {OUT / 'splits.csv'} ({len(sp):,} rows) and split_report.md")
    print(sp["split"].value_counts().to_string())


if __name__ == "__main__":
    main()
