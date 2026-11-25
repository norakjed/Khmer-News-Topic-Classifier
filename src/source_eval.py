"""Per-source metrics and DAP -> CEN cross-source test (member 2).
Uses train and val only. The test set is NOT touched."""
import pandas as pd
from sklearn.metrics import classification_report, f1_score

from src.data import LABELS, load_split
from src.classical import make_pipeline, make_text

train = load_split("train")
val = load_split("val")
print("Sources in data:", sorted(train["source"].unique()))

# Final model: linear SVM, n-gram (2, 4), C=10
pipe = make_pipeline("svm", 10.0, (2, 4))
pipe.fit(make_text(train), train["label"])
pred = pipe.predict(make_text(val))

print("\n=== OVERALL on VALIDATION ===")
print(classification_report(val["label"], pred, labels=LABELS, digits=3, zero_division=0))

print("=== PER SOURCE on VALIDATION ===")
val = val.copy()
val["pred"] = pred
for src in sorted(val["source"].unique()):
    part = val[val["source"] == src]
    f1 = f1_score(part["label"], part["pred"], average="macro")
    acc = (part["label"] == part["pred"]).mean()
    print(f"{src}: rows={len(part)}  accuracy={acc:.3f}  macro-F1={f1:.3f}")

# Cross-source: train on DAP only, test on CEN only
print("\n=== CROSS-SOURCE: train on DAP, test on CEN ===")
both = pd.concat([train, val])
dap_train = train[train["source"].str.lower().str.contains("dap")]
cen_test = both[both["source"].str.lower().str.contains("cen")]
print("DAP train rows:", len(dap_train), " CEN test rows:", len(cen_test))

pipe2 = make_pipeline("svm", 10.0, (2, 4))
pipe2.fit(make_text(dap_train), dap_train["label"])
pred2 = pipe2.predict(make_text(cen_test))
print(classification_report(cen_test["label"], pred2, labels=LABELS, digits=3, zero_division=0))
print("Cross-source macro-F1:", round(f1_score(cen_test["label"], pred2, average="macro"), 4))