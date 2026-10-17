"""Metrics used to compare automated scores with human scores (all on 0-10)."""
import numpy as np
from scipy.stats import pearsonr, spearmanr
from sklearn.metrics import cohen_kappa_score, mean_absolute_error, mean_squared_error

HUMAN_WEIGHTS = {"correctness": 0.4, "relevance": 0.2, "completeness": 0.4}  # project plan, section 11


def human_overall(row) -> float:
    return sum(w * row[c] for c, w in HUMAN_WEIGHTS.items())


def mae(y_true, y_pred):
    return float(mean_absolute_error(y_true, y_pred))


def rmse(y_true, y_pred):
    return float(np.sqrt(mean_squared_error(y_true, y_pred)))


def pearson(y_true, y_pred):
    if np.std(y_pred) == 0 or np.std(y_true) == 0:
        return float("nan")
    return float(pearsonr(y_true, y_pred)[0])


def spearman(y_true, y_pred):
    if np.std(y_pred) == 0 or np.std(y_true) == 0:
        return float("nan")
    return float(spearmanr(y_true, y_pred)[0])


def within(y_true, y_pred, tol=1.0):
    """% of answers where the two scores are within `tol` points — the 'agreement' metric."""
    return float(np.mean(np.abs(np.asarray(y_true) - np.asarray(y_pred)) <= tol) * 100)


def weighted_kappa(a, b):
    """Quadratic-weighted Cohen's kappa on scores rounded to whole numbers (0-10)."""
    a = np.clip(np.rint(a), 0, 10).astype(int)
    b = np.clip(np.rint(b), 0, 10).astype(int)
    return float(cohen_kappa_score(a, b, weights="quadratic", labels=list(range(11))))


def all_metrics(y_true, y_pred) -> dict:
    return {
        "MAE": mae(y_true, y_pred),
        "RMSE": rmse(y_true, y_pred),
        "Pearson": pearson(y_true, y_pred),
        "Spearman": spearman(y_true, y_pred),
        "Within ±1 (%)": within(y_true, y_pred),
    }
