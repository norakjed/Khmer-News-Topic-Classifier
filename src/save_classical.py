"""Save the final classical model and results 
Uses train and val only. The test set is NOT touched."""
import os
import joblib
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score

from src.data import load_split
from src.classical import make_pipeline, make_text

os.makedirs("models", exist_ok=True)
os.makedirs("reports", exist_ok=True)

train = load_split("train")
val = load_split("val")

# Final model: linear SVM, n-gram (2, 4), C=10
pipe = make_pipeline("svm", 10.0, (2, 4))
pipe.fit(make_text(train), train["label"])
pred = pipe.predict(make_text(val))

joblib.dump(pipe, "models/classical_svm.joblib")

out = pd.DataFrame({"id": val["id"], "label": val["label"], "pred": pred})
out.to_csv("reports/classical_val_predictions.csv", index=False)

rows = [
    ["logreg", "(2, 4)", 50.0, 0.8998],
    ["linear svm", "(2, 4)", 10.0, 0.9030],

]
table = pd.DataFrame(rows, columns=["model", "ngram", "C", "cv_macro_f1"])
table.to_csv("reports/classical_cv_results.csv", index=False)

# Logistic regression, n-gram (2, 4), C=50
logreg = make_pipeline("logreg", 50.0, (2, 4))
logreg.fit(make_text(train), train["label"])
logreg_pred = logreg.predict(make_text(val))

joblib.dump(logreg, "models/classical_logreg.joblib")

print("Saved models and results.")
for name, p in [("SVM", pred), ("Logistic regression", logreg_pred)]:
    print(f"{name} validation accuracy:", round(accuracy_score(val["label"], p), 3))
    print(f"{name} validation macro-F1:", round(f1_score(val["label"], p, average="macro"), 3))