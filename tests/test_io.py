import pandas as pd
import pytest
from medicare_claims.io import parse_claim_dates, read_beneficiaries

def test_parse_claim_dates_multiple_explicit_formats():
    s = pd.Series(["20220104", "2022-12-31", "20220230", ""])
    parsed = parse_claim_dates(s)
    assert str(parsed.iloc[0].date()) == "2022-01-04"
    assert str(parsed.iloc[1].date()) == "2022-12-31"
    assert pd.isna(parsed.iloc[2])
    assert pd.isna(parsed.iloc[3])

def test_beneficiary_id_preserves_leading_zeros(tmp_path):
    (tmp_path / "beneficiary_2022.csv").write_text(
        "BENE_ID|AGE|ZIP_CD\n000123|67|00123\n", encoding="utf-8"
    )
    out = read_beneficiaries(tmp_path, 2022)
    assert out.loc[0, "BENE_ID"] == "000123"
    assert out.loc[0, "ZIP_CD"] == "00123"

def test_duplicate_beneficiary_id_fails(tmp_path):
    (tmp_path / "beneficiary_2022.csv").write_text(
        "BENE_ID|AGE\nA|70\nA|71\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="duplicate"):
        read_beneficiaries(tmp_path, 2022)
