# Known-Truth Computational Experiment — Reproducible Illustration

**Status:** seeded simulation illustration; no CMS data or actual patients were analyzed. Do **not** cite these numerical findings as a Medicare empirical result.

## Question

Can claim-line multiplicity—particularly if associated with a beneficiary characteristic—distort an Econometric estimate when analysts count claim lines rather than distinct claims?

## Prespecified simulation

- 600 **invented** beneficiaries per replication; ages 65–95.
- 80 paired Monte Carlo replications, pseudorandom seed **20261020**.
- Known data-generating age coefficient: **0.180** log-count units per decade.
- Correct counts: beneficiary-level draws from a Poisson model.
- Naive counts: treating deliberately added claim lines as if they were claims.
- Comparator 1: an age-independent chance of one additional claim line.
- Comparator 2: a chance of one additional claim line increasing with age.
- Estimator: the same Poisson log-mean model in both counting methods.

## Simulation results

| Quantity | Age-independent line multiplicity | Age-dependent line multiplicity |
|---|---:|---:|
| Replications | 80 | 80 |
| True artificial age coefficient | 0.180 | 0.180 |
| Mean fitted coefficient, **correct claim count** | 0.1782 | 0.1782 |
| Mean fitted coefficient, **naive line count** | 0.1780 | **0.2898** |
| Mean absolute coefficient error, corrected counts | 0.0265 | 0.0265 |
| Mean absolute coefficient error, naive counts | 0.0270 | **0.1098** |
| Mean naive lines / correct claims | 1.1395 | **1.3567** |

The table summarizes an independent local execution of the **equivalent seeded algorithm** documented in `src/medicare_claims/stress_test.py`; values are rounded to four decimals. The public research reproducibility path is to execute the committed module and compare its `simulation_summary.csv` values. This report does **not** certify that the current GitHub Actions jobs or the full CMS ingestion pipeline have passed; those statuses must be checked separately.

## Interpretation

The independent-multiplicity comparator increases the counted number of events but leaves the *average age slope* close to the artificial true parameter under these simulated conditions. When claim-line multiplicity rises with age by design, the naive age coefficient is higher than the correctly constructed coefficient. In this example, treating lines as claims yields mean absolute coefficient error about **4.15 times** the corrected-count error (0.109789 / 0.026452); this ratio is **not a generalizable effect size**.

The example demonstrates an identifiable software failure mode: incorrect aggregation can misrepresent both count levels and associations. It cannot establish how frequently this happens in official Medicare data, whether any real analyst made such an error, or what the implications are for real healthcare expenditure or aging.

## Reproduction

```powershell
python -m pip install -e ".[dev]"
python -m medicare_claims.stress_test --output-dir reports/stress_test --n-beneficiaries 600 --replications 80 --seed 20261020
python -m pytest -q
```

Inspect `reports/stress_test/simulation_metadata.json`, `simulation_summary.csv` and `claim_granularity_stress_test.png`.

**Limits:** uncertainty intervals for Monte Carlo averages were not calculated in this example; the multiplicity mechanisms are deliberately uncalibrated and toy scale. No Fee-for-Service enrollment exposure or causal identification is attempted.

**Relevant methodology:** [Full study, hypotheses, mathematical notation, and references](RESEARCH_STUDY.md).
