"""Tests use invented simulation data; no official CMS download is required."""
import json
import numpy as np
import pandas as pd
import pytest
from medicare_claims.stress_test import run_experiment, write_experiment


def test_stress_test_is_seeded_and_scenarios_are_balanced():
    draws, summary = run_experiment(n_beneficiaries=180, replications=4, seed=21)
    second, _ = run_experiment(n_beneficiaries=180, replications=4, seed=21)
    pd.testing.assert_frame_equal(draws, second)
    assert len(draws) == 8
    assert set(summary.scenario) == {"uniform", "age_differential"}
    assert (draws.naive_lines_total >= draws.true_claims_total).all()
    assert np.isfinite(draws[["corrected_beta", "naive_line_beta"]]).all().all()


def test_differential_line_counts_distort_age_coefficient_on_average():
    _, summary = run_experiment(n_beneficiaries=800, replications=16, seed=20261020)
    rows = summary.set_index("scenario")
    # This seeded scenario deliberately makes lines per claim age-dependent.
    assert (
        rows.loc["age_differential", "mean_naive_beta"]
        > rows.loc["age_differential", "mean_corrected_beta"] + 0.04
    )


def test_simulation_outputs_are_labeled_and_reproducible(tmp_path):
    write_experiment(tmp_path, n_beneficiaries=50, replications=2, seed=5)
    meta = json.loads((tmp_path / "simulation_metadata.json").read_text())
    assert meta["cms_data_used"] is False
    assert meta["clinical_or_policy_inference"] is False
    assert (tmp_path / "simulation_summary.csv").is_file()
    assert (tmp_path / "claim_granularity_stress_test.png").is_file()


@pytest.mark.parametrize("size,reps", [(29, 2), (30, 1)])
def test_bad_simulation_configuration_is_rejected(size, reps):
    with pytest.raises(ValueError):
        run_experiment(n_beneficiaries=size, replications=reps)
