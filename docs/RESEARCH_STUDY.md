# Claim Granularity, Measurement Error, and Reproducible Medicare-Style Claims Analytics

**A computational methods study and research-engineering demonstration**  
**Status (20 October 2026):** implementation with invented Monte Carlo data; full official CMS synthetic-file validation pending. **Not a completed empirical Medicare study.**

## Structured abstract

**Background.** Administrative health records may contain multiple service lines for one healthcare claim. An analyst who confuses claim lines with distinct claims may bias utilization counts, and the distortion of regression coefficients depends on whether line multiplicity covaries with modeled characteristics. More broadly, administrative claims research requires defensible denominator definitions, transparent linkage, and honest reporting of missing coverage (Virnig & Parsons, 2021; Benchimol et al., 2015).

**Objective.** Develop a transparent, reproducible Python workflow that (i) constructs distinct claim-level measures from Medicare-like files, (ii) audits records and claim-level payments, and (iii) tests a specific measurement-error mechanism using a controlled simulation with known data-generating parameters.

**Design.** Software verification with invented fixtures, plus two-arm Monte Carlo stress testing. The candidate real-world dataset is the CMS Synthetic Medicare Enrollment, Fee-for-Service Claims, and Prescription Drug Event Data Public Use File. The repository has **not yet been validated on the downloaded official dataset**.

**Contribution.** An executable *claim-granularity stress-test protocol* that compares correctly aggregated claim counts with naive claim-line counts under age-independent and age-dependent line multiplicity. This is a proposed methodological teaching and benchmarking contribution, **not a claim of being the first such method**.

**Interpretation.** The test examines software measurement sensitivity, **not** real Medicare utilization, clinical outcomes, health inequities, treatment effects, or policy impacts.

## 1. Motivation and defensible research gap

Health Economics studies often require transforming payment-oriented administrative data into meaningful measures of patient utilization. Claims capture reimbursed or billable events and can omit services, clinical severity, and information needed for population-wide inference. The RECORD statement emphasizes reporting data cleaning, linkage, variable derivation, and sensitivity analyses (Benchimol et al., 2015). Recent research has also demonstrated that commercial claims estimates may differ from appropriate population benchmarks (Dahlen et al., 2024), although that study addresses *coverage and selection bias*, not the exact claim-line error tested here.

**Practical methodological question:** How sensitive is an estimated age–utilization association to a mistaken unit of analysis (claim line versus distinct claim), especially if line multiplicity itself varies with age?

The literature supports the *importance* of transparent data processing. A comprehensive novelty claim has **not** been established. This portfolio targets an inspectable engineering and pedagogical gap: a unit-tested, end-to-end example that makes one consequential analytic choice falsifiable using known truth.

### Proposed contribution versus established methods

- **Established:** beneficiary linkage, claim deduplication, Poisson/NB2 count models, robust uncertainty, transparent QA reporting.
- **Contribution of this repository:** combines these components with a seeded error-mechanism stress test and explicit contrast between naive line counting and correct claim counting.
- **Not contributed:** a new count estimator, a new identification strategy, a clinically validated algorithm, a Medicare policy-effect estimate, or representative synthetic-data generation.

## 2. Testable hypotheses and refutation

- **H1 (mechanical inflation):** When a claim can contribute more than one line, counting lines instead of claims overstates the total number of claims by construction. **Refuted** if the implementation incorrectly finds fewer lines than distinct claims in the specified nonmissing simulated records.
- **H2 (differential measurement bias):** When the probability of an additional line rises with age, naive line-based Poisson age slopes tend to exceed slopes from correctly counted claims in the prespecified simulated process. **Refuted** for that process if repeated simulation does not establish the anticipated positive slope shift.
- **H3 (nondifferential comparator):** Under age-independent multiplicity, the naive count *level* increases, while the age-slope shift should be much smaller, on average, under the simulated model. **Refuted** if the slope distortion is comparable to the age-dependent arm across adequately powered replications.

These are hypotheses about **artificially specified data-generation mechanisms**; they are not empirical propositions about actual Medicare claims.

## 3. Data sources and reproducibility

1. **Official candidate dataset:** CMS 2023 Synthetic Medicare RIF Public Use Files (not included with project; users must download from CMS).
2. **Invented integration fixture:** 100 toy beneficiaries with generated enrollment, inpatient and outpatient claims, deliberately duplicated line-level records.
3. **Monte Carlo benchmark:** independent from both the official CMS release and the 100-beneficiary fixture; generates invented count outcomes with a known coefficient.

