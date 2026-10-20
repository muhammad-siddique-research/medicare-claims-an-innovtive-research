import numpy as np
import pandas as pd
import pytest
from medicare_claims.models import fit_count_models
from medicare_claims.toy import make_toy_dataset

def test_count_models_on_synthetic_fixture():
    rng = np.random.default_rng(4)
    n = 100
    ages = np.arange(n) % 35 + 65
    counts = rng.poisson(np.exp(0.2 + 0.03 * (ages - 65)))
    coefficients, details = fit_count_models(
        pd.DataFrame({"age": ages, "outpatient_claims": counts})
    )
    assert "Poisson (HC3)" in set(coefficients.model)
    assert details["n_analysis"] == n
    assert "age_per_decade" in set(coefficients.term)

def test_invalid_counts_rejected():
    with pytest.raises(ValueError, match="nonnegative"):
        fit_count_models(
            pd.DataFrame({"age": range(65, 77), "outpatient_claims": [-1] + [2] * 11})
        )

def test_toy_dataset_clearly_identified(tmp_path):
    make_toy_dataset(tmp_path)
    assert (tmp_path / "TOY_NOT_CMS.txt").exists()
    assert "GENERATED_NOT_CMS" in (tmp_path / "beneficiary_2022.csv").read_text()
