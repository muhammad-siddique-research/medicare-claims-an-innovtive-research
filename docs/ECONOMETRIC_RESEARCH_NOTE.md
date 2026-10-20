# Econometric Research Note: Claims Measurement, Model Diagnostics, and Inference

**Project:** Medicare Claims Integrity Lab  
**Analysis:** Python-based synthetic-claims methods and computational validation  
**Research stage:** Reproducible methods demonstration; validation on the full official CMS synthetic archive remains pending  
**Scope:** Observed *claim counts*, not population-level utilization rates or causal treatment effects

## 1. Research motivation and the estimand

Administrative healthcare claims are stored for processing and reimbursement. An encounter, a billable claim, and a *claim line* are not necessarily interchangeable units. For Medicare-style inpatient and outpatient files, several rows may refer to one claim. The immediate engineering challenge is to build the correct analytic grain **before** fitting Econometric models.

Let \(B_r\), \(C_r\), and \(S_r\) identify a beneficiary, claim, and service category for source row \(r\). The analysis key is \((B_r,C_r,S_r)\), with calendar year assigned from the claim start date. For beneficiary \(i\), service \(s\), and year \(t\), define:

\[
Y_{ist}=\sum_{c}\mathbf{1}\{\exists r:B_r=i,C_r=c,S_r=s,\operatorname{year}(D_r)=t\}.
\]

The **naive line count** is instead \(Z_{ist}=\sum_r\mathbf{1}\{B_r=i,S_r=s,\operatorname{year}(D_r)=t\}\). The difference \(Z-Y\) measures repeated source lines, not necessarily duplicate visits. In the included toy simulation every line belongs to a claim and \(Z\ge Y\) by construction; real source anomalies may require further adjudication.

The implemented descriptive estimand is the **age-associated difference in expected observed claims in a synthetic beneficiary-year record**. It is *not* a Medicare rate per beneficiary-year with verified FFS exposure, nor a measure of healthcare need.

## 2. Cohort definition and exposure

The script selects synthetic annual enrollment records aged at least 65 in the selected year. It counts observed inpatient and outpatient claims in that year. Eligibility for full-year traditional fee-for-service coverage has **not** been established from monthly enrollment fields. As a result, the project does **not** calculate person-time rates.

An appropriate rate model, conditional on validated traditional Medicare FFS exposure \(T_{it}>0\), would take the form:

\[
E[Y_{it}\mid \mathbf X_{it},T_{it}]
 = T_{it}\exp(\beta_0+\mathbf X_{it}^{\top}\boldsymbol\beta),
\qquad
\log E[Y_{it}\mid\cdot]=\log T_{it}+\beta_0+\mathbf X_{it}^{\top}\boldsymbol\beta.
\]

The offset \(\log T_{it}\) **must not be inserted until eligible exposure has been constructed and audited**. Claims missing due to Medicare Advantage enrollment or incomplete observation may not be treated as proof of non-use.

## 3. Baseline count regression

For age \(A_i\) measured in years, define \(X_i=(A_i-65)/10\). For each service separately:

\[
E[Y_i\mid X_i]=\mu_i=\exp(\beta_0+\beta_1X_i).
\]

The implemented baseline is a Poisson Generalized Linear Model (GLM) with HC3 heteroskedasticity-consistent standard errors. Poisson specifies a log-linear conditional mean and, as a full likelihood, assumes equality of conditional mean and variance. HC3 changes covariance estimation, **not** the point estimates or the correctness of the conditional-mean specification.

The Wald interval on the count-ratio scale is:

\[
CR_{10}=\exp(\widehat{\beta}_1),\quad
CI_{95\%}=\exp\left[
\widehat{\beta}_1\pm 1.96\,SE_{HC3}(\widehat{\beta}_1)
\right].
\]

This exponentiated coefficient is called a **conditional count ratio per age decade**, rather than an incidence-rate ratio (IRR), because the current data do not provide a validated exposure denominator.

**Avoid causal language:** Age is associated with claims but not assigned experimentally; selective coverage, comorbidity, cohort effects, and data-generation rules can all influence the comparison.

## 4. Model adequacy and alternatives

### 4.1 Overdispersion

Compute Pearson dispersion

\[
\widehat{\phi}=\frac{1}{n-p}\sum_i\frac{(Y_i-\widehat{\mu}_i)^2}{\widehat{\mu}_i},
\]

