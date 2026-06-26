from __future__ import annotations

import pickle
from typing import Callable
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline, FeatureUnion

class ProductPredictor:
    """Lightweight, text-only product head trained on OCR text.

    Two TF-IDF (char + word n-grams) + LogisticRegression stages:
      - a "noise gate" (`is_product`) predicting whether any product is present, and
      - a multi-class classifier (`predict`) naming the product.
    A regex rule function (passed to `fit`) takes priority over the ML output.
    """

    def __init__(self, min_class_count=1, prob_threshold=0.50, auto_tune=False):
        self.min_class_count = min_class_count
        self.prob_threshold = prob_threshold
        self.auto_tune = auto_tune
        self._has_clf = self._prod_clf = None
        self._n_train = self._n_classes = 0

    def fit(self, train_labels, rule_fn):
        """Fit the noise gate and the product classifier.

        Args:
            train_labels: DataFrame with `ocr_text` and `product_name` columns.
            rule_fn: Regex rule function used at predict time before the ML head.
        """
        df = train_labels.copy()
        df["ocr_text"] = df["ocr_text"].astype(str).str.strip()
        df["product_name"] = df["product_name"].astype(str).str.strip()
        self._rule_fn = rule_fn
        
        # --- NOISE GATE: binary "does this text mention a product?" ---
        union_has_clf = FeatureUnion([
            ("char_features", TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), max_features=3000, min_df=2)),
            ("word_features", TfidfVectorizer(analyzer="word", ngram_range=(1, 2), max_features=1500, min_df=2))
        ])
        self._has_clf = Pipeline([
            ("union", union_has_clf),
            ("clf", LogisticRegression(C=1.0, max_iter=400, class_weight="balanced")),
        ])
        self._has_clf.fit(df["ocr_text"], (df["product_name"] != "").astype(int))
        
        # --- PRODUCT CLASSIFIER: multi-class product name ---
        pos = df[(df["ocr_text"] != "") & (df["product_name"] != "")]
        keep = pos["product_name"].value_counts()
        keep_all = keep[keep >= self.min_class_count].index
        pos_all = pos[pos["product_name"].isin(keep_all)]
        
        if not len(pos_all):
            return self

        union_prod_clf = FeatureUnion([
            ("char_features", TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), max_features=3000, min_df=2)),
            ("word_features", TfidfVectorizer(analyzer="word", ngram_range=(1, 2), max_features=1500, min_df=2))
        ])
        self._prod_clf = Pipeline([
            ("union", union_prod_clf),
            ("clf", LogisticRegression(C=1.0, max_iter=400, class_weight="balanced")),
        ])
        
        self._prod_clf.fit(pos_all["ocr_text"], pos_all["product_name"])
            
        self._n_train = len(df)
        self._n_classes = pos_all["product_name"].nunique()
        return self

    def predict(self, ocr_text):
        ocr_text = "" if ocr_text is None else str(ocr_text).strip()
        if not ocr_text or self._prod_clf is None:
            return ""
        return str(self._prod_clf.predict([ocr_text])[0])

    def is_product(self, ocr_text):
        if not ocr_text or self._has_clf is None:
            return False
        proba = self._has_clf.predict_proba([ocr_text])[0]
        prod_idx = list(self._has_clf.classes_).index(1)
        return proba[prod_idx] >= self.prob_threshold

    def model_size_mb(self) -> float:
        total = 0
        for clf in (self._has_clf, self._prod_clf):
            if clf is not None:
                total += len(pickle.dumps(clf, protocol=pickle.HIGHEST_PROTOCOL))
        return total / (1024 * 1024)

    def summary(self) -> str:
        return (
            f"ProductPredictor(train={self._n_train}, classes={self._n_classes}, "
            f"size≈{self.model_size_mb():.2f}MB, prob_threshold={self.prob_threshold})"
        )