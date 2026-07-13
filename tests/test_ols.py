from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
import statsmodels.api as sm

from empirical_standards import fit_ols


@pytest.fixture
def data() -> pd.DataFrame:
    rng = np.random.default_rng(20260713)
    n = 240
    x1 = rng.normal(size=n)
    x2 = rng.normal(size=n)
    group = np.repeat(np.arange(24), 10)
    group_effect = rng.normal(scale=0.5, size=24)[group]
    y = 1.5 + 2.0 * x1 - 0.75 * x2 + group_effect + rng.normal(scale=0.25, size=n)
    return pd.DataFrame({"y": y, "x1": x1, "x2": x2, "group": group})


@pytest.mark.parametrize("covariance", ["nonrobust", "HC1", "cluster"])
def test_matches_statsmodels(data: pd.DataFrame, covariance: str) -> None:
    kwargs = {"covariance": covariance}
    x = sm.add_constant(data[["x1", "x2"]], has_constant="add")
    if covariance == "nonrobust":
        expected = sm.OLS(data["y"], x).fit()
    elif covariance == "HC1":
        expected = sm.OLS(data["y"], x).fit(cov_type="HC1")
    else:
        kwargs["cluster"] = "group"
        expected = sm.OLS(data["y"], x).fit(
            cov_type="cluster", cov_kwds={"groups": data["group"]}
        )
    result = fit_ols(data, "y", ["x1", "x2"], **kwargs)  # type: ignore[arg-type]
    np.testing.assert_allclose(result.coefficients, expected.params)
    np.testing.assert_allclose(result.standard_errors, expected.bse)


def test_recovers_known_coefficients(data: pd.DataFrame) -> None:
    result = fit_ols(data, "y", ["x1", "x2"])
    assert result.coefficients["x1"] == pytest.approx(2.0, abs=0.1)
    assert result.coefficients["x2"] == pytest.approx(-0.75, abs=0.1)
    assert result.predictors == ("x1", "x2")


def test_no_intercept_and_tidy_output(data: pd.DataFrame) -> None:
    result = fit_ols(data, "y", ["x1", "x2"], add_intercept=False)
    assert list(result.coefficients.index) == ["x1", "x2"]
    assert list(result.tidy().columns) == [
        "term", "estimate", "std_error", "statistic", "p_value", "conf_low", "conf_high"
    ]
    assert list(result.tidy()["term"]) == ["x1", "x2"]


def test_missing_values_are_explicit(data: pd.DataFrame) -> None:
    data.loc[0, "x1"] = np.nan
    with pytest.raises(ValueError, match="missing values"):
        fit_ols(data, "y", ["x1", "x2"])
    result = fit_ols(data, "y", ["x1", "x2"], drop_missing=True)
    assert result.original_nobs == 240
    assert result.nobs == 239
    assert result.dropped_nobs == 1


@pytest.mark.parametrize(
    ("mutator", "error", "message"),
    [
        (lambda d: d.assign(x1="text"), TypeError, "must be numeric"),
        (lambda d: d.assign(x1=np.inf), ValueError, "finite values"),
        (lambda d: d.assign(x2=d["x1"] * 2), ValueError, "rank deficient"),
    ],
)
def test_invalid_designs(
    data: pd.DataFrame, mutator: object, error: type[Exception], message: str
) -> None:
    invalid = mutator(data)  # type: ignore[operator]
    with pytest.raises(error, match=message):
        fit_ols(invalid, "y", ["x1", "x2"])


def test_invalid_covariance_and_clusters(data: pd.DataFrame) -> None:
    with pytest.raises(ValueError, match="covariance must"):
        fit_ols(data, "y", ["x1"], covariance="HC3")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="cluster column is required"):
        fit_ols(data, "y", ["x1"], covariance="cluster")
    with pytest.raises(ValueError, match="at least two"):
        fit_ols(data.assign(group=1), "y", ["x1"], covariance="cluster", cluster="group")


def test_confidence_level_validation(data: pd.DataFrame) -> None:
    result = fit_ols(data, "y", ["x1"])
    with pytest.raises(ValueError, match="confidence_level"):
        result.tidy(1.0)

