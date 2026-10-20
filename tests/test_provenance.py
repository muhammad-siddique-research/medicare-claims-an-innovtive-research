"""Check deterministic input fingerprints and manifest provenance caveats."""
import hashlib
import json

import pytest

from medicare_claims.provenance import write_input_manifest


def _make_minimal_inputs(root):
    (root / "beneficiary_2022.csv").write_text(
        "BENE_ID|AGE\n001|77\n", encoding="utf-8"
    )
    for service in ("inpatient", "outpatient"):
        (root / f"{service}.csv").write_text(
            "BENE_ID|CLM_ID|CLM_FROM_DT|CLM_PMT_AMT\n"
            "001|C1|20220101|15\n", encoding="utf-8"
        )


def test_manifest_does_not_claim_cms_authenticity(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    _make_minimal_inputs(raw)
    result = write_input_manifest(raw, 2022, tmp_path / "reports")
    assert result["official_CMS_authenticity"].startswith("NOT VERIFIED")
    assert len(result["files"]) == 3
    expected = hashlib.sha256((raw / "inpatient.csv").read_bytes()).hexdigest()
    assert next(f for f in result["files"] if f["name"] == "inpatient.csv")["sha256"] == expected
    persisted = json.loads((tmp_path / "reports" / "input_manifest.json").read_text())
    assert persisted == result
    assert "001|77" not in str(result)


def test_manifest_detects_schema_error(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    _make_minimal_inputs(raw)
    (raw / "inpatient.csv").write_text("BENE_ID|CLM_ID\n001|C1\n")
    with pytest.raises(ValueError, match="CLM_FROM_DT"):
        write_input_manifest(raw, 2022, tmp_path / "reports")


def test_manifest_identifies_changed_inputs(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    _make_minimal_inputs(raw)
    a = write_input_manifest(raw, 2022, tmp_path / "a")
    with (raw / "outpatient.csv").open("a") as out:
        out.write("001|C2|20220202|20\n")
    b = write_input_manifest(raw, 2022, tmp_path / "b")
    assert a["files"][2]["sha256"] != b["files"][2]["sha256"]
