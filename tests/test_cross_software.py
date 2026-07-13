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
    assert manifest.loc["Python IV", "status"] == "verified"
    assert manifest.loc["R fixest IV", "status"] == "verified"
    assert set(manifest.index) == {
        "Python",
        "R fixest",
        "Python IV",
        "R fixest IV",
        "Python IV relevance",
        "R IV relevance",
    }


def test_python_fixest_iv_benchmark() -> None:
    directory = Path(__file__).parents[1] / "benchmarks"
    python = pd.read_csv(directory / "python_iv_results.csv").set_index("term")
    fixest = pd.read_csv(directory / "fixest_iv_results.csv").set_index("term")
    fixest.index = fixest.index.str.replace("fit_", "", regex=False).str.replace(
        "(Intercept)", "const", regex=False
    )
    fixest = fixest.reindex(python.index)
    assert list(python.index) == list(fixest.index) == ["const", "x", "endogenous"]
    np.testing.assert_allclose(python["estimate"], fixest["estimate"], rtol=0, atol=1e-10)
    np.testing.assert_allclose(python["std_error"], fixest["std_error"], rtol=0, atol=1e-8)


def test_python_r_iv_relevance_benchmark() -> None:
    directory = Path(__file__).parents[1] / "benchmarks"
    python = pd.read_csv(directory / "python_iv_relevance_results.csv")
    r = pd.read_csv(directory / "r_iv_relevance_results.csv")
    assert list(python["endogenous"]) == list(r["endogenous"]) == ["endogenous"]
    columns = [
        "conditional_partial_r_squared",
        "conditional_f_statistic",
        "numerator_df",
        "denominator_df",
        "p_value",
    ]
    np.testing.assert_allclose(python[columns], r[columns], rtol=0, atol=1e-10)
