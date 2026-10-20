"""Scholarly outputs are checked on invented toy data, never real patients."""
import json

import numpy as np
import pandas as pd
import pytest

from medicare_claims.advanced import run_advanced_analyses


def _invented_panel(n=100, seed=30):
    rng = np.random.default_rng(seed)
    ages = rng.integers(65, 96, size=n)
    return pd.DataFrame({
        "BENE_ID": [f"TOY{i:04d}" for i in range(n)],
        "age": ages,
        "outpatient_claims": rng.poisson(np.exp(0.5 + 0.025 * (ages - 65))),
        "inpatient_claims": rng.poisson(np.exp(-0.7 + 0.013 * (ages - 65))),
    })


def test_advanced_outputs_include_valid_ci_model_checks_and_plots(tmp_path):
    output = run_advanced_analyses(
        _invented_panel(), tmp_path, bootstrap_replications=12, seed=20261020
    )
    assert set(output.service) == {"outpatient", "inpatient"}
    assert (output["n"] == 100).all()
    assert (output["irr_ci_low"] <= output["incidence_count_ratio"]).all()
    assert (output["irr_ci_high"] >= output["incidence_count_ratio"]).all()
    assert (output["bootstrap_successful_replications"] >= 8).all()
    assert np.isfinite(output["poisson_aic"]).all()
    assert (output["observed_zero_fraction"].between(0, 1)).all()
    assert (output["poisson_expected_zero_fraction"].between(0, 1)).all()
    for filename in (
        "advanced_econometric_diagnostics.csv",
        "age_associations_forest.png",
        "observed_vs_expected_zeros.png",
        "calibration_outpatient.csv",
        "calibration_outpatient.png",
        "calibration_inpatient.csv",
        "calibration_inpatient.png",
    ):
        assert (tmp_path / filename).is_file()
    meta = json.loads(
        (tmp_path / "advanced_econometric_provenance.json").read_text()
    )
    assert "not a treatment" in " ".join(meta["limitations"]).lower()
    outputs_as_text = (tmp_path / "advanced_econometric_diagnostics.csv").read_text()
    assert "BENE_ID" not in outputs_as_text and "TOY0001" not in outputs_as_text


def test_advanced_seeded_bootstrap_is_reproducible(tmp_path):
    frame = _invented_panel()
    first = run_advanced_analyses(
        frame, tmp_path / "first", bootstrap_replications=10, seed=23
    )
    second = run_advanced_analyses(
        frame, tmp_path / "second", bootstrap_replications=10, seed=23
    )
    pd.testing.assert_frame_equal(first, second)


@pytest.mark.parametrize(
    "mode", ["negative", "fractional", "young", "missing", "small"]
)
def test_advanced_rejects_invalid_analytic_inputs(tmp_path, mode):
    frame = _invented_panel()
    if mode == "negative":
        frame.loc[0, "outpatient_claims"] = -1
    elif mode == "fractional":
        frame.loc[0, "outpatient_claims"] = 1.25
    elif mode == "young":
        frame.loc[0, "age"] = 53
    elif mode == "missing":
        frame.drop(columns="inpatient_claims", inplace=True)
    else:
        frame = frame.head(15)
    with pytest.raises(ValueError):
        run_advanced_analyses(
            frame, tmp_path, bootstrap_replications=10
        )


def test_bootstrap_requires_nontrivial_replicates(tmp_path):
    with pytest.raises(ValueError, match="bootstrap_replications"):
        run_advanced_analyses(_invented_panel(), tmp_path, bootstrap_replications=2)
