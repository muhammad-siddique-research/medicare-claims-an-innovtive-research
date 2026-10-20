"""Invented toy fixtures for software tests; NOT CMS-supplied patient-level data."""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

def make_toy_dataset(dest: Path, year: int = 2022, n: int = 100, seed: int = 20261020) -> None:
    if n < 12:
        raise ValueError("Fixture needs >=12 beneficiaries")
    dest.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)
    ids = [f"TOY{i:05d}" for i in range(n)]
    ages = rng.integers(65, 96, size=n)
    pd.DataFrame({
        "BENE_ID": ids, "AGE": ages, "TOY_DATA_WARNING": "GENERATED_NOT_CMS",
    }).to_csv(dest / f"beneficiary_{year}.csv", sep="|", index=False)
    for service, rate in (("inpatient", 0.45), ("outpatient", 2.9)):
        rows = []
        for i, bene in enumerate(ids):
            count = int(rng.poisson(rate * (1 + 0.035 * (int(ages[i]) - 65))))
            for c in range(count):
                claim = f"TOY-{service}-{i}-{c}"
                month = int(rng.integers(1, 13))
                day = int(rng.integers(1, 27))
                amount = round(float(rng.uniform(80, 4000)), 2)
                record = {
                    "BENE_ID": bene, "CLM_ID": claim,
                    "CLM_FROM_DT": f"{year}{month:02d}{day:02d}", "CLM_PMT_AMT": amount,
                }
                rows.extend([record, record] if c % 4 == 0 else [record])
        pd.DataFrame(
            rows, columns=["BENE_ID", "CLM_ID", "CLM_FROM_DT", "CLM_PMT_AMT"]
        ).to_csv(dest / f"{service}.csv", sep="|", index=False)
    (dest / "TOY_NOT_CMS.txt").write_text(
        "Invented fixture for automated tests. NOT CMS data.\n", encoding="utf-8"
    )
