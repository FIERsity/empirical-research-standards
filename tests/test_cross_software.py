from pathlib import Path

import numpy as np
import pandas as pd


def test_python_fixest_benchmark() -> None:
    directory = Path(__file__).parents[1] / "benchmarks"
    python = pd.read_csv(directory / "python_results.csv").set_index("term")
    fixest = pd.read_csv(directory / "fixest_results.csv").set_index("term")
    assert list(python.index) == list(fixest.index) == ["x", "did"]
    np.testing.assert_allclose(python["estimate"], fixest["estimate"], rtol=0, atol=1e-10)
    np.testing.assert_allclose(python["std_error"], fixest["std_error"], rtol=0, atol=1e-8)


def test_benchmark_status_is_explicit() -> None:
    directory = Path(__file__).parents[1] / "benchmarks"
    manifest = pd.read_csv(directory / "benchmark_manifest.csv").set_index("software")
    assert manifest.loc["Python", "status"] == "verified"
    assert manifest.loc["R fixest", "status"] == "verified"
    assert manifest.loc["Stata reghdfe", "status"] == "pending"
