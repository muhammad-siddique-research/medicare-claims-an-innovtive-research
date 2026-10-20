# Research Portfolio Brief
### Medicare Claims Integrity Lab — Computational Health Economics

**Portfolio type:** Independent Python research-engineering and Econometric methods demonstration  
**Research interests:** Health Economics · Aging · Healthcare Utilization · Administrative Data Quality · Reproducible Research

## Executive overview

**Research question:** What happens to descriptive healthcare utilization measures and fitted count-model age associations when claim lines are mistakenly treated as unique claims?

The project tackles a consequential upstream issue in health administrative data research: *data construction is part of the Econometric identification and measurement problem.* It implements a synthetic Medicare-style beneficiary/claims linkage pipeline, followed by regression diagnostics and a known-truth Monte Carlo experiment that separates mechanical line-count inflation from covariate-dependent coefficient distortion.

**Dataset provenance:** The reference specification is a genuine official CMS synthetic RIF release. The repository **has not yet been validated using the downloaded full CMS dataset**. Current reported experiment results use separately invented computer-generated data; no identifiable patient data or actual Medicare outcomes are analyzed.

## Technical and research contributions

| Area | Implemented evidence |
|---|---|
| Health administrative data engineering | Key-preserving ingestion, claim-line collapse, beneficiary-level aggregation, audit of dates, missing keys and payment conflicts |
| Applied Econometrics | Poisson log-link GLM with HC3 robust covariance; NB2 sensitivity when estimable; age count-ratio interpretation |
| Model assessment | Pearson dispersion, AIC comparisons, zero-count diagnostics and in-sample age-band calibration |
| Uncertainty quantification | HC3 Wald intervals and seeded beneficiary-bootstrap percentile intervals |
| Simulation methodology | Paired known-truth Monte Carlo scenarios with age-independent and age-dependent claim-line multiplicity |
| Computational reproducibility | Python packaging, deterministic random seeds, tests, continuous integration, aggregate-only research reports |

## Research results: explicitly simulated, not real Medicare estimates

The known-truth simulation generates 600 invented beneficiaries in each of 80 replications, with a true age slope of **0.180** log counts per decade.

| Comparison | Correct claims | Naive claim lines |
|---|---:|---:|
| Average slope, age-independent multiplicity | 0.1782 | 0.1780 |
| Average slope, age-dependent multiplicity | 0.1782 | 0.2898 |

These results are a **computational demonstration of possible measurement bias under deliberately specified assumptions**. They neither quantify the frequency of actual Medicare billing errors nor establish causal effects, novel statistical theory, or real-world associations.

The analytic mechanism is transparent: if \(Y\) counts claims and \(Z\) counts claim lines, with an extra line on a claim occurring with conditional probability \(p(X)\), then

\[
E[Z\mid X]=E[Y\mid X]\{1+p(X)\}.
\]

When \(p(X)\) is constant, the multiplicative error changes the log-model intercept; when \(p(X)\) varies with \(X\), the log mean gains a covariate-varying term and coefficients may shift.

## Reproduce and evaluate the work

Install with Python 3.10+ and run the toy-data regression and Monte Carlo experiments:

~~~bash
python -m pip install -e ".[dev]"
python -m medicare_claims.cli make-fixture --dest data/toy
python -m medicare_claims.cli run --data-dir data/toy --year 2022 --output-dir reports/toy
python -m medicare_claims.stress_test --n-beneficiaries 600 --replications 80 --seed 20261020
pytest -q
~~~

The generated report, **RESEARCH_REPORT.md**, includes an aggregated QA table, count-model estimates, bootstrap intervals, embedded figures, interpretation, limitations, and references. Review current GitHub Actions tests and downloadable **invented-data** figure artifacts in the Actions tab.

**Technical limitations:** Limited to observed claim counts without validated traditional Fee-for-Service coverage person-time. Input chunking still retains unique claims in memory. Claims cannot independently distinguish an absent service from one missing because of incomplete insurance observation. Longitudinal dependence and policy counterfactuals are not modeled.

## Evidence-based professional positioning

This portfolio legitimately supports claims of **transferable Applied Econometrics, Python research programming, synthetic claims-data workflow design, robust statistical diagnostics, and reproducible computational analysis**. It must **not** be presented as extensive prior experience with restricted Medicare claims or as a completed empirical clinical study.

A strong next milestone for an Indiana University research application is to execute and inspect the *official CMS-supplied synthetic* RIF archive, record its checksums and file versions, audit traditional Fee-for-Service exposure, and publish aggregate diagnostics. A complementary R pipeline would more directly address the position's explicit R requirement.

**Read:** [Full Research Study](RESEARCH_STUDY.md) · [Econometric Research Note](ECONOMETRIC_RESEARCH_NOTE.md) · [Simulation Results](SIMULATION_RESULTS.md)

## Selected references (APA 7th edition)

Benchimol, E. I., Smeeth, L., Guttmann, A., Harron, K., Moher, D., Petersen, I., Sørensen, H. T., von Elm, E., & Langan, S. M. (2015). The REporting of studies Conducted using Observational Routinely-collected health Data (RECORD) statement. *PLOS Medicine, 12*(10), e1001885. https://doi.org/10.1371/journal.pmed.1001885

Cameron, A. C., & Trivedi, P. K. (2013). *Regression analysis of count data* (2nd ed.). Cambridge University Press. https://cameron.econ.ucdavis.edu/racd2/

Centers for Medicare & Medicaid Services. (2023). *Synthetic Medicare enrollment, fee-for-service claims, and prescription drug event data public use file: User guide*. https://data.cms.gov/sites/default/files/2023-05/d51e1218-68c3-4c7c-9598-0b81f22fe903/User%20Guide%20-%20CMS%20Synthetic%20RIF%20Files%20May%202023_AM508_v2.pdf