Identifiers are treated as strings; current import is pipe-delimited and chunked. **Scope of official-data pipeline:** beneficiary age 65+, annual claim-start year, inpatient and outpatient records. No Medicare Advantage or full-year Fee-for-Service exposure is presumed. No protected health information is used or redistributed.

## 4. Computational architecture and claim construction

### 4.1 Grain of the analytic tables

Let raw record `r` contain beneficiary `B_r`, claim `C_r`, service category `S_r`, and claim start date `D_r`. Define the claim key:

```text
K_r = (B_r, C_r, S_r)
```

The distinct observed annual claim count for beneficiary `i` and service `s` is:

```text
Y_is(t) = | { (B,C,s) : B = i, year(D) = t } |
```

Rows describing multiple billable lines within the *same* claim do not increase `Y_is(t)`. Claims from different service types are not accidentally collapsed together.

**Audits:** missing keys, malformed dates, off-year rows, line multiplicity, unmatched beneficiary IDs and inconsistent claim-level payment fields. The project does not blindly sum a repeated `CLM_PMT_AMT` across all lines. Payment discrepancies are flagged; affected claims are omitted from payment summaries.

### 4.2 Analytic cohort and denominator caveat

The present cohort is an annual synthetic enrollment-file cross-section with observed age at least 65. It is **not** demonstrated to be a full-calendar-year Fee-for-Service population. Without verified months of eligibility and coverage, the project reports *observed claim counts* rather than utilization rates per person-year.

A later credible exposure-adjusted specification would require:

```text
log E[Y_it | X_it, T_it] = log(T_it) + beta_0 + X_it' beta
```

where `T_it` is **validated Fee-for-Service person-time**, not a guessed offset. The present code does **not** insert an artificial offset.

## 5. Baseline econometric specification

For the illustrative cohort, define age in decades `X_i = (Age_i - 65) / 10`. The descriptive model is

```text
E[Y_i | X_i] = exp(beta_0 + beta_1 X_i).
```

The existing Python implementation estimates Poisson GLM with HC3 heteroskedasticity-robust uncertainty, checks Pearson dispersion, and attempts a negative-binomial NB2 model when convergence permits (Cameron & Trivedi, 2013). It records convergence and modeling limitations.

**Interpretation:** `exp(beta_1)` would represent a conditional synthetic-count ratio for a ten-year age difference **under the model**. It is not a causal effect, a generalizable Medicare rate ratio, or a demonstrated response to a policy intervention. HC3 robustness does not repair eligibility-related selection, missing utilization, or outcome mismeasurement.

## 6. Designed experiment: claim-granularity stress test

A separately executable simulation tests a known mechanism, not facts in real administrative data.

For synthetic individual `i` in replication `b`:

```text
X_i ~ discrete age-in-decades induced by Age_i ~ UniformInteger(65,95)

Y_i | X_i ~ Poisson(mu_i)
log(mu_i) = log(1.4) + 0.18 X_i

L_ij = 1 + Bernoulli(p_i), for j = 1,...,Y_i
Z_i = sum_j L_ij.
```

Here `Y_i` is the **correct number of invented claims**, `L_ij` is the invented number of lines for claim `j`, and `Z_i` is the **naively counted number of lines**.

Two prespecified regimes:

```text
A. Uniform:          p_i = logistic(-1.8)
B. Age-differential: p_i = logistic(-1.8 + 0.7 X_i).
```

Fit the same Poisson model to `Y_i` and `Z_i`; compare `beta_hat_correct` and `beta_hat_naive` with the known synthetic truth `beta_1 = 0.18`.

**Evaluation measures:** average estimated slope, mean absolute estimation error relative to the *known simulated* coefficient, and mean ratio of naive lines to correct claims. Distinguish the level inflation `sum Z_i / sum Y_i` from slope distortion. The comparisons are paired within replications because the underlying `Y_i` and covariates are shared.

**Suggested primary configuration:** fixed seed 20261020; 600 beneficiaries per replicate; 80 replicates per regime. The uncalibrated `0.7` differential-multiplicity parameter was chosen to create a detectable stress case, **not** to approximate real Medicare billing.

### Run the experiment

```bash
python -m medicare_claims.stress_test --n-beneficiaries 600 --replications 80 --seed 20261020 --output-dir reports/stress_test
```

