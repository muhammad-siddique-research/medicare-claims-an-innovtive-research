"""Beneficiary-year construction and exact claim-level deduplication."""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
import numpy as np
import pandas as pd
from .io import CLAIM_KEY, DATE_KEY, KEY, PAYMENT_KEY, chunks, find_file, parse_claim_dates

@dataclass
class ClaimStats:
    service: str
    rows_seen: int = 0
    distinct_claims: int = 0
    malformed_dates: int = 0
    off_year_rows: int = 0
    missing_key_rows: int = 0
    conflicting_payments: int = 0
    unmatched_beneficiaries: int = 0
    duplicate_claim_lines: int = 0
    payment_present: bool = False
    warnings: list[str] = field(default_factory=list)

def _read_age(beneficiaries: pd.DataFrame, year: int) -> pd.Series:
    if "AGE" in beneficiaries:
        return pd.to_numeric(beneficiaries["AGE"], errors="coerce")
    if "BENE_BIRTH_DT" in beneficiaries:
        born = parse_claim_dates(beneficiaries["BENE_BIRTH_DT"])
        return (year - born.dt.year).astype("float64")
    raise ValueError("Beneficiary file needs AGE or BENE_BIRTH_DT to study aging")

def select_cohort(beneficiaries: pd.DataFrame, year: int, min_age: int):
    """Annual synthetic beneficiaries aged min_age+, not a verified FFS exposure cohort."""
    age = _read_age(beneficiaries, year)
    base = pd.DataFrame({KEY: beneficiaries[KEY].astype("string"), "age": age})
    missing = int(base["age"].isna().sum())
    invalid = int(((base.age < 0) | (base.age > 110)).sum())
    base = base.loc[base.age.between(min_age, 110)].copy()
    if base.empty:
        raise ValueError(f"No beneficiaries ages {min_age}+ found for {year}")
    return base.reset_index(drop=True), {
        "total_beneficiary_rows": len(beneficiaries),
        "cohort_rows": len(base),
        "missing_age_rows": missing,
        "invalid_age_rows": invalid,
        "min_age": min_age,
        "cohort_caveat": (
            "Synthetic enrollment-file inclusion does not establish full-year FFS "
            "exposure or Medicare Advantage status."
        ),
    }

def claims_for_year(path: Path, year: int, service: str, chunk_size: int = 100_000):
    """Deduplicate claim lines by (BENE_ID, CLM_ID), preserving claim-level amounts."""
    stats = ClaimStats(service=service)
    claims: dict[tuple[str, str], float | None] = {}
    uncertain: set[tuple[str, str]] = set()
    for chunk in chunks(path, chunk_size):
        chunk.columns = chunk.columns.str.strip()
        needed = {KEY, CLAIM_KEY, DATE_KEY}
        if not needed.issubset(chunk.columns):
            raise ValueError(f"{path} missing {sorted(needed - set(chunk.columns))}")
        stats.rows_seen += len(chunk)
        stats.payment_present = stats.payment_present or PAYMENT_KEY in chunk.columns
        dates = parse_claim_dates(chunk[DATE_KEY])
        stats.malformed_dates += int(dates.isna().sum())
        valid = dates.notna()
        stats.off_year_rows += int((valid & (dates.dt.year != year)).sum())
        valid &= dates.dt.year.eq(year)
        valid_key = chunk[KEY].ne("") & chunk[CLAIM_KEY].ne("")
        stats.missing_key_rows += int((valid & ~valid_key).sum())
        for item in chunk.loc[valid & valid_key].to_dict("records"):
            key = (str(item[KEY]), str(item[CLAIM_KEY]))
            raw = item.get(PAYMENT_KEY)
            amount = pd.to_numeric(raw, errors="coerce") if raw not in (None, "") else np.nan
            payment = float(amount) if pd.notna(amount) and np.isfinite(amount) else None
            if key in claims:
                stats.duplicate_claim_lines += 1
                previous = claims[key]
                if key not in uncertain and previous is not None and payment is not None:
                    if not np.isclose(previous, payment, rtol=0, atol=0.01):
                        uncertain.add(key)
                        stats.conflicting_payments += 1
                if previous is None and payment is not None:
                    claims[key] = payment
            else:
                claims[key] = payment
    stats.distinct_claims = len(claims)
    if stats.conflicting_payments:
        stats.warnings.append(
            "Conflicting claim-level payment values; omitted affected claims from payment totals."
        )
    frame = pd.DataFrame(
        [
            {KEY: bene, CLAIM_KEY: claim, "payment": None if (bene, claim) in uncertain else amount}
            for (bene, claim), amount in claims.items()
        ],
        columns=[KEY, CLAIM_KEY, "payment"],
    )
    return frame, stats

def construct_panel(
    beneficiaries: pd.DataFrame,
    data_dir: Path,
    year: int,
    min_age: int = 65,
    chunk_size: int = 100_000,
    services: tuple[str, ...] = ("outpatient", "inpatient"),
):
    """Construct one row per beneficiary without many-to-many join inflation."""
    panel, checks = select_cohort(beneficiaries, year, min_age)
    beneficiary_ids = set(panel[KEY])
    qa = {"year": year, **checks, "services": {}}
    for service in services:
        path = find_file(data_dir, f"{service}.csv")
        events, stat = claims_for_year(path, year, service, chunk_size)
        stat.unmatched_beneficiaries = int((~events[KEY].isin(beneficiary_ids)).sum())
        matching = events.loc[events[KEY].isin(beneficiary_ids)]
        counts = matching.groupby(KEY, sort=False)[CLAIM_KEY].size()
        panel[f"{service}_claims"] = panel[KEY].map(counts).fillna(0).astype(int)
        if stat.payment_present:
            payments = matching.groupby(KEY, sort=False)["payment"].sum(min_count=1)
            panel[f"{service}_claim_payment_observed"] = panel[KEY].map(payments)
        qa["services"][service] = {
            key: value for key, value in vars(stat).items() if key != "service"
        }
    if panel[KEY].duplicated().any() or panel[KEY].isna().any():
        raise AssertionError("Panel is not unique by beneficiary identifier")
    return panel, qa
