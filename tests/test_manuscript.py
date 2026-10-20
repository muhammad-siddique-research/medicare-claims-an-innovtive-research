"""Check report integrity, privacy and explicit data provenance."""
import pandas as pd

from medicare_claims.manuscript import write_research_report


def _summary():
    return pd.DataFrame([{
        "service": "outpatient",
        "n": 100,
        "conditional_count_ratio": 1.14,
        "count_ratio_ci_low": 1.05,
        "count_ratio_ci_high": 1.26,
        "bootstrap_count_ratio_ci_low": 1.03,
        "bootstrap_count_ratio_ci_high": 1.28,
        "pearson_dispersion": 1.2,
        "nb2_converged": True,
    }])


def _qa():
    return {
        "year": 2022,
        "cohort_rows": 100,
        "min_age": 65,
        "source_kind": "invented_toy_fixture",
        "services": {
            "outpatient": {
                "rows_seen": 140, "distinct_claims": 120,
                "duplicate_claim_lines": 20, "malformed_dates": 0,
                "unmatched_beneficiaries": 0,
            }
        },
    }


def test_report_contains_math_interpretation_and_figure_links(tmp_path):
    path = write_research_report(_qa(), _summary(), tmp_path)
    s = path.read_text(encoding="utf-8")
    assert "INVENTED TOY FIXTURE" in s
    assert "not CMS records" in s
    assert "Causal" not in s or "not causal" in s.lower()
    assert "age_associations_forest.png" in s
    assert "observed_vs_expected_zeros.png" in s
    assert "RECORD" in s
    assert "1.140" in s
    assert "TOY00001" not in s
    assert "No quasi-experiment" in s


def test_unknown_local_sources_are_not_mislabeled_as_cms(tmp_path):
    qa = _qa()
    qa["source_kind"] = "unverified_local"
    s = write_research_report(qa, _summary(), tmp_path).read_text()
    assert "OFFICIAL CMS ORIGIN NOT INDEPENDENTLY VERIFIED" in s
