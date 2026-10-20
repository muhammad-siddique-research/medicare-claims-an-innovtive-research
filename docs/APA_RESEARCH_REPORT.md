# From Claims to Credible Evidence
## Claim-Granularity Measurement Error and Reproducible Count-Data Econometrics: A Python Research Demonstration

**Study type:** Computational methods demonstration; controlled simulation and claims-compatible software engineering  
**Research domains:** Health Economics; Applied Econometrics; Administrative Data Science; Reproducible Research  
**Version:** October 20, 2026  
**Evidence status:** Official CMS synthetic data product and documentation identified; repository-level official-file analysis **not yet verified**. Numerical findings below are from **fully invented Monte Carlo data**, not CMS analyses.

## Abstract

**Background.** Administrative claims may be recorded with multiple service lines per claim. Confusing claim lines with unique claims inflates event counts mechanically; if the number of lines differs systematically by covariates, estimated associations may also shift. Reproducible research therefore requires explicit accounting units, record-linkage audits, transparent denominators, and sensitivity analysis.

**Objective.** Build a Python-based claims research pipeline and a known-truth simulation that tests how line-level counting errors may alter descriptive age–claim-count associations.

**Methods.** A claim-processing framework reads synthetic Medicare Research Identifiable File (RIF)–style tables, validates identifiers and dates, aggregates unique inpatient and outpatient claims by beneficiary, and estimates Poisson count models with HC3 robust uncertainty, supplementary NB2 specifications when estimable, bootstrap uncertainty, and model-adequacy diagnostics. Separately, a seeded Monte Carlo experiment draws invented beneficiary-level Poisson claim counts under a known age coefficient and introduces either age-independent or age-dependent claim-line multiplicity. Correct claim counts and naive line counts are modeled using the same specification.

**Results.** In the illustrative previously documented 80-replication experiment, the true artificial age log-count coefficient was 0.180. Under age-dependent line multiplicity, the mean naive coefficient was 0.2898, compared with 0.1782 using correct counts. Under age-independent multiplicity, the corresponding means were 0.1780 and 0.1782. These are **simulated results only**; their exact reproduction should be checked by executing the committed Python module.

**Conclusion.** The methods demonstration illustrates a plausible measurement-error mechanism and supports a reproducible audit workflow. It provides no evidence of actual Medicare utilization, policy effects, or the frequency of line-counting errors in real claims.

**Keywords:** Medicare; Claims Data; Administrative Data; Health Economics; Poisson Regression; Negative Binomial Regression; Monte Carlo Simulation; Measurement Error; Reproducibility.

---

## Introduction and research motivation

Health Economics increasingly relies on administrative claims to study health service use, spending, insurance design, and aging. Although claims offer longitudinal and fine-grained descriptions of reimbursed care, they originate in administrative processes rather than clinical trial measurement systems. Data cleaning, completeness, linkage, denominators, and variable construction therefore determine what the resulting estimates mean. The RECORD guideline recommends transparency about routinely collected health-data design, cleaning, and selection (Benchimol et al., 2015).

Two separate concerns motivate this project. First, **data structure**: a single claim may contain multiple billable lines, while the substantive outcome of interest may be a count of *distinct claims*. Second, **population coverage**: claims collected from a selected insurance population need not measure all care or represent the target population. Dahlen et al. (2025) empirically examine the latter generalizability concern in *commercial* claims. Their findings do not validate or calibrate the present line-multiplicity experiment; the papers are cited for distinct reasons.

The present project focuses narrowly on the first concern and **does not claim first discovery or proven novelty**. Its portfolio-level contribution is the auditable combination of a CMS-schema-oriented ETL pipeline, basic count-data Econometrics, a known-truth failure-mode experiment, reporting, and automated checks.

## Research questions and falsifiable hypotheses

**RQ1.** Does treating claim lines as separate claims inflate event totals when the true data-generating structure permits multiple lines per claim?

