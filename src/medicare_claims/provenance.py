"""File-level audit for reproducible, independently verifiable local inputs.

An SHA-256 manifest establishes byte identity, NOT that a file was officially
downloaded from CMS. Never write patient records to repository outputs.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from .io import find_file


def sha256_file(path: Path, block_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            block = handle.read(block_size)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def write_input_manifest(
    data_dir: Path, year: int, output_dir: Path
) -> dict:
    """Hash three selected local files without inspecting any patient data rows."""
    result = {
        "year": year,
        "identity": "local byte-level input fingerprint",
        "official_CMS_authenticity": "NOT VERIFIED by hashes alone",
        "files": [],
    }
    for filename in (f"beneficiary_{year}.csv", "inpatient.csv", "outpatient.csv"):
        path = find_file(data_dir, filename)
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            first_line = handle.readline()
        if not first_line:
            raise ValueError(f"Empty source file: {filename}")
        columns = next(csv.reader([first_line], delimiter="|"))
        columns = [col.strip() for col in columns]
        required = ({"BENE_ID", "AGE"} if filename.startswith("beneficiary_")
                    else {"BENE_ID", "CLM_ID", "CLM_FROM_DT"})
        # Some beneficiary files contain date of birth instead of a prebuilt AGE.
        missing = required - set(columns)
        if filename.startswith("beneficiary_") and missing == {"AGE"}:
            if "BENE_BIRTH_DT" in columns:
                missing.clear()
        if missing:
            raise ValueError(f"{filename} lacks expected columns: {sorted(missing)}")
        result["files"].append({
            "name": filename,
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
            "header_columns": columns,
        })
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "input_manifest.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    return result
