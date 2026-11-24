"""Exploratory data analysis of data/processed/dataset.csv.

Writes figures to reports/figures/, tables to reports/eda/ and a summary to
reports/eda_summary.md. Everything is computed from the dataset, nothing is typed in by hand.

Usage (from the project root):
    python -m src.eda
"""
import re
import unicodedata
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from scipy.stats import chi2_contingency
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import make_pipeline

DATA = Path("data/processed/dataset.csv")
FIG = Path("reports/figures")
TAB = Path("reports/eda")
SEED = 42

CLASS_ORDER = ["politics", "economy", "technology", "sports", "society_health", "entertainment"]
SOURCE_NAMES = {"dap-news": "DAP News", "cen": "CEN", "kampucheathmey": "Kampuchea Thmey"}
# categorical slots 1-3 of the validated palette (all-pairs check passes; aqua needs visible labels)
SOURCE_COLORS = {"dap-news": "#2a78d6", "cen": "#eb6834", "kampucheathmey": "#1baf7a"}
SEQ = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]  # sequential blue
BLUE = "#2a78d6"
SURFACE, INK, INK2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"

KHMER = re.compile("[" + chr(0x1780) + "-" + chr(0x17FF) + "]")  # Khmer Unicode block U+1780-U+17FF
LATIN = re.compile(r"[A-Za-z]")


def style():
    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "font.family": ["Segoe UI", "DejaVu Sans"], "font.size": 10,
        "text.color": INK, "axes.labelcolor": INK2, "xtick.color": MUTED, "ytick.color": MUTED,
        "axes.edgecolor": AXIS, "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": False, "axes.titlesize": 12, "axes.titleweight": "bold", "axes.titlelocation": "left",
    })


def hgrid(ax):
    ax.xaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def md_table(df: pd.DataFrame, index=True) -> str:
    d = df.reset_index() if index else df
    cols = [str(c) for c in d.columns]
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, r in d.iterrows():
        out.append("| " + " | ".join(f"{v:,.2f}".rstrip("0").rstrip(".") if isinstance(v, float) else str(v) for v in r) + " |")
    return "\n".join(out)


def load() -> pd.DataFrame:
    df = pd.read_csv(DATA, encoding="utf-8-sig", keep_default_na=False)
    df["n_chars"] = df["text"].str.len()
    df["n_lines"] = df["text"].str.count("\n") + 1
    df["khmer_share"] = df["text"].map(lambda t: len(KHMER.findall(t)) / max(1, len(t)))
    df["latin_share"] = df["text"].map(lambda t: len(LATIN.findall(t)) / max(1, len(t)))
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["year"] = df["date"].dt.year
    df["src"] = df["source"].map(SOURCE_NAMES)
    return df


# ------------------------------------------------------------------------------ figures
def fig_class_balance(df):
    ct = pd.crosstab(df["label"], df["source"]).reindex(CLASS_ORDER)[list(SOURCE_COLORS)]
    ct = ct.loc[ct.sum(axis=1).sort_values().index]  # largest at the top
    fig, ax = plt.subplots(figsize=(8.4, 3.9))
    left = np.zeros(len(ct))
    for s, color in SOURCE_COLORS.items():
        vals = ct[s].values
        ax.barh(ct.index, vals, left=left, color=color, edgecolor=SURFACE, linewidth=1.6, height=0.62, label=SOURCE_NAMES[s])
        for y, (l, v) in enumerate(zip(left, vals)):
            if v >= 40:
                ax.text(l + v / 2, y, f"{int(v)}", ha="center", va="center", color="#ffffff", fontsize=9, fontweight="bold")
        left += vals
    for y, tot in enumerate(left):
        ax.text(tot + 8, y, f"{int(tot)}", va="center", color=INK2, fontsize=9)
    ax.axvline(300, color=MUTED, linewidth=1, linestyle=(0, (4, 3)))
    ax.text(300, len(ct) - 0.35, "300 minimum", color=MUTED, fontsize=8, ha="center", va="bottom")
    ax.set_xlim(0, ct.sum(axis=1).max() * 1.1)
    ax.set_title("Articles per class, split by source")
    ax.set_xlabel("Articles")
    ax.legend(frameon=False, ncols=3, loc="lower right", fontsize=9, bbox_to_anchor=(1, 1.0))
    hgrid(ax)
    fig.tight_layout()
    fig.savefig(FIG / "fig_class_balance.png", dpi=160)
    plt.close(fig)


