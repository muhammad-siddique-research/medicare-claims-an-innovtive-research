"""Expanded descriptive Econometrics: independently reproducible aggregate outputs.

Every output is synthetic-data-only and uses observed claim *counts*, not
person-time utilization rates or causal effects. No beneficiary identifiers
are written to disk.
"""
from __future__ import annotations

import json
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.discrete.discrete_model import NegativeBinomial


AGE_BREAKS = (64, 74, 84, 110)
AGE_LABELS = ("65–74", "75–84", "85+")


def _prepare(panel: pd.DataFrame, service: str) -> pd.DataFrame:
    outcome = f"{service}_claims"
    if "age" not in panel or outcome not in panel:
        raise ValueError(f"Missing age or {outcome}")
    frame = panel[["age", outcome]].copy()
    frame["age"] = pd.to_numeric(frame["age"], errors="coerce")
    frame[outcome] = pd.to_numeric(frame[outcome], errors="coerce")
    frame = frame.dropna()
    if len(frame) < 30 or frame.age.nunique() < 3:
        raise ValueError(f"Need >=30 complete observations and age variation for {service}")
    if not np.isfinite(frame[["age", outcome]].to_numpy()).all():
        raise ValueError("Age and claim counts must be finite")
    if not frame.age.between(65, 110).all():
        raise ValueError("Age must be between 65 and 110")
    if (frame[outcome] < 0).any() or not np.allclose(
        frame[outcome], np.round(frame[outcome])
    ):
        raise ValueError("Claim counts must be nonnegative integers")
    frame["age_per_decade"] = (frame.age - 65.0) / 10.0
    return frame


def _bootstrap_ci(
    y: np.ndarray, x: np.ndarray, replications: int, seed: int
) -> tuple[float, float, int]:
    """IID beneficiary bootstrap; assumes independent single-year observations."""
    rng = np.random.default_rng(seed)
    slopes = []
    for _ in range(replications):
        sampled = rng.integers(0, len(y), size=len(y))
        if np.unique(x[sampled]).size < 2:
            continue
        X = sm.add_constant(x[sampled], has_constant="add")
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                fit = sm.GLM(y[sampled], X, family=sm.families.Poisson()).fit(
                    disp=0, maxiter=100
                )
            if np.isfinite(fit.params[1]):
                slopes.append(float(fit.params[1]))
        except (ValueError, RuntimeError, np.linalg.LinAlgError):
            continue
    if len(slopes) < max(8, replications // 2):
        return float("nan"), float("nan"), len(slopes)
    return (
        float(np.quantile(np.exp(slopes), 0.025)),
        float(np.quantile(np.exp(slopes), 0.975)),
        len(slopes),
    )


def _calibration_plot(table: pd.DataFrame, service: str, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 4.6))
    x = np.arange(len(table))
    ax.plot(x, table["mean_observed"], "o-", linewidth=2, label="Observed counts")
    ax.plot(x, table["mean_poisson_fitted"], "s--", linewidth=2, label="Poisson fitted")
    ax.set_xticks(x, table["age_band"].astype(str))
    ax.set_xlabel("Synthetic beneficiary age band")
    ax.set_ylabel(f"Mean distinct {service} claims (not a rate)")
    ax.set_title(f"Descriptive age-band calibration: {service.upper()}")
    ax.legend()
    ax.grid(axis="y", alpha=0.2)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def _forest_plot(results: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for i, row in enumerate(results.itertuples()):
        ax.errorbar(
            row.conditional_count_ratio, i,
            xerr=[[row.conditional_count_ratio - row.count_ratio_ci_low],
                  [row.count_ratio_ci_high - row.conditional_count_ratio]],
            fmt="o", capsize=5, markersize=8,
        )
    ax.axvline(1, linestyle="--", linewidth=1.2)
    ax.set_yticks(range(len(results)), results["service"].str.title())
    ax.set_xlabel("Exp(age coefficient): count ratio per decade, 95% HC3 Wald CI")
    ax.set_title("Descriptive synthetic claim counts — NOT causal or population estimates")
    ax.grid(axis="x", alpha=0.2)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def _zero_plot(results: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 4.5))
    x = np.arange(len(results))
    ax.bar(x - 0.18, results["observed_zero_fraction"], width=0.36, label="Observed")
    ax.bar(x + 0.18, results["poisson_expected_zero_fraction"], width=0.36,
           label="Model expected")
    ax.set_xticks(x, results["service"].str.title())
    ax.set_ylabel("Fraction of beneficiaries with zero observed claims")
    ax.set_ylim(0, 1)
    ax.set_title("Zero counts: descriptive model adequacy check (synthetic)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def run_advanced_analyses(
    panel: pd.DataFrame,
    output_dir: Path,
    bootstrap_replications: int = 150,
    seed: int = 20261020,
) -> pd.DataFrame:
    """Publish aggregate inference tables and plots for both claim service types.

    HC3 Wald and IID bootstrap intervals quantify model uncertainty *conditional
    on the synthetic sample*, not real-world uncertainty. AIC values compare
    likelihood specifications on the same records but do not establish causation.
    """
    if bootstrap_replications < 10:
        raise ValueError("bootstrap_replications must be >=10")
    output_dir.mkdir(parents=True, exist_ok=True)
    records = []
    for service_num, service in enumerate(("outpatient", "inpatient")):
        frame = _prepare(panel, service)
        outcome = f"{service}_claims"
        y = frame[outcome].to_numpy(dtype=float)
        x = frame["age_per_decade"].to_numpy(dtype=float)
        X = sm.add_constant(x, has_constant="add")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            fit = sm.GLM(y, X, family=sm.families.Poisson()).fit(cov_type="HC3")
            null = sm.GLM(
                y, np.ones((len(y), 1)), family=sm.families.Poisson()
            ).fit()
        beta, se = float(fit.params[1]), float(fit.bse[1])
        mu = np.asarray(fit.predict(X), dtype=float)
        pearson = float(np.sum((y - mu) ** 2 / np.maximum(mu, 1e-12)) / (len(y) - 2))
        ci_l, ci_u = beta - 1.9599639845 * se, beta + 1.9599639845 * se
        boot_l, boot_u, boots_ok = _bootstrap_ci(
            y, x, bootstrap_replications, seed + service_num
        )
        nb_aic, nb_alpha, nb_converged = np.nan, np.nan, False
        if y.mean() > 0:
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    nb = NegativeBinomial(y, X, loglike_method="nb2").fit(
                        disp=False, maxiter=200
                    )
                nb_converged = bool(nb.mle_retvals.get("converged", False))
                if nb_converged and np.isfinite(nb.params).all():
                    nb_aic, nb_alpha = float(nb.aic), float(nb.params[-1])
                else:
                    nb_converged = False
            except (ValueError, RuntimeError, OverflowError, np.linalg.LinAlgError):
                nb_converged = False
        records.append({
            "service": service, "n": len(y), "mean_observed_claims": float(y.mean()),
            "coefficient_per_decade": beta, "hc3_standard_error": se,
            "conditional_count_ratio": float(np.exp(beta)),
            "count_ratio_ci_low": float(np.exp(ci_l)),
            "count_ratio_ci_high": float(np.exp(ci_u)),
            "bootstrap_count_ratio_ci_low": boot_l, "bootstrap_count_ratio_ci_high": boot_u,
            "bootstrap_successful_replications": boots_ok,
            "poisson_aic": float(fit.aic), "intercept_only_poisson_aic": float(null.aic),
            "nb2_aic": nb_aic, "nb2_alpha": nb_alpha,
            "nb2_converged": nb_converged,
            "pearson_dispersion": pearson,
            "observed_zero_fraction": float(np.mean(y == 0)),
            "poisson_expected_zero_fraction": float(np.mean(np.exp(-mu))),
        })
        groups = pd.cut(frame["age"], AGE_BREAKS, labels=AGE_LABELS)
        calibration = pd.DataFrame({
            "age_band": groups, "observed": y, "poisson_fitted": mu
        }).groupby("age_band", observed=True).agg(
            n=("observed", "size"),
            mean_observed=("observed", "mean"),
            mean_poisson_fitted=("poisson_fitted", "mean"),
        ).reset_index()
        calibration.to_csv(
            output_dir / f"calibration_{service}.csv", index=False
        )
        _calibration_plot(
            calibration, service, output_dir / f"calibration_{service}.png"
        )

    summary = pd.DataFrame.from_records(records)
    summary.to_csv(output_dir / "advanced_econometric_diagnostics.csv", index=False)
    _forest_plot(summary, output_dir / "age_associations_forest.png")
    _zero_plot(summary, output_dir / "observed_vs_expected_zeros.png")
    metadata = {
        "data_inference": "synthetic source only; descriptive and illustrative",
        "source_verification": "verify input directory with RUN_SUMMARY and CMS guide",
        "models": "Poisson HC3, intercept-only Poisson; NB2 if converged",
        "bootstrap": {
            "design": "IID beneficiary resampling of one-year observations",
            "replications_requested": bootstrap_replications,
            "seed": seed,
            "purpose": "model sensitivity, NOT external validation",
        },
        "uncertainty": "95% Wald interval and percentile bootstrap conditional on data",
        "limitations": [
            "No established Fee-for-Service enrollment person-time or offset.",
            "Counts are not clinical utilization rates; zeros may reflect missing coverage.",
            "Age is a descriptive association, not a treatment.",
            "No claim of policy effects, representative prevalence, or causal inference.",
            "NB2 AIC and Poisson AIC are descriptive model comparisons only.",
            "Age grouping/calibration is in-sample and may overstate generalization.",
        ],
    }
    (output_dir / "advanced_econometric_provenance.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    return summary
