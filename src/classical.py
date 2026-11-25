
"""Classical models: TF-IDF character n-grams + Logistic Regression / SVM."""
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, f1_score
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

from src.data import LABELS, MAX_CHARS, load_cv_folds, load_split


def make_text(df):
    """Title + body, capped at MAX_CHARS. Never uses source/url/id/date."""
    return (df["title"] + " " + df["text"]).str.slice(0, MAX_CHARS)


def make_pipeline(model="logreg", C=1.0, ngram=(1, 3)):
    # The vectorizer is inside the pipeline, so it is fitted on train rows only.
    tfidf = TfidfVectorizer(analyzer="char", ngram_range=ngram,
                            min_df=2, max_features=200_000, sublinear_tf=True)
    if model == "logreg":
        clf = LogisticRegression(C=C, max_iter=1000)
    else:
        clf = LinearSVC(C=C)
    return Pipeline([("tfidf", tfidf), ("clf", clf)])


def cv_macro_f1(model, C, ngram):
    scores = []
    for tr, va in load_cv_folds():
        pipe = make_pipeline(model, C, ngram)
        pipe.fit(make_text(tr), tr["label"])
        scores.append(f1_score(va["label"], pipe.predict(make_text(va)), average="macro"))
    return float(np.mean(scores))


if __name__ == "__main__":
    train, val = load_split("train"), load_split("val")   # NOT the test set
    for model in ("logreg", "svm"):
        pipe = make_pipeline(model)
        pipe.fit(make_text(train), train["label"])
        pred = pipe.predict(make_text(val))
        print(f"\n=== {model} on VALIDATION ===")
        print(classification_report(val["label"], pred, labels=LABELS, digits=3))