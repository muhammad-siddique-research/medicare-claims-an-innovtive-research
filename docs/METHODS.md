# Methodological specification and limitations

## Objective
Demonstrate defensible computational analysis on the structure of the **CMS 2023 synthetic Medicare RIF** files. This is a software/research methods project, **not evidence about real healthcare outcomes**.

## Data engineering
- Annual enrollment: one beneficiary row per `BENE_ID` in `beneficiary_YYYY.csv`.
- Claims: `inpatient.csv` and `outpatient.csv`, assigned to the year of `CLM_FROM_DT`.
- Distinct claim key: `(BENE_ID, CLM_ID, service_type)`, not claim-line row count.
- Cohort: synthetic beneficiaries aged at least 65; no unverified fee-for-service exposure eligibility is inferred.
- Payment: `CLM_PMT_AMT` is claim-level, never sum repeating line values. Conflicting amounts are flagged and withheld.
- Data QA: missing IDs, duplicate claim lines, malformed dates, off-year records, unmatched claim records, conflicting payment amounts.

## Econometric demonstration

The model is an illustrative descriptive count regression:

```text
E[Y_i | A_i] = exp(beta_0 + beta_1 * (A_i - 65) / 10)
```

where `Y_i` is the number of observed distinct outpatient claims in the selected year and `A_i` is synthetic beneficiary age.

- Fit Poisson GLM with HC3 robust standard errors; inspect Pearson dispersion.
- Fit NB2 with estimated dispersion when convergence permits.
- The exponentiated age coefficient is an **illustrative synthetic-count association**, not a causal effect or valid Medicare utilization-rate ratio.
- **No offset is included** because verified enrollment/FFS person-time was not established.
- Do not interpret p-values or model comparisons as real-world conclusions.

## Threats to interpretation
1. Source records are **synthetic**, not actual Medicare claims.
2. Missing FFS claims do not mean absence of healthcare use.
3. No complete exposure-time denominator or Medicare Advantage enrollment adjustment.
4. Lines must be collapsed to claims before counting.
5. Claim-start-year allocation is an explicit choice.
6. No causal treatment assignment, quasi-experiment or identification strategy.
7. No external validation on restricted real Medicare data.

## Next steps
Validate the downloaded CMS-supplied synthetic archive, record file hashes and exact row counts; derive coverage months and verified FFS exposure; add age-band, date-assignment and eligibility sensitivity checks; and only consider difference-in-differences if a credible policy research design and suitable data exist.
