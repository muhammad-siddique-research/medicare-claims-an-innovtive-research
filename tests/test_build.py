from pathlib import Path
import pandas as pd
import pytest
from medicare_claims.build import claims_for_year, construct_panel
from medicare_claims.io import read_beneficiaries

def test_line_item_duplication_is_not_claim_duplication(tmp_path: Path):
    frame = pd.DataFrame([
        ["0001", "ABC", "20220104", "35.50"],
        ["0001", "ABC", "20220104", "35.50"],
        ["0001", "DEF", "20221231", "25.00"],
        ["0001", "GHI", "20210101", "25.00"],
        ["0002", "ZZZ", "2022-06-30", "10.00"],
        ["0003", "BAD", "20220230", "10.00"],
    ], columns=["BENE_ID", "CLM_ID", "CLM_FROM_DT", "CLM_PMT_AMT"])
    path = tmp_path / "outpatient.csv"
    frame.to_csv(path, sep="|", index=False)
    unique, stats = claims_for_year(path, 2022, "outpatient", chunk_size=2)
    assert len(unique) == 3
    assert stats.duplicate_claim_lines == 1
    assert stats.off_year_rows == 1
    assert stats.malformed_dates == 1
    assert unique.loc[unique.CLM_ID == "ABC", "payment"].iloc[0] == 35.50

def test_conflicting_claim_payments_are_flagged(tmp_path):
    p = tmp_path / "inpatient.csv"
    p.write_text(
        "BENE_ID|CLM_ID|CLM_FROM_DT|CLM_PMT_AMT\nA|1|20220101|40\nA|1|20220101|50\n",
        encoding="utf-8",
    )
    out, stats = claims_for_year(p, 2022, "inpatient")
    assert stats.conflicting_payments == 1
    assert pd.isna(out.loc[0, "payment"])
    assert len(out) == 1

def test_panel_keeps_zero_claims_without_multiplying_beneficiaries(tmp_path):
    (tmp_path / "beneficiary_2022.csv").write_text(
        "BENE_ID|AGE\nA|65\nB|78\nC|52\n", encoding="utf-8"
    )
    for service in ("outpatient", "inpatient"):
        (tmp_path / f"{service}.csv").write_text(
            "BENE_ID|CLM_ID|CLM_FROM_DT|CLM_PMT_AMT\n"
            "A|C1|20220105|300\nA|C1|20220105|300\nB|C2|20220110|20\n",
            encoding="utf-8",
        )
    panel, qa = construct_panel(read_beneficiaries(tmp_path, 2022), tmp_path, 2022)
    assert set(panel.BENE_ID) == {"A", "B"}
    assert panel.set_index("BENE_ID").loc["A", "outpatient_claims"] == 1
    assert qa["cohort_rows"] == 2

def test_missing_claim_id_fails(tmp_path):
    (tmp_path / "outpatient.csv").write_text(
        "BENE_ID|CLM_FROM_DT\nA|20220101\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="CLM_ID"):
        claims_for_year(tmp_path / "outpatient.csv", 2022, "outpatient")