**RQ2.** How does age-dependent line multiplicity, compared with age-independent multiplicity, change a naive Poisson age coefficient relative to a correctly counted outcome?

**RQ3.** Do expanded diagnostics—robust confidence intervals, bootstrap sensitivity, Pearson dispersion, zero-count calibration, and age-band observed-versus-fitted checks—reveal relevant aspects of model adequacy under the artificial demonstration?

**H1.** In the prespecified mechanism, total line counts weakly exceed total unique claim counts; the inequality is strict when any claim has multiple lines.

**H2.** With a positive age gradient in extra line probability, naive line-based regression generally overstates the prespecified age log-count slope relative to correct claim counts across repeated simulations.

**H3.** With age-independent extra line probability, the main effect is an intercept/count-level increase; the average slope distortion is smaller than in H2.

These are *simulation hypotheses*. Their scope is bounded by the synthetic data-generating process. A hypothesis about real Medicare prevalence or causal effects would require new data and a separate design.

## Data and reproducible provenance

### Official reference source

The reference source is the Centers for Medicare & Medicaid Services (CMS) **Synthetic Medicare Enrollment, Fee-for-Service Claims, and Prescription Drug Event Data** (2023 RIF-format release). CMS supplies simulated records to support familiarity with Medicare-like claims and technical workflows. This is a real official *source of synthetic data*, **not real beneficiaries or representative healthcare outcomes**.

The analytical code expects a selected `beneficiary_YYYY.csv`, `inpatient.csv`, and `outpatient.csv` in the release documented by the repository, using pipe delimiters and identifiers maintained as strings. Field-level applicability must be cross-checked against the actual release before an official-data run is certified. This project currently reports no verified aggregate result from those source files.

### Entirely invented computational datasets

The software integration fixture contains 100 generated beneficiaries and claims. The independent Monte Carlo experiment generates beneficiary ages, claim counts, and artificial line multiplicity under disclosed parameters. Both are fully invented and suitable for code testing, not scientific conclusions about a health population.

### Unit of observation and analytical safeguards

Define `BENE_ID` as beneficiary identifier, `CLM_ID` as claim identifier, `S` as service type, and `t` as claim-start year. An observed claim is uniquely counted using `(BENE_ID, CLM_ID, S)`. The initial cohort comprises synthetic beneficiaries ages 65+ present in the chosen annual enrollment file. It is **not** assumed to represent continuous Fee-for-Service coverage.

An absent claim is coded as no **observed claim in the files**, not as a proof of no healthcare services. Without verified person-time `T_it`, the outcome is a *count*, not an exposure-adjusted rate. Payment fields are handled as potentially repeated claim-level quantities; inconsistent line-level payments are flagged, not silently summed.

## Econometric specification

### Primary descriptive count model

Let `Y_is` be unique observed claims of service `s` for beneficiary `i`; let `X_i = (age_i − 65)/10`.

```math
Y_{is}\mid X_i \sim \mathrm{Poisson}(\mu_{is}),\qquad
\log\mu_{is}=\beta_{0s}+\beta_{1s}X_i.
```

The exponentiated parameter `exp(β₁s)` is a **conditional count ratio for a decade of age difference**, conditional on the modeled assumptions and synthetic data. Because validated enrollment duration is unavailable, it should **not** be labeled an incidence rate ratio. Age is observational; this parameter is **not causal**.

The model reports HC3 heteroskedasticity-robust Wald standard errors and 95% confidence intervals. These do not correct selection, omissions, misclassified exposure, structural misspecification, or the artificiality of data. An intercept-only Poisson model serves as an uncomplicated likelihood comparator.

### Overdispersion and NB2 alternative

A Poisson mean–variance equality `Var(Y|X)=E(Y|X)` may fail. The Pearson diagnostic is

```math
\widehat\phi=\frac{\sum_i(Y_i-\widehat\mu_i)^2/\widehat\mu_i}{n-p}.
```

As an illustrative alternative, negative-binomial NB2 specifies

