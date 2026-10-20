# Minimal field mapping: CMS 2023 synthetic RIF release

Source: [CMS Synthetic RIF User Guide, May 2023](https://data.cms.gov/sites/default/files/2023-05/d51e1218-68c3-4c7c-9598-0b81f22fe903/User%20Guide%20-%20CMS%20Synthetic%20RIF%20Files%20May%202023_AM508_v2.pdf).

| Raw file | Field | Purpose | Validation |
|---|---|---|---|
| beneficiary_YYYY.csv | BENE_ID | Synthetic beneficiary identifier | Unique and nonblank |
| beneficiary_YYYY.csv | AGE (fallback BENE_BIRTH_DT) | Cohort age | 0–110; analytical cohort 65+ |
| inpatient.csv / outpatient.csv | BENE_ID | Claim to beneficiary linkage | Nonblank, match rates audited |
| inpatient.csv / outpatient.csv | CLM_ID | Claim ID, repeated across line items | Distinct claim counts |
| inpatient.csv / outpatient.csv | CLM_FROM_DT | Claim year | Exact YYYYMMDD / YYYY-MM-DD parse |
| inpatient.csv / outpatient.csv | CLM_PMT_AMT | Claim-level payment (if present) | Detect conflicts; no line sum |

Pipe-delimited fields require release-specific inspection. Other CMS products, including the older DE-SynPUF, must not be mixed with the 2023 synthetic RIF product. This demonstration intentionally covers only inpatient and outpatient services; full enrollment eligibility is not established.