def fig_length(df):
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.9), sharex=True, gridspec_kw={"width_ratios": [6, 3]})
    def boxes(ax, groups, labels, colors):
        bp = ax.boxplot(groups, vert=False, whis=(5, 95), showfliers=False, widths=0.55, patch_artist=True, tick_labels=labels,
                        medianprops={"color": INK, "linewidth": 1.8}, whiskerprops={"color": MUTED}, capprops={"color": MUTED})
        for patch, c in zip(bp["boxes"], colors):
            patch.set(facecolor=c, edgecolor=SURFACE, linewidth=1.2, alpha=0.9)
        ax.set_xscale("log")
        hgrid(ax)
    order = list(reversed(CLASS_ORDER))
    boxes(axes[0], [df.loc[df.label == c, "n_chars"] for c in order], order, [BLUE] * len(order))
    for y, c in enumerate(order, start=1):
        m = int(df.loc[df.label == c, "n_chars"].median())
        axes[0].text(1.6e4, y, f"median {m:,}", va="center", ha="right", color=INK2, fontsize=8.5)
    axes[0].set_title("Text length by class")
    srcs = list(reversed(list(SOURCE_COLORS)))
    boxes(axes[1], [df.loc[df.source == s, "n_chars"] for s in srcs], [SOURCE_NAMES[s] for s in srcs], [SOURCE_COLORS[s] for s in srcs])
    axes[1].set_title("Text length by source")
    axes[0].set_xlabel("Characters, log scale (box = quartiles, whiskers = 5th-95th percentile)")
    axes[1].set_xlabel("Characters, log scale")
    for ax in axes:
        ax.set_xticks([300, 1000, 3000, 10000])
        ax.set_xticklabels(["300", "1,000", "3,000", "10,000"])
        ax.set_xlim(200, 2e4)
    fig.tight_layout()
    fig.savefig(FIG / "fig_length.png", dpi=160)
    plt.close(fig)


def fig_khmer_share(df):
    fig, axes = plt.subplots(2, 3, figsize=(10.5, 5.2), sharex=True, sharey=True)
    bins = np.linspace(0.5, 1.0, 26)
    for ax, c in zip(axes.ravel(), CLASS_ORDER):
        d = df.loc[df.label == c, "khmer_share"]
        ax.hist(d, bins=bins, color=BLUE, edgecolor=SURFACE, linewidth=0.8)
        ax.set_title(c, fontsize=10)
        ax.text(0.03, 0.9, f"{(d < 0.8).sum()} below 0.80", transform=ax.transAxes, color=INK2, fontsize=8.5)
        ax.yaxis.grid(True, color=GRID, linewidth=0.8)
        ax.set_axisbelow(True)
    for ax in axes[1]:
        ax.set_xlabel("Khmer share of characters")
    for ax in axes[:, 0]:
        ax.set_ylabel("Articles")
    fig.suptitle("How Khmer are the articles? (the filter already removed everything below 0.50)", x=0.01, ha="left", fontsize=12, fontweight="bold")
    fig.tight_layout()
    fig.savefig(FIG / "fig_khmer_share.png", dpi=160)
    plt.close(fig)


