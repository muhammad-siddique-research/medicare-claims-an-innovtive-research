"""Descriptive count models; synthetic-data estimates have no clinical meaning."""
from __future__ import annotations
import warnings
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.discrete.discrete_model import NegativeBinomial

def fit_count_models(panel: pd.DataFrame, outcome: str = "outpatient_claims"):
    """HC3-robust Poisson and estimated-dispersion NB2 models, no causal interpretation."""
    if outcome not in panel.columns:
        raise ValueError(f"Outcome not found: {outcome}")
    frame = panel[["age", outcome]].dropna().copy()
    frame["age_per_decade"] = (frame["age"] - 65.0) / 10.0
    if len(frame) < 10 or frame["age_per_decade"].nunique() < 2:
        raise ValueError("Need >= 10 rows and age variation for the count models")
    if not (frame[outcome] >= 0).all():
        raise ValueError("Claim counts must be nonnegative")
    y = frame[outcome].astype(float)
    X = sm.add_constant(frame[["age_per_decade"]].astype(float), has_constant="add")
    poisson = sm.GLM(y, X, family=sm.families.Poisson()).fit(cov_type="HC3")
    dispersion = float(sum(poisson.resid_pearson**2) / max(len(frame) - len(X.columns), 1))
    fitted = [("Poisson (HC3)", poisson, ["const", "age_per_decade"])]
    try:
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            nb = NegativeBinomial(y, X, loglike_method="nb2").fit(disp=False, maxiter=200)
        if nb.mle_retvals.get("converged", False) and np.isfinite(nb.params).all():
            fitted.append(("Negative binomial (NB2)", nb, list(nb.params.index)))
        else:
            warnings.warn("NB2 did not converge; reporting robust Poisson only.", stacklevel=2)
    except (ValueError, np.linalg.LinAlgError, RuntimeError, OverflowError) as exc:
        warnings.warn(f"NB2 not estimable: {exc}", stacklevel=2)
    records = []
    for name, result, terms in fitted:
        for term in terms:
            coef = float(result.params[term])
            records.append({
                "model": name, "term": term, "coefficient": coef,
                "std_error": float(result.bse[term]),
                "exponentiated_coefficient": float(np.exp(coef)) if term != "alpha" else np.nan,
                "n": len(frame), "aic": float(result.aic),
            })
    description = {
        "n_analysis": int(len(frame)), "outcome": outcome,
        "mean_claims": float(y.mean()),
        "share_zero_claims": float((y == 0).mean()),
        "poisson_pearson_dispersion": dispersion,
        "models_fitted": [x[0] for x in fitted],
        "interpretation": (
            "Synthetic-data technical demonstration only. Estimates, p-values and "
            "model comparisons cannot support real Medicare conclusions."
        ),
        "caveats": [
            "No verified FFS enrollment-time exposure offset.",
            "Unobserved claims need not mean zero healthcare utilization.",
            "Descriptive age association, not a causal effect.",
            "Only selected services and claim-start-year allocation.",
        ],
    }
    return pd.DataFrame.from_records(records), description