```math
\operatorname{Var}(Y_i\mid X_i)=\mu_i+\alpha\mu_i^2,\qquad \alpha\geq0.
```

Where NB2 converges, its estimated dispersion and AIC are reported. An improvement in AIC is **not** evidence of a substantive health finding. Poisson HC3 remains useful for robust mean-model interpretation, provided the conditional mean is appropriately specified.

### Bootstrap sensitivity

Using a fixed seed, beneficiaries are resampled with replacement to construct a nonparametric percentile interval for the Poisson **count ratio**. This assumes cross-sectional sampling independence for the current simulation. In real longitudinal research, beneficiary-level clustered resampling would be needed, and any organization/provider correlations would require an appropriate design.

### Model-adequacy graphics

The output pipeline produces (a) a coefficient/95% HC3 interval chart for inpatient and outpatient counts; (b) in-sample age-band observed-versus-Poisson-fitted mean count comparisons; and (c) observed-versus-Poisson-expected fractions of zero claim counts. Together these illustrate model interpretability and inadequacy, but they are not a substitute for out-of-sample calibration, exposure adjustment, or causal validity.

### Exposure-adjusted extension (not implemented without valid data)

A scientifically defensible claims *rate* model would use verified Fee-for-Service exposure `T_it`:

```math
\log E(Y_{it}\mid X_{it},T_{it})=\log T_{it}+\beta_0+X_{it}^{\mathsf T}\beta.
```

**No imputed enrollment offset has been inserted** into the current models.

## Monte Carlo validation experiment

For replication `b`, synthetic `age_i` is sampled uniformly from integers 65 through 95, `X_i=(age_i-65)/10`, and

```math
Y_i\sim\mathrm{Poisson}\left(\exp\{\log(1.4)+0.18X_i\}\right).
```

For each true claim `j=1,...,Y_i`, an additional claim line is generated:

```math
L_{ij}=1+\mathrm{Bernoulli}(p_i),\quad Z_i=\sum_{j=1}^{Y_i}L_{ij}.
```

Here `Y_i` is the correct count and `Z_i` is the incorrect line count. Two regimes are examined:

```math
p_i^{\mathrm{independent}}=\operatorname{logit}^{-1}(-1.8),\qquad
p_i^{\mathrm{dependent}}=\operatorname{logit}^{-1}(-1.8+0.7X_i).
```

Correct `Y_i` and incorrect `Z_i` outcomes receive the same Poisson age specification. The main metrics are mean slope, absolute parameter error against the *known artificial coefficient 0.18*, and the naive-to-correct total-count ratio. The replications are paired for the two count definitions. Parameters were **not calibrated to CMS**.

## Illustrative results (invented Monte Carlo data only)

| Metric | Age-independent multiplicity | Age-dependent multiplicity |
|---|---:|---:|
| Replications per scenario | 80 | 80 |
| True slope imposed by simulation | 0.1800 | 0.1800 |
| Mean slope: correct unique claims | 0.1782 | 0.1782 |
| Mean slope: naive line counts | 0.1780 | 0.2898 |
| Mean absolute slope error: correct counts | 0.0265 | 0.0265 |
| Mean absolute slope error: naive counts | 0.0270 | 0.1098 |
| Mean naive lines / unique claims | 1.1395 | 1.3567 |

*Note.* These figures summarize an earlier independently executed implementation of the documented seeded simulation; the repository generates repeatable `simulation_summary.csv` and `simulation_replications.csv` when executed. No CMS source files were used to produce the figures. The run should be repeated in the target environment before numerical results are presented as fully replicated.

### Results interpretation

In the artificially age-independent regime, naive counts are higher than correct counts, yet mean age slopes are similar. In the artificially age-dependent regime, the naive slope is meaningfully larger than the known data-generation slope. The difference illustrates a possible **covariate-dependent measurement-error mechanism**. It does not establish that line counting errors exist at any particular frequency in real Medicare research, nor is it evidence about patient aging or treatments.

