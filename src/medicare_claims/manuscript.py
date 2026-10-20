"""Create a Markdown research report from aggregate-only model and QA outputs."""
from __future__ import annotations

from pathlib import Path

import pandas as pd


def write_research_report(qa: dict, diagnostics: pd.DataFrame, output_dir: Path) -> Path:
    """Render a scholarly methods report without beneficiary identifiers."""
    output_dir.mkdir(parents=True, exist_ok=True)
    source_kind = qa.get("source_kind", "unverified_local")
    source_label = (
        "INVENTED TOY FIXTURE (not CMS records)"
        if source_kind == "invented_toy_fixture"
        else "LOCAL INPUTS: OFFICIAL CMS ORIGIN NOT INDEPENDENTLY VERIFIED"
    )
    lines = [
        "# Medicare Claims Integrity Lab — Reproducible Research Report", "",
        "**Status: computational methods demonstration only.** All estimates",
        "are descriptive results from synthetic or unverified local inputs;",
        "not real Medicare findings, causal effects, or national utilization rates.", "",
        f"**Input provenance:** {source_label}.  ",
        f"**Calendar year:** {qa['year']}.  ",
        f"**Beneficiary cohort:** {qa['cohort_rows']:,} records aged {qa['min_age']}+.",
        "",
        "## 1. Research motivation", "",
        "Healthcare claims may contain multiple service lines per unique claim.",
        "Mistaking lines for claims inflates observed counts and may distort",
        "model associations. Accurate analytic grain and denominator validation",
        "are prerequisites for defensible Health Economics research.", "",
        "## 2. Data engineering and quality assurance", "",
        "Claims are deduplicated by beneficiary, claim, and service category.",
        "Invalid dates, unmatched beneficiaries, conflicting payment records,",
        "and line multiplicity are audited. Records are linked to a synthetic",
        "beneficiary-year cohort; FFS person-time is NOT established.", "",
        "| Service | Lines | Unique claims | Extra lines | Invalid dates | Unmatched claims |",
        "|:--|--:|--:|--:|--:|--:|",
    ]
    for name, stat in qa["services"].items():
        lines.append(
            f"| {name.title()} | {stat['rows_seen']:,} | "
            f"{stat['distinct_claims']:,} | {stat['duplicate_claim_lines']:,} | "
            f"{stat['malformed_dates']:,} | {stat['unmatched_beneficiaries']:,} |"
        )
    lines.extend([
        "", "## 3. Econometric specification and results", "",
        "For age in decades X=(age-65)/10, fit log E[Y|X] = beta_0 + beta_1 X.",
        "Poisson GLM uses HC3 robust standard errors; NB2 is attempted for",
        "overdispersion sensitivity. A seeded beneficiary bootstrap illustrates",
        "numerical uncertainty. The exponentiated coefficient is a conditional",
        "COUNT RATIO, NOT an exposure-adjusted incidence-rate ratio.", "",
        "| Service | N | Count ratio | HC3 95% CI | Bootstrap 95% CI | Dispersion | NB2 fitted |",
        "|:--|--:|--:|:--|:--|--:|:--|",
    ])
    for r in diagnostics.itertuples():
        lines.append(
            f"| {r.service.title()} | {r.n:,} | {r.conditional_count_ratio:.3f} | "
            f"[{r.count_ratio_ci_low:.3f}, {r.count_ratio_ci_high:.3f}] | "
            f"[{r.bootstrap_count_ratio_ci_low:.3f}, "
            f"{r.bootstrap_count_ratio_ci_high:.3f}] | "
            f"{r.pearson_dispersion:.2f} | {'Yes' if r.nb2_converged else 'No'} |"
        )
    lines.extend([
        "", "These intervals are conditional on the supplied synthetic data.",
        "Neither confidence intervals nor model-selection statistics resolve",
        "coverage selection, missing utilization, or causal confounding.", "",
        "## 4. Research visualizations", "",
        "### Figure 1. Age coefficient forest plot (HC3 uncertainty)",
        "![Descriptive age count ratios](age_associations_forest.png)", "",
        "### Figure 2. Observed versus predicted outpatient claims",
        "![In-sample outpatient calibration](calibration_outpatient.png)", "",
        "### Figure 3. Observed versus predicted inpatient claims",
        "![In-sample inpatient calibration](calibration_inpatient.png)", "",
        "### Figure 4. Observed versus Poisson-expected zero counts",
        "![Observed and expected zero fractions](observed_vs_expected_zeros.png)", "",
        "Age-band calibration is in-sample. Differences in zeros are screening",
        "diagnostics, not formal zero-inflation hypothesis tests.", "",
        "## 5. Robustness and research limitations", "",
        "- Check Poisson Pearson dispersion, NB2 convergence and same-sample AIC.",
        "- Review 95% HC3 Wald and percentile bootstrap intervals.",
        "- Verify CMS source archive, eligibility, and claim-definition rules before use.",
        "- The current cohort has no validated traditional FFS person-time offset.",
        "- Missing FFS claims do not imply the absence of healthcare use.",
        "- Repeated years would require beneficiary-level clustering.",
        "- No quasi-experiment, treatment effect, or causal effect is identified.",
        "- The present figures are not representative Medicare estimates.", "",
        "## 6. Conclusion", "",
        "The project demonstrates reproducible Python research engineering:",
        "claim granularity, transparent linkage, QA, count models,",
        "statistical sensitivity and interpretable visualization.",
        "It does not establish experience with restricted patient claims",
        "or provide evidence about actual Medicare populations.", "",
        "## 7. Reproducibility", "",
        "All figures and numerical results are regenerated by the CLI.",
        "See the input audit, advanced diagnostics CSV and provenance JSON.",
        "Consult the comprehensive econometric note in the docs directory.", "",
        "## References (APA 7th edition)", "",
        "Benchimol, E. I., Smeeth, L., Guttmann, A., Harron, K.,",
        "Moher, D., Petersen, I., Sørensen, H. T., von Elm, E., &",
        "Langan, S. M. (2015). The REporting of studies Conducted",
        "using Observational Routinely-collected health Data (RECORD)",
        "statement. PLOS Medicine, 12(10), e1001885.",
        "https://doi.org/10.1371/journal.pmed.1001885", "",
        "Cameron, A. C., & Trivedi, P. K. (2013). Regression analysis",
        "of count data (2nd ed.). Cambridge University Press.",
        "https://cameron.econ.ucdavis.edu/racd2/", "",
        "Centers for Medicare & Medicaid Services. (2023). Synthetic",
        "Medicare enrollment, fee-for-service claims, and prescription",
        "drug event data public use file: User guide.",
        "https://data.cms.gov/collection/synthetic-medicare-enrollment-fee-for-service-claims-and-prescription-drug-event",
    ])
    path = output_dir / "RESEARCH_REPORT.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
