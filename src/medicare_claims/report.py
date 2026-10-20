"""Aggregate-only research reports with illustrative synthetic-data graphics."""
from __future__ import annotations
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from .models import fit_count_models

def write_outputs(panel: pd.DataFrame, qa: dict, output_dir: Path) -> dict:
    """Write aggregate outputs without beneficiary IDs."""
    output_dir.mkdir(parents=True, exist_ok=True)
    coef, report = fit_count_models(panel)
    coef.to_csv(output_dir / "count_model_coefficients.csv", index=False)
    (output_dir / "data_quality.json").write_text(json.dumps(qa, indent=2), encoding="utf-8")
    (output_dir / "model_diagnostics.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    summary = panel.groupby(
        pd.cut(panel.age, [64, 74, 84, 110], labels=["65–74", "75–84", "85+"]),
        observed=True,
    ).agg(
        beneficiaries=("age", "size"),
        mean_outpatient_claims=("outpatient_claims", "mean"),
        mean_inpatient_claims=("inpatient_claims", "mean"),
    ).reset_index().rename(columns={"age": "age_band"})
    summary.to_csv(output_dir / "aggregate_descriptives.csv", index=False)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(summary["age_band"].astype(str), summary["mean_outpatient_claims"].astype(float))
    ax.set_xlabel("Synthetic beneficiary age group")
    ax.set_ylabel("Mean distinct outpatient claims (synthetic)")
    ax.set_title(f"Technical demonstration: synthetic claims ({qa['year']})")
    fig.tight_layout()
    fig.savefig(output_dir / "outpatient_by_age.png", dpi=160)
    plt.close(fig)
    lines = [
        "# Reproducibility run: synthetic claims demonstration", "",
        f"- Analysis year: **{qa['year']}**",
        f"- Synthetic beneficiary cohort: **{qa['cohort_rows']}** (age >= {qa['min_age']})",
        f"- Poisson dispersion diagnostic: **{report['poisson_pearson_dispersion']:.3f}**",
        f"- Count models: {', '.join(report['models_fitted'])}", "",
        "## Limitations", "",
        "Software/methods demonstration, not a clinical or policy estimate. ",
        "Synthetic data do not permit inference about actual Medicare beneficiaries. ",
        "FFS exposure is not established; zero claims need not imply zero healthcare use.", "",
        "## Quality assurance", "",
    ]
    for service, stat in qa["services"].items():
        lines.append(
            f"- **{service}**: {stat['rows_seen']:,} rows; "
            f"{stat['distinct_claims']:,} distinct claims; "
            f"{stat['duplicate_claim_lines']:,} extra claim-line rows; "
            f"{stat['malformed_dates']:,} malformed dates."
        )
    (output_dir / "RUN_SUMMARY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report
