"""Tune C and n-gram range with 5-fold CV on the training set"""
from src.classical import cv_macro_f1

results = []

for model in ["logreg", "svm"]:
    for ngram in [(1, 3), (2, 4)]:
        for C in [0.1, 1.0, 10.0]:
            score = cv_macro_f1(model, C, ngram)
            results.append((score, model, ngram, C))
            print(f"{model}  ngram={ngram}  C={C}  cv macro-F1={score:.4f}")

results.sort(reverse=True)

print("\n=== Best 3 by cross-validated macro-F1 ===")
for i in range(3):
    score, model, ngram, C = results[i]
    print(f"{model}  ngram={ngram}  C={C}  cv macro-F1={score:.4f}")