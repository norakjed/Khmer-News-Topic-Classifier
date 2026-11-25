"""RBF SVM tuning with 5-fold CV on the training set."""
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import f1_score
from sklearn.pipeline import Pipeline
from sklearn.svm import SVC

from src.data import load_cv_folds
from src.classical import make_text

results = []

for C in [1.0, 10.0, 100.0]:
    scores = []
    for tr, va in load_cv_folds():
        tfidf = TfidfVectorizer(analyzer="char", ngram_range=(2, 4),
                                min_df=2, max_features=100_000, sublinear_tf=True)
        pipe = Pipeline([("tfidf", tfidf), ("clf", SVC(kernel="rbf", C=C, gamma="scale"))])
        pipe.fit(make_text(tr), tr["label"])
        pred = pipe.predict(make_text(va))
        scores.append(f1_score(va["label"], pred, average="macro"))
    score = float(np.mean(scores))
    results.append((score, C))
    print(f"rbf  ngram=(2, 4)  C={C}  cv macro-F1={score:.4f}")

results.sort(reverse=True)
print("\n=== Best RBF setting ===")
print(f"C={results[0][1]}  cv macro-F1={results[0][0]:.4f}")