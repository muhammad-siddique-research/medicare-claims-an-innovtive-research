"""Monte Carlo falsification exercise for claim-line counting errors.

Uses entirely invented beneficiary counts and line multiplicity. It does not
sample, estimate, validate, or reproduce actual Medicare utilization.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm


def _fit_slope(outcome: np.ndarray, age_decades: np.ndarray) -> float:
    """Fit the same Poisson log-mean model to correctly and incorrectly counted events."""
    design = sm.add_constant(age_decades)
    model = sm.GLM(outcome, design, family=sm.families.Poisson())
    return float(model.fit().params[1])


def run_experiment(
    n_beneficiaries: int = 600,
    replications: int = 80,
    seed: int = 20261020,
    true_beta: float = 0.18,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Compare claim counts to claim-line counts under two explicit error regimes.

    Each simulated claim has either one or two lines. The uniform-error regime
    makes duplication independent of age; the differential-error regime makes
    duplication probability increase with age. Neither regime is CMS-calibrated.
    """
    if n_beneficiaries < 30 or replications < 2:
        raise ValueError("Require at least 30 beneficiaries and two replications")
    rng = np.random.default_rng(seed)
    records: list[dict[str, object]] = []
    for replication in range(replications):
        age = rng.integers(65, 96, size=n_beneficiaries)
        decades = (age.astype(float) - 65.0) / 10.0
        mean_claims = np.exp(np.log(1.4) + true_beta * decades)
        true_claim_counts = rng.poisson(mean_claims)
        corrected = _fit_slope(true_claim_counts, decades)
        for scenario in ("uniform", "age_differential"):
            linear = np.full(n_beneficiaries, -1.8)
            if scenario == "age_differential":
                linear += 0.7 * decades
            extra_line_probability = 1.0 / (1.0 + np.exp(-linear))
            additional_lines = rng.binomial(true_claim_counts, extra_line_probability)
            observed_line_counts = true_claim_counts + additional_lines
            naive = _fit_slope(observed_line_counts, decades)
            records.append(
                {
                    "replication": replication + 1,
                    "scenario": scenario,
                    "true_beta": true_beta,
                    "corrected_beta": corrected,
                    "naive_line_beta": naive,
                    "corrected_absolute_error": abs(corrected - true_beta),
                    "naive_absolute_error": abs(naive - true_beta),
                    "true_claims_total": int(true_claim_counts.sum()),
                    "naive_lines_total": int(observed_line_counts.sum()),
                    "claim_count_inflation_ratio": float(
                        observed_line_counts.sum() / true_claim_counts.sum()
                    ),
                }
            )
    draws = pd.DataFrame.from_records(records)
    summary = (
        draws.groupby("scenario", as_index=False)
        .agg(
            replications=("replication", "size"),
            mean_corrected_beta=("corrected_beta", "mean"),
            mean_naive_beta=("naive_line_beta", "mean"),
            mean_corrected_absolute_error=("corrected_absolute_error", "mean"),
            mean_naive_absolute_error=("naive_absolute_error", "mean"),
            mean_line_to_claim_ratio=("claim_count_inflation_ratio", "mean"),
        )
    )
    summary.insert(1, "true_beta", true_beta)
    return draws, summary


def write_experiment(
    output_dir: Path,
    n_beneficiaries: int = 600,
    replications: int = 80,
    seed: int = 20261020,
) -> pd.DataFrame:
    """Persist aggregate demonstration artifacts; never create patient records."""
    draws, summary = run_experiment(n_beneficiaries, replications, seed)
    output_dir.mkdir(parents=True, exist_ok=True)
    draws.to_csv(output_dir / "simulation_replications.csv", index=False)
    summary.to_csv(output_dir / "simulation_summary.csv", index=False)
    metadata = {
        "evidence_type": "fully simulated / invented",
        "cms_data_used": False,
        "clinical_or_policy_inference": False,
        "seed": seed,
        "n_beneficiaries_per_replication": n_beneficiaries,
        "replications_per_scenario": replications,
        "line_multiplicity": "each hypothetical claim has one or two lines",
        "scenarios": {
            "uniform": "Pr(extra line) = logistic(-1.8)",
            "age_differential": "Pr(extra line) = logistic(-1.8 + 0.7 * age_decades)",
        },
        "true_log_rate_slope_per_decade": 0.18,
        "meaning": (
            "Demonstrates potential estimation errors caused by treating claim "
            "lines as claims; not empirical evidence of errors in actual CMS data."
        ),
    }
    (output_dir / "simulation_metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    fig, ax = plt.subplots(figsize=(8, 5))
    order = ["uniform", "age_differential"]
    for index, scenario in enumerate(order):
        frame = draws.loc[draws["scenario"] == scenario]
        ax.scatter(
            np.full(len(frame), index - 0.13),
            frame["corrected_beta"],
            s=9, alpha=0.25, label="Claim-level" if index == 0 else None,
        )
        ax.scatter(
            np.full(len(frame), index + 0.13),
            frame["naive_line_beta"],
            s=9, alpha=0.25, label="Naive line-level" if index == 0 else None,
        )
        ax.plot([index - 0.19, index - 0.07], [frame["corrected_beta"].mean()] * 2, lw=3)
        ax.plot([index + 0.07, index + 0.19], [frame["naive_line_beta"].mean()] * 2, lw=3)
    ax.axhline(0.18, linestyle="--", linewidth=1.2, label="True simulated slope")
    ax.set_xticks([0, 1], ["Uniform multiplicity", "Age-dependent multiplicity"])
    ax.set_ylabel("Estimated log-rate coefficient per decade")
    ax.set_title("Claim granularity stress test — INVENTED DATA ONLY")
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(output_dir / "claim_granularity_stress_test.png", dpi=160)
    plt.close(fig)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Synthetic claim-granularity Monte Carlo")
    parser.add_argument("--output-dir", type=Path, default=Path("reports/stress_test"))
    parser.add_argument("--n-beneficiaries", type=int, default=600)
    parser.add_argument("--replications", type=int, default=80)
    parser.add_argument("--seed", type=int, default=20261020)
    args = parser.parse_args()
    summary = write_experiment(
        args.output_dir, args.n_beneficiaries, args.replications, args.seed
    )
    print(summary.to_string(index=False))
    print("SIMULATION ONLY: No CMS records, real patients, or causal estimates were used.")


if __name__ == "__main__":
    main()
