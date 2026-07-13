"""Explicit ordinary least squares estimation with validated inputs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

import numpy as np
import pandas as pd
import statsmodels.api as sm

CovarianceType = Literal["nonrobust", "HC1", "cluster"]


@dataclass(frozen=True)
class OLSResult:
    """A small, auditable wrapper around a statsmodels OLS result."""

    coefficients: pd.Series
    standard_errors: pd.Series
    statistic: pd.Series
    p_values: pd.Series
    confidence_intervals: pd.DataFrame
    nobs: int
    original_nobs: int
    dropped_nobs: int
    df_model: float
    df_resid: float
    r_squared: float
    adjusted_r_squared: float
    covariance: CovarianceType
    outcome: str
    predictors: tuple[str, ...]
    add_intercept: bool
    cluster: str | None
    raw_result: Any

    def tidy(self, confidence_level: float = 0.95) -> pd.DataFrame:
        """Return one row per estimated term in a stable, tidy format."""
        if not 0 < confidence_level < 1:
            raise ValueError("confidence_level must be strictly between 0 and 1")
        alpha = 1.0 - confidence_level
        intervals = self.raw_result.conf_int(alpha=alpha)
        intervals = pd.DataFrame(intervals, index=self.coefficients.index)
        return pd.DataFrame(
            {
                "term": self.coefficients.index,
                "estimate": self.coefficients.to_numpy(),
                "std_error": self.standard_errors.to_numpy(),
                "statistic": self.statistic.to_numpy(),
                "p_value": self.p_values.to_numpy(),
                "conf_low": intervals.iloc[:, 0].to_numpy(),
                "conf_high": intervals.iloc[:, 1].to_numpy(),
            }
        )


def fit_ols(
    data: pd.DataFrame,
    outcome: str,
    predictors: list[str] | tuple[str, ...],
    *,
    add_intercept: bool = True,
    covariance: CovarianceType = "nonrobust",
    cluster: str | None = None,
    drop_missing: bool = False,
) -> OLSResult:
    """Fit OLS after explicit validation of the model sample and design matrix."""
    if not isinstance(data, pd.DataFrame):
        raise TypeError("data must be a pandas DataFrame")
    terms = tuple(predictors)
    if not terms:
        raise ValueError("predictors must contain at least one column")
    if len(set(terms)) != len(terms):
        raise ValueError("predictors must not contain duplicate columns")
    if outcome in terms:
        raise ValueError("outcome must not also appear in predictors")
    if covariance not in {"nonrobust", "HC1", "cluster"}:
        raise ValueError("covariance must be one of: nonrobust, HC1, cluster")
    if covariance == "cluster" and cluster is None:
        raise ValueError("cluster column is required when covariance='cluster'")
    if covariance != "cluster" and cluster is not None:
        raise ValueError("cluster may only be set when covariance='cluster'")

    required = [outcome, *terms]
    if cluster is not None:
        required.append(cluster)
    missing_columns = [name for name in required if name not in data.columns]
    if missing_columns:
        raise KeyError(f"columns not found: {missing_columns}")
    for name in [outcome, *terms]:
        if not pd.api.types.is_numeric_dtype(data[name]):
            raise TypeError(f"column {name!r} must be numeric")

    sample = data.loc[:, required].copy()
    original_nobs = len(sample)
    missing_rows = sample.isna().any(axis=1)
    if missing_rows.any():
        if not drop_missing:
            raise ValueError(
                f"model columns contain missing values in {int(missing_rows.sum())} rows; "
                "set drop_missing=True to use complete cases"
            )
        sample = sample.loc[~missing_rows].copy()
    if sample.empty:
        raise ValueError("no complete observations remain")

    numeric = sample.loc[:, [outcome, *terms]].to_numpy(dtype=float)
    if not np.isfinite(numeric).all():
        raise ValueError("outcome and predictor columns must contain only finite values")

    y = sample[outcome].astype(float)
    x = sample.loc[:, list(terms)].astype(float)
    if add_intercept:
        x = sm.add_constant(x, has_constant="add")
    matrix = x.to_numpy(dtype=float)
    if len(sample) <= matrix.shape[1]:
        raise ValueError("number of observations must exceed number of estimated parameters")
    rank = int(np.linalg.matrix_rank(matrix))
    if rank < matrix.shape[1]:
        raise ValueError("design matrix is rank deficient; remove collinear predictors")

    model = sm.OLS(y, x, missing="raise")
    if covariance == "nonrobust":
        fitted = model.fit()
    elif covariance == "HC1":
        fitted = model.fit(cov_type="HC1")
    else:
        assert cluster is not None
        groups = sample[cluster]
        if groups.nunique(dropna=False) < 2:
            raise ValueError("cluster covariance requires at least two distinct groups")
        fitted = model.fit(cov_type="cluster", cov_kwds={"groups": groups})

    names = x.columns
    confidence = pd.DataFrame(fitted.conf_int(), index=names, columns=["conf_low", "conf_high"])
    return OLSResult(
        coefficients=pd.Series(np.asarray(fitted.params), index=names, name="estimate"),
        standard_errors=pd.Series(np.asarray(fitted.bse), index=names, name="std_error"),
        statistic=pd.Series(np.asarray(fitted.tvalues), index=names, name="statistic"),
        p_values=pd.Series(np.asarray(fitted.pvalues), index=names, name="p_value"),
        confidence_intervals=confidence,
        nobs=int(fitted.nobs),
        original_nobs=original_nobs,
        dropped_nobs=original_nobs - int(fitted.nobs),
        df_model=float(fitted.df_model),
        df_resid=float(fitted.df_resid),
        r_squared=float(fitted.rsquared),
        adjusted_r_squared=float(fitted.rsquared_adj),
        covariance=covariance,
        outcome=outcome,
        predictors=terms,
        add_intercept=add_intercept,
        cluster=cluster,
        raw_result=fitted,
    )
