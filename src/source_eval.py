"""Per-source metrics and DAP -> CEN cross-source test.
Uses train and val only. The test set is NOT touched.

Not every source has every class (e.g. CEN has no sports). Macro-F1 is averaged only over
the classes that really occur in the evaluated articles. Predicting an absent class is still
an error: it lowers the recall of the true class.
A source with only one class gets no macro-F1; its accuracy is the recall of that class.

Usage (from the project root):
    python -m src.source_eval
"""
import os

import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, f1_score, precision_recall_fscore_support

from src.data import LABELS, load_split
from src.classical import make_pipeline, make_text

SUMMARY_OUT = "reports/source_eval_summary.csv"
PER_CLASS_OUT = "reports/source_eval_per_class.csv"

summary_rows, class_rows = [], []


def evaluate(name, y_true, y_pred):
    """Print and record the scores over the classes present in y_true."""
    present = [c for c in LABELS if c in set(y_true)]
    acc = accuracy_score(y_true, y_pred)
    macro = None
    if len(present) > 1:
        macro = f1_score(y_true, y_pred, labels=present, average="macro", zero_division=0)

    print(f"\n--- {name}: rows={len(y_true)}, classes present={len(present)} ---")
    if macro is None:
        print(f"Only '{present[0]}' articles: recall={acc:.3f} (macro-F1 is not meaningful)")
    else:
        print(classification_report(y_true, y_pred, labels=present, digits=3, zero_division=0))
        print(f"accuracy={acc:.3f}  macro-F1 over {len(present)} classes={macro:.3f}")

    summary_rows.append({"evaluation": name, "rows": len(y_true), "classes_present": len(present),
                         "accuracy": round(acc, 4), "macro_f1": None if macro is None else round(macro, 4)})

    precision, recall, f1, support = precision_recall_fscore_support(
        y_true, y_pred, labels=present, zero_division=0)
    for i, label in enumerate(present):
        # With one class only, precision and F1 say nothing about telling topics apart.
        class_rows.append({"evaluation": name, "class": label,
                           "precision": None if macro is None else round(precision[i], 4),
                           "recall": round(recall[i], 4),
                           "f1": None if macro is None else round(f1[i], 4),
                           "support": int(support[i])})


train = load_split("train")
val = load_split("val")
print("Sources in data:", sorted(train["source"].unique()))

# Final model: linear SVM, n-gram (2, 4), C=10
pipe = make_pipeline("svm", 10.0, (2, 4))
pipe.fit(make_text(train), train["label"])
val = val.copy()
val["pred"] = pipe.predict(make_text(val))

print("\n=== OVERALL and PER SOURCE on VALIDATION ===")
evaluate("val: all sources", val["label"], val["pred"])
for src in sorted(val["source"].unique()):
    part = val[val["source"] == src]
    evaluate(f"val: {src}", part["label"], part["pred"])

# Cross-source: train on DAP only, test on CEN only (CEN rows from train and val)
print("\n=== CROSS-SOURCE: train on DAP, test on CEN ===")
both = pd.concat([train, load_split("val")])
dap_train = train[train["source"] == "dap-news"]
cen_test = both[both["source"] == "cen"]
print("DAP train rows:", len(dap_train), " CEN test rows:", len(cen_test))

pipe2 = make_pipeline("svm", 10.0, (2, 4))
pipe2.fit(make_text(dap_train), dap_train["label"])
evaluate("cross-source: train dap-news, test cen", cen_test["label"], pipe2.predict(make_text(cen_test)))

os.makedirs("reports", exist_ok=True)
pd.DataFrame(summary_rows).to_csv(SUMMARY_OUT, index=False)
pd.DataFrame(class_rows).to_csv(PER_CLASS_OUT, index=False)
print(f"\nSaved {SUMMARY_OUT} and {PER_CLASS_OUT}")