where \(p\) is the number of fitted mean parameters. Values substantially above one motivate investigation of overdispersion. This statistic is a **diagnostic, not a formal significance test**. Values substantially below one also warrant investigation.

### 4.2 Negative binomial (NB2) sensitivity

The NB2 model uses a log mean and the variance function

\[
\operatorname{Var}(Y_i\mid X_i)=\mu_i+\alpha\mu_i^2,\qquad\alpha>0.
\]

The implementation fits an estimated-dispersion NB2 model where possible, records its convergence status, and exports its AIC. Failed convergence is not concealed or reinterpreted as evidence favoring Poisson. Comparisons are limited to the same outcome and analytic cohort.

A lower AIC provides **relative in-sample likelihood fit**, not proof of external validity or causal identification. Formal model choice would additionally examine residuals, specification tests, out-of-sample performance, and research objectives.

### 4.3 Excess zeros

Report observed zero fraction

\[
\widehat{p}_0=\frac{1}{n}\sum_i\mathbf1\{Y_i=0\},
\]

versus the Poisson-implied mean zero probability

\[
\widehat{p}_{0,P}=\frac{1}{n}\sum_i\exp(-\widehat{\mu}_i).
\]

Discrepancies are **screening diagnostics**, not formal proof that a zero-inflated model is necessary. A zero claim in this release may reflect enrollment and claims observation, not absence of need or care.

### 4.4 Age-band calibration

Plot mean observed and fitted synthetic claim counts for ages 65–74, 75–84, and 85+. This is **in-sample descriptive calibration**; it can mask within-band lack of fit. Cross-validated or temporally separated validation is recommended when a real prediction task becomes possible.

## 5. Uncertainty and resampling

**HC3 Wald interval:** uncertainty conditional on the synthetic cohort and chosen model.

**Percentile beneficiary bootstrap:** draw beneficiaries with replacement, refit the Poisson model, and take the 2.5th and 97.5th percentiles of exponentiated coefficients. The default is 150 seeded replicates for the simple one-year toy analysis. This is **an illustrative numerical stability check**, not publication-grade precision; increase repetitions to at least 1,000 and examine Monte Carlo error for substantive analysis.

The current bootstrap assumes **independent beneficiary observations**. For longitudinal CMS research, resampling must occur at the beneficiary (or relevant cluster) level across repeated years; this repository's single-year implementation does not yet address that problem. Robust standard errors and bootstrap intervals do not correct selection or measurement bias.

## 6. Controlled measurement-error stress test

The secondary experiment deliberately **does not use the CMS files**. It generates a known artificial count process:

\[
Y_i\mid X_i\sim\operatorname{Poisson}(\mu_i),\quad
\log\mu_i=\log(1.4)+0.18X_i.
\]

For each invented claim \(j\), an additional line appears with probability \(p_i\):

\[
L_{ij}=1+\operatorname{Bernoulli}(p_i),\qquad
Z_i=\sum_{j=1}^{Y_i}L_{ij}.
\]

Scenarios:

- **Age-independent:** \(p_i=\operatorname{logit}^{-1}(-1.8)\).
- **Age-dependent:** \(p_i=\operatorname{logit}^{-1}(-1.8+0.7X_i)\).

The same Poisson model is fitted to \(Y_i\) and \(Z_i\), holding the true simulated age coefficient at \(0.18\). Primary outcomes are bias \(\overline{\widehat{\beta}}-\beta\), mean absolute error, and the claim-line inflation ratio. The code reports these per replication and as scenario summaries.

Under the stated data-generating process,

\[
E[Z_i\mid X_i]=E[Y_i\mid X_i]\{1+p_i\}.
\]

Therefore,

\[
\log E[Z_i\mid X_i]
= \log(1.4)+0.18X_i+\log(1+p_i).
\]

**Analytic implication:** when \(p_i\) is constant, line counting changes the intercept but not the true age slope. When \(p_i\) varies with age, the extra term induces slope distortion; the naive log mean is generally not exactly linear in age. This analytical decomposition motivates the simulation and clarifies *why* the comparator scenarios differ. It is a methodological illustration, not a new causal estimator or evidence of errors in genuine Medicare research.