## Internal and external validity

**Internal validity of the designed simulation** comes from a known data-generating process, documented pseudo-random seed, fixed contrasts, and software checks. Failure to recover the anticipated difference should prompt verification of the simulation mechanism, optimizer behavior, sample size, and implementation.

**Construct validity** depends on carefully distinguishing claims, services, claim lines, healthcare visits, and individuals. A unique claim is *not necessarily* a unique clinical encounter. Consequently this project avoids describing distinct claim counts as numbers of medical visits.

**External validity** is not established. Official CMS synthetic RIF records do not replicate actual disease distributions, policies, or healthcare utilization. Moreover, sampling and coverage issues that arise in actual claims data must be addressed with appropriate enrollment and reference populations (Dahlen et al., 2025).

**Causal identification** is absent. A descriptive age coefficient cannot be interpreted as the effect of aging, a policy, Medicare enrollment, or any intervention. A genuine difference-in-differences design would first require a well-defined policy change, comparison group, parallel-trends assessment and suitable longitudinal data.

## Limitations, research integrity, and planned validation

The software currently loads distinct claim keys in memory even though raw input is chunked, so it is **not a fully out-of-core national-claims implementation**. A future production extension could use database-backed deduplication. The annual enrollment extract does not establish Fee-for-Service months or continuous enrollment. Claim-start-year assignment is a transparent, but contestable, convention; alternative service-year and overlap allocation could be assessed. No medical diagnosis prevalence claims, expenditure trends, patient identification, or intervention-effect claims are warranted.

A strong official-data validation should record file versions, file hashes, observed column names, missingness, join match rates, raw line counts, unique claims, contradictory payments, exposure eligibility, and non-sensitive aggregate descriptive outputs. All results would still be **synthetic-data findings**, not generalizable Medicare inference.

## Conclusion

This repository demonstrates disciplined **claims data engineering**, **descriptive Applied Econometrics**, **Monte Carlo validation**, and **transparent research reporting** in Python. Its key methodological lesson is that a seemingly small aggregation decision can affect both event totals and estimated conditional associations when the error process is covariate-dependent. The work is suitable as a technical portfolio demonstration and foundation for future collaborative health-economics research—not as a peer-reviewed empirical Medicare finding or substitute for experience with restricted claims databases.

## References

Benchimol, E. I., Smeeth, L., Guttmann, A., Harron, K., Moher, D., Petersen, I., Sørensen, H. T., von Elm, E., & Langan, S. M. (2015). The REporting of studies Conducted using Observational Routinely-collected health Data (RECORD) statement. *PLOS Medicine, 12*(10), Article e1001885. https://doi.org/10.1371/journal.pmed.1001885

Cameron, A. C., & Trivedi, P. K. (2013). *Regression analysis of count data* (2nd ed.). Cambridge University Press. https://doi.org/10.1017/CBO9781139013567

Centers for Medicare & Medicaid Services. (2023). *Synthetic Medicare enrollment, fee-for-service claims, and prescription drug event data public use file: User guide*. https://data.cms.gov/sites/default/files/2023-05/d51e1218-68c3-4c7c-9598-0b81f22fe903/User%20Guide%20-%20CMS%20Synthetic%20RIF%20Files%20May%202023_AM508_v2.pdf

Centers for Medicare & Medicaid Services. (n.d.). *Synthetic Medicare enrollment, fee-for-service claims, and prescription drug event data* [Data collection]. https://data.cms.gov/collection/synthetic-medicare-enrollment-fee-for-service-claims-and-prescription-drug-event

Dahlen, A., Deng, Y., & Charu, V. (2025). Evaluating the generalizability of commercial healthcare claims data. *American Journal of Epidemiology, 194*(10), 2999–3006. https://doi.org/10.1093/aje/kwaf142

**APA 7 convention:** Citations and references identify the dataset provider and established methodological research. Numerical simulation results here are generated project artifacts—not external sources or evidence of peer-reviewed acceptance.
