import hashlib
import json

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.model_selection import GroupShuffleSplit
from sklearn.preprocessing import StandardScaler


class InterestTrainer:
    def fit(self, rows):
        x = np.asarray([row["features"] for row in rows], dtype=float)
        y = np.asarray([row["label"] for row in rows])
        groups = np.asarray([row["user_id"] for row in rows])
        train, test = next(GroupShuffleSplit(n_splits=1, test_size=.25, random_state=42).split(x, y, groups))
        if len(set(y[train])) < 2 or len(set(y[test])) < 2 or len(test) < 10:
            return {"status": "insufficient_validation_data", "metrics": {"train_rows": len(train), "test_rows": len(test)}, "artifact": {}}
        scaler = StandardScaler().fit(x[train])
        model = LogisticRegression(max_iter=300, random_state=42).fit(scaler.transform(x[train]), y[train])
        scores = model.predict_proba(scaler.transform(x[test]))[:, 1]
        auc = float(roc_auc_score(y[test], scores))
        brier = float(brier_score_loss(y[test], scores))
        baseline = float(brier_score_loss(y[test], np.full(len(test), float(y[train].mean()))))
        metrics = {"auc": round(auc, 4), "brier": round(brier, 4), "baseline_brier": round(baseline, 4),
            "train_rows": len(train), "test_rows": len(test), "split": "held_out_users_seed_42",
            "dataset_hash": hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest(), "active_in_ranking": False}
        return {"status": "validated_shadow" if auc >= .65 and brier < baseline else "needs_review_shadow", "metrics": metrics,
            "artifact": {"coefficients": model.coef_[0].tolist(), "intercept": model.intercept_.tolist(), "mean": scaler.mean_.tolist(), "scale": scaler.scale_.tolist()}}