The simulation is not calibrated to CMS billing complexity and contains no realistic disease process. It is intended to test an **error mechanism** under known truth.

## 7. Visualization and interpretation

The reproducible CLI creates, in the selected run's output directory:

| Figure / file | What it shows | What it cannot prove |
|---|---|---|
| \`outpatient_by_age.png\` | Mean observed synthetic outpatient claims by age band | Medicare utilization rates |
| \`age_associations_forest.png\` | Conditional count ratios with 95% HC3 Wald intervals, both services | Causal effects |
| \`calibration_outpatient.png\` / \`calibration_inpatient.png\` | Age-band fitted-versus-observed means | Out-of-sample generalizability |
| \`observed_vs_expected_zeros.png\` | Observed and Poisson-predicted zero fractions | Formal excess-zero hypothesis test |
| \`advanced_econometric_diagnostics.csv\` | Coefficients, robust SE, bootstrap CI, AIC, dispersion, zeros | National Medicare parameters |
| \`data_quality.json\` | Claim-line collapse and missingness audits | Quality of unavailable real data |
| \`simulation_summary.csv\` and stress-test figure | Paired Monte Carlo coefficients under known truth | Actual claims-data biases |

**Provenance:** plots from the fixture are generated by code and labeled synthetic/toy. No patient-level outputs are committed. An illustrative **static** schematic in the README is derived from an independently reported simulation run, not from actual CMS beneficiaries.

## 8. Validity, falsification, and robustness checklist

- **Grain integrity:** verify that each unique \((BENE\_ID, CLM\_ID, S)\) produces one distinct claim; audit line multiplicity.
- **Input integrity:** retain leading zeros; validate dates, payment conflicts, unmatched claims, and denominator membership.
- **Preprocessing sensitivity:** test alternative claim dates, inclusion restrictions, and partial-year exposure once data fields permit.
- **Model sensitivity:** compare baseline Poisson, robust inference, NB2 and observed-versus-predicted counts.
- **Statistical sensitivity:** increase bootstrap repetitions; report uncertainty of Monte Carlo simulation averages, not just point estimates.
- **Design sensitivity:** vary age-dependent line probability, mean claim incidence, sample size, and zero generation.
- **Predictive validation:** only use cross-validation when a predictive target and clearly partitioned data are defined.
- **Causal inference:** no difference-in-differences or instrumental-variable estimate is claimed. A future policy evaluation requires a concrete intervention, timing, assignment structure, credible counterfactual, no-anticipation and appropriate identification checks.

## 9. Interpretation and conclusion

The code demonstrates reproducible **measurement integrity**, descriptive count-data estimation, and design-based computational testing. Its strongest methodological point is not that more sophisticated estimators automatically produce valid Health Economics conclusions; it is that the **definition of the analytic unit and exposure precedes valid inference**.

A careful health-economics reviewer should regard the repository as evidence of transferable quantitative programming and research design skills, **not** prior professional experience handling restricted Medicare patient-level claims or a completed research paper. Credibility depends on an independently verified run using official CMS-supplied *synthetic* files, source hashes, transparent exclusions, repeated tests and clearly differentiated interpretations.

## References (APA 7th edition)

Benchimol, E. I., Smeeth, L., Guttmann, A., Harron, K., Moher, D., Petersen, I., Sørensen, H. T., von Elm, E., & Langan, S. M. (2015). The REporting of studies Conducted using Observational Routinely-collected health Data (RECORD) statement. *PLOS Medicine, 12*(10), e1001885. https://doi.org/10.1371/journal.pmed.1001885

Cameron, A. C., & Trivedi, P. K. (2013). *Regression analysis of count data* (2nd ed.). Cambridge University Press. https://cameron.econ.ucdavis.edu/racd2/

Centers for Medicare & Medicaid Services. (2023). *Synthetic Medicare enrollment, fee-for-service claims, and prescription drug event data public use file: User guide*. https://data.cms.gov/sites/default/files/2023-05/d51e1218-68c3-4c7c-9598-0b81f22fe903/User%20Guide%20-%20CMS%20Synthetic%20RIF%20Files%20May%202023_AM508_v2.pdf

**Reporting standard:** RECORD, an extension of STROBE, supports transparent descriptions of routinely collected administrative data. A completed empirical paper would need substantially more design-specific reporting than this code demonstration.