def fig_year_heatmap(df):
    yrs = list(range(int(df.year.min()), int(df.year.max()) + 1))
    ct = pd.crosstab(df["label"], df["year"]).reindex(index=CLASS_ORDER, columns=yrs, fill_value=0)
    cmap = LinearSegmentedColormap.from_list("blue_seq", SEQ)
    fig, ax = plt.subplots(figsize=(9.2, 3.8))
    im = ax.imshow(ct.values, cmap=cmap, aspect="auto", vmin=0, vmax=ct.values.max())
    ax.set_xticks(range(len(yrs)), [str(y) for y in yrs])
    ax.set_yticks(range(len(CLASS_ORDER)), CLASS_ORDER)
    for i in range(ct.shape[0]):
        for j in range(ct.shape[1]):
            v = ct.values[i, j]
            ax.text(j, i, str(v) if v else "", ha="center", va="center", fontsize=8.5,
                    color="#ffffff" if v > ct.values.max() * 0.45 else INK)
    ax.set_xticks(np.arange(-.5, len(yrs)), minor=True)
    ax.set_yticks(np.arange(-.5, len(CLASS_ORDER)), minor=True)
    ax.grid(which="minor", color=SURFACE, linewidth=2)
    ax.tick_params(which="minor", length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_title("Publication year by class (articles per cell)")
    fig.tight_layout()
    fig.savefig(FIG / "fig_year_heatmap.png", dpi=160)
    plt.close(fig)
    return ct


def source_predictability(df):
    """Can a plain TF-IDF model tell the two sources of a class apart? High scores = shortcut risk."""
    rows, feats = [], {}
    for c in CLASS_ORDER:
        d = df[df.label == c]
        srcs = sorted(d.source.unique())
        if len(srcs) != 2:
            continue
        y = (d.source == srcs[1]).astype(int).values
        pipe = make_pipeline(TfidfVectorizer(analyzer="char", ngram_range=(2, 4), min_df=3, sublinear_tf=True, max_features=150000),
                             LogisticRegression(max_iter=2000, class_weight="balanced"))
        pred = cross_val_predict(pipe, d["text"].values, y, cv=StratifiedKFold(5, shuffle=True, random_state=SEED))
        rows.append({"class": c, "source_a": SOURCE_NAMES[srcs[0]], "source_b": SOURCE_NAMES[srcs[1]], "articles": len(d),
                     "balanced_accuracy": round(balanced_accuracy_score(y, pred), 3)})
        pipe.fit(d["text"].values, y)
        vec, lr = pipe.steps[0][1], pipe.steps[1][1]
        names = np.array(vec.get_feature_names_out()); order = np.argsort(lr.coef_[0])
        feats[c] = {SOURCE_NAMES[srcs[0]]: [n for n in names[order[:10]]], SOURCE_NAMES[srcs[1]]: [n for n in names[order[::-1][:10]]]}
    res = pd.DataFrame(rows)
    fig, ax = plt.subplots(figsize=(8.2, 3.3))
    r = res.sort_values("balanced_accuracy")
    ax.barh(r["class"], r["balanced_accuracy"], color=BLUE, edgecolor=SURFACE, height=0.58)
    for y, (v, a, b) in enumerate(zip(r.balanced_accuracy, r.source_a, r.source_b)):
        ax.text(v + 0.008, y, f"{v:.2f}  ({a} vs {b})", va="center", color=INK2, fontsize=8.5)
    ax.axvline(0.5, color=MUTED, linewidth=1, linestyle=(0, (4, 3)))
    ax.set_ylim(-0.95, len(r) - 0.45)
    ax.text(0.505, -0.9, "chance = 0.50", color=MUTED, fontsize=8, ha="left", va="center")
    ax.set_xlim(0.4, 1.28)
    ax.set_xticks([0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
    ax.set_xlabel("Balanced accuracy of a text-only model telling the two sources apart (5-fold CV)")
    ax.set_title("Can a simple model tell the source from the text?")
    hgrid(ax)
    fig.tight_layout()
    fig.savefig(FIG / "fig_source_predictability.png", dpi=160)
    plt.close(fig)
    return res, feats


# ------------------------------------------------------------------------------ tables
def top_chars(df, k=30):
    def freq(texts):
        s = "".join(texts)
        kh = [ch for ch in s if KHMER.match(ch)]
        return pd.Series(kh).value_counts(), len(s)
    allc, n = freq(df["text"])
    out = pd.DataFrame({"char": allc.index[:k], "codepoint": [f"U+{ord(c):04X}" for c in allc.index[:k]],
                        "name": [unicodedata.name(c, "?").replace("KHMER ", "").title() for c in allc.index[:k]],
                        "per_1000_chars": (allc.values[:k] / n * 1000).round(1)})
    return out


def distinctive_ngrams(df, n=4, k=10, min_docs=20):
    """Per class: character n-grams with the highest smoothed log-odds of appearing in that class's articles."""
    cv = CountVectorizer(analyzer="char", ngram_range=(n, n), min_df=min_docs, binary=True)
    X = cv.fit_transform(df["text"]); names = np.array(cv.get_feature_names_out())
    khmer_only = np.array([bool(KHMER.search(t)) and " " not in t and "\n" not in t for t in names])
    out = {}
    for c in CLASS_ORDER:
        m = (df["label"] == c).values
        a = np.asarray(X[m].sum(0)).ravel() + 1; b = np.asarray(X[~m].sum(0)).ravel() + 1
        lo = np.log(a / (m.sum() - a + 2)) - np.log(b / ((~m).sum() - b + 2))
        keep = khmer_only & (np.asarray(X[m].sum(0)).ravel() >= min_docs)
        idx = np.argsort(-(lo * keep))[:k]
        out[c] = [(names[i], int(a[i] - 1)) for i in idx]
    return out


def main():
    FIG.mkdir(parents=True, exist_ok=True); TAB.mkdir(parents=True, exist_ok=True)
    style()
    df = load()
    lines = [f"# EDA summary\n\nGenerated by `python -m src.eda` from `{DATA}` ({len(df):,} articles). Numbers below are computed, not typed.\n"]

    # overview
    ct = pd.crosstab(df["label"], df["src"]).reindex(CLASS_ORDER)
    ct["total"] = ct.sum(axis=1)
    ct["largest_source_share"] = (ct.drop(columns="total").max(axis=1) / ct["total"]).map(lambda v: f"{v:.0%}")
    ct.to_csv(TAB / "class_by_source.csv", encoding="utf-8-sig")
    lines += ["## Class by source\n", md_table(ct), ""]
    V = chi2_contingency(pd.crosstab(df["label"], df["source"]))[0]
    cv = float(np.sqrt(V / (len(df) * (min(pd.crosstab(df["label"], df["source"]).shape) - 1))))
    lines += [f"Cramer's V between class and source: **{cv:.2f}**. This is high by design (sports comes only from DAP and Kampuchea Thmey, "
              f"entertainment only from DAP and CEN), so source can leak the label unless sources are mixed in every class.\n"]

    # length
    def lstats(g):
        return g["n_chars"].describe(percentiles=[.05, .5, .95]).round(0).astype(int)[["count", "mean", "5%", "50%", "95%", "max"]]
    lc = df.groupby("label").apply(lstats, include_groups=False).reindex(CLASS_ORDER)
    ls = df.groupby("src").apply(lstats, include_groups=False)
    lc.to_csv(TAB / "length_by_class.csv", encoding="utf-8-sig"); ls.to_csv(TAB / "length_by_source.csv", encoding="utf-8-sig")
    lines += ["## Text length (characters)\n", "By class:\n", md_table(lc), "\nBy source:\n", md_table(ls), ""]
    lines += [f"Lines (paragraphs) per article: median {int(df.n_lines.median())}, 95th percentile {int(df.n_lines.quantile(.95))}.\n"]

    # language
    mixed = df[df.khmer_share < 0.8]
    comp = df.groupby("label").agg(median_khmer_share=("khmer_share", "median"), articles_below_0_80=("khmer_share", lambda s: int((s < 0.8).sum())),
                                   median_latin_share=("latin_share", "median")).reindex(CLASS_ORDER).round(3)
    comp.to_csv(TAB / "language_by_class.csv", encoding="utf-8-sig")
    lines += ["## Khmer vs. English content\n", md_table(comp),
              f"\n{len(mixed)} articles ({len(mixed) / len(df):.1%}) have a Khmer share below 0.80 (names, brands and English terms inside Khmer text).\n"]

    # time
    yr = fig_year_heatmap(df)
    yr.to_csv(TAB / "year_by_class.csv", encoding="utf-8-sig")
    dr = df.groupby("label")["date"].agg(["min", "median", "max"]).reindex(CLASS_ORDER)
    for c in dr.columns:
        dr[c] = dr[c].dt.strftime("%Y-%m-%d")
    share26 = (df.assign(is26=df.year == 2026).groupby("label")["is26"].mean().reindex(CLASS_ORDER) * 100).round(0).astype(int).astype(str) + "%"
    dr["published_in_2026"] = share26
    lines += ["## Time coverage\n", md_table(dr), ""]

    # characters + distinctive n-grams
    tc = top_chars(df)
    tc.to_csv(TAB / "top_khmer_characters.csv", index=False, encoding="utf-8-sig")
    lines += ["## Most frequent Khmer characters\n", md_table(tc, index=False), ""]
    dn = distinctive_ngrams(df)
    rows = [{"class": c, "top distinctive 4-grams (articles containing it)": ", ".join(f"{g} ({n})" for g, n in v)} for c, v in dn.items()]
    pd.DataFrame(rows).to_csv(TAB / "distinctive_4grams_by_class.csv", index=False, encoding="utf-8-sig")
    lines += ["## Distinctive character 4-grams per class\n",
              "Highest smoothed log-odds of appearing in the class versus all others (document frequency in brackets). "
              "Fragments are not words (Khmer has no spaces); they are listed to check that the signal is topical rather than a site artifact.\n",
              md_table(pd.DataFrame(rows), index=False), ""]

    # source predictability
    res, feats = source_predictability(df)
    res.to_csv(TAB / "source_predictability.csv", index=False, encoding="utf-8-sig")
    lines += ["## Can the source be recognised from the text?\n", md_table(res, index=False), "\nCharacter n-grams that push a prediction toward each source:\n"]
    for c, d in feats.items():
        for s, g in d.items():
            lines.append(f"- **{c} / {s}**: {', '.join(g[:8])}")
    lines.append("")

    # figures
    fig_class_balance(df); fig_length(df); fig_khmer_share(df)
    lines += ["## Files written\n", "- reports/figures: fig_class_balance, fig_length, fig_khmer_share, fig_year_heatmap, fig_source_predictability",
              "- reports/eda/*.csv: every table above\n"]
    Path("reports/eda_summary.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"EDA done: {len(df):,} articles. See reports/eda_summary.md, reports/figures/, reports/eda/")


if __name__ == "__main__":
    main()