Outputs: `simulation_replications.csv`, `simulation_summary.csv`, `simulation_metadata.json`, and `claim_granularity_stress_test.png`. Results are deterministic *for the documented environment and seed*, allowing practical reproducibility audits.

### Sensitivity analyses recommended for further development

Vary `n` (e.g., 300, 600, 1200); multiplicity–age slope (0, 0.35, 0.7, 1.05); mean claim incidence; rare claims and excess zeros; and missing claim keys. Check whether the slope distortion changes direction and uncertainty at different design points. Repeated simulations are not equivalent to external validation against real claims.

## 7. Technical validation and validity threats

Automated tests should verify: duplicate-line collapse across chunks; conflicting payments are flagged; cohort keys remain unique; absent outcome records are handled consistently; Monte Carlo experiments are seeded; scenarios are balanced; and the age-differential simulation can detect a prespecified slope change.

**Internal validity of simulation:** true data-generation parameters are known; stress-test assumptions are disclosed. The simulation can reveal a code error or demonstrate a possible bias mechanism, but it cannot identify an actual prevalence of such errors.

**External validity:** none is claimed. Official CMS synthetic data are not representative evidence of clinical or policy effects. Synthetic RIF data are for development and analytical familiarity. Neither those data nor invented fixtures validate population-level interpretations.

**Other threats:** uncertain Medicare Advantage/FFS enrollment, imperfect diagnosis ascertainment, claim processing delays, incident vs. prevalent conditions, left truncation, payment definitions, time-varying disease severity, missing coverage, and denominator mismatch. A real causal study would require explicit intervention, assignment mechanism, comparability assumptions, and appropriate data.

**Engineering limitations:** all observed claims are retained in memory as unique keys after chunked input, so input chunking alone does not guarantee out-of-core scalability. For true national datasets, a SQL/DuckDB/Arrow group-by implementation, partition validation, unit tests and benchmarked memory ceilings would be preferable.

## 8. Conclusions

This project establishes a **testable methods demonstration** in Python for research using Medicare-style claims schemas. It combines proper claim-level aggregation, beneficiary linkage, payment and date integrity checks, count-model diagnostics, and a controlled experiment distinguishing line-level counting from claim-level counting.

**The defensible result is the existence of a reproducible test design—not evidence of Medicare utilization patterns or an original empirical discovery.** If the seeded simulation shows larger slope distortion when multiplicity is age-dependent, that will confirm the behavior of the *specified simulation* and motivate analogous auditing in approved claims settings. It will not quantify real-world clinical or policy bias.

**Before scholarly submission or claims-specific job presentation:** run the official CMS archive, verify exact schema and hashes, publish non-sensitive aggregate quality checks, execute expanded parameter sweeps, review literature systematically, and seek independent reproduction.

## References (APA 7th edition)

Benchimol, E. I., Smeeth, L., Guttmann, A., Harron, K., Moher, D., Petersen, I., Sørensen, H. T., von Elm, E., & Langan, S. M. (2015). The REporting of studies Conducted using Observational Routinely-collected health Data (RECORD) statement. *PLOS Medicine, 12*(10), e1001885. https://doi.org/10.1371/journal.pmed.1001885

Cameron, A. C., & Trivedi, P. K. (2013). *Regression analysis of count data* (2nd ed.). Cambridge University Press. https://cameron.econ.ucdavis.edu/racd2/

Centers for Medicare & Medicaid Services. (2023). *Synthetic Medicare enrollment, fee-for-service claims, and prescription drug event data public use file: User guide*. https://data.cms.gov/sites/default/files/2023-05/d51e1218-68c3-4c7c-9598-0b81f22fe903/User%20Guide%20-%20CMS%20Synthetic%20RIF%20Files%20May%202023_AM508_v2.pdf

Dahlen, A., Deng, Y., & Charu, V. (2024). *Benchmarking commercial healthcare claims data* [Preprint]. medRxiv. https://doi.org/10.1101/2024.08.19.24312249

Virnig, B., & Parsons, H. (2021, March 16). *Strengths and limitations of CMS administrative data in research*. Research Data Assistance Center. https://www.resdac.org/articles/strengths-and-limitations-cms-administrative-data-research

**Source differentiation:** CMS explains the synthetic source; Benchimol et al. address administrative-data reporting; Cameron and Trivedi cover econometrics; Virnig and Parsons discuss claims content and enrollment; Dahlen et al. examine a *different*, selection-related claims-data bias. None of these sources directly proves the novelty or empirical validity of the repository's proposed line-granularity stress test.
