"""Input discovery and safe parsing of pipe-delimited CMS synthetic RIF extracts."""
from __future__ import annotations
from pathlib import Path
import pandas as pd

KEY = "BENE_ID"
CLAIM_KEY = "CLM_ID"
DATE_KEY = "CLM_FROM_DT"
PAYMENT_KEY = "CLM_PMT_AMT"

def find_file(data_dir: Path, basename: str) -> Path:
    """Locate exactly one requested CMS file, including nested extraction folders."""
    matches = sorted(data_dir.rglob(basename))
    if not matches:
        raise FileNotFoundError(f"Missing {basename} under {data_dir}; see README.md")
    if len(matches) > 1:
        raise ValueError(f"Multiple matches for {basename}: {matches}; isolate one CMS release")
    return matches[0]

def chunks(path: Path, chunk_size: int = 100_000):
    """Read only needed fields while preserving identifiers and codes as strings."""
    if chunk_size < 1:
        raise ValueError("chunk_size must be positive")
    columns = {KEY, CLAIM_KEY, DATE_KEY, PAYMENT_KEY}
    yield from pd.read_csv(
        path, sep="|", dtype="string", chunksize=chunk_size,
        keep_default_na=False, usecols=lambda name: name.strip() in columns,
    )

def read_beneficiaries(data_dir: Path, year: int) -> pd.DataFrame:
    path = find_file(data_dir, f"beneficiary_{year}.csv")
    frame = pd.read_csv(path, sep="|", dtype="string", keep_default_na=False)
    frame.columns = frame.columns.str.strip()
    if KEY not in frame.columns:
        raise ValueError(f"{path} missing {KEY}; verify synthetic RIF schema")
    if frame[KEY].eq("").any() or frame[KEY].isna().any():
        raise ValueError("Beneficiary file contains blank beneficiary IDs")
    if frame[KEY].duplicated().any():
        raise ValueError("Beneficiary-year file unexpectedly contains duplicate BENE_ID")
    return frame

def parse_claim_dates(series: pd.Series) -> pd.Series:
    """Parse dates as YYYYMMDD or YYYY-MM-DD, never ambiguous day/month guessing."""
    s = series.astype("string").str.strip().str.replace(r"\.0$", "", regex=True)
    compact = s.str.fullmatch(r"\d{8}").fillna(False)
    out = pd.Series(pd.NaT, index=series.index, dtype="datetime64[ns]")
    out.loc[compact] = pd.to_datetime(s.loc[compact], format="%Y%m%d", errors="coerce")
    out.loc[~compact] = pd.to_datetime(s.loc[~compact], format="%Y-%m-%d", errors="coerce")
    return out
