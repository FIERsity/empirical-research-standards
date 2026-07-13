"""Transparent sample-rank and conditional first-stage relevance diagnostics."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats


@dataclass(frozen=True)
class IVRelevanceDiagnostics:
    conditional_tests: pd.DataFrame
    cross_moment_rank: int
    required_rank: int
    rank_condition_satisfied: bool
    normalized_singular_values: tuple[float, ...]
    nobs: int
    exogenous: tuple[str, ...]
    endogenous: tuple[str, ...]
    instruments: tuple[str, ...]
    add_intercept: bool

    def summary(self) -> pd.Series:
        return pd.Series(
            {
                "nobs": self.nobs,
                "cross_moment_rank": self.cross_moment_rank,
                "required_rank": self.required_rank,
                "rank_condition_satisfied": self.rank_condition_satisfied,
                "minimum_normalized_singular_value": min(self.normalized_singular_values),
            }
        )


def _residualize(values: np.ndarray, controls: np.ndarray) -> np.ndarray:
    if controls.shape[1] == 0:
        return values
    residuals = values - controls @ np.linalg.lstsq(controls, values, rcond=None)[0]
    return np.asarray(residuals, dtype=float)


def diagnose_iv_relevance(
    data: pd.DataFrame,
    *,
    exogenous: list[str] | tuple[str, ...],
    endogenous: list[str] | tuple[str, ...],
    instruments: list[str] | tuple[str, ...],
    add_intercept: bool = True,
    drop_missing: bool = False,
) -> IVRelevanceDiagnostics:
    """Diagnose sample rank and homoskedastic conditional instrument relevance.

    These diagnostics are not Kleibergen-Paap statistics and do not establish instrument
    validity or population identification.
    """
    exog, endog, excluded = tuple(exogenous), tuple(endogenous), tuple(instruments)
    if not endog or not excluded:
        raise ValueError("endogenous and instruments must each contain at least one column")
    columns = (*exog, *endog, *excluded)
    if len(set(columns)) != len(columns):
        raise ValueError("exogenous, endogenous, and instruments must not overlap")
    if len(excluded) < len(endog):
        raise ValueError(
            "sample rank condition requires at least as many instruments as endogenous variables"
        )
    missing = [column for column in columns if column not in data]
    if missing:
        raise KeyError(f"columns not found: {missing}")
    for column in columns:
        if not pd.api.types.is_numeric_dtype(data[column]):
            raise TypeError(f"column {column!r} must be numeric")
    sample = data.loc[:, list(columns)].copy()
    missing_rows = sample.isna().any(axis=1)
    if missing_rows.any() and not drop_missing:
        raise ValueError("IV relevance columns contain missing values; set drop_missing=True")
    sample = sample.loc[~missing_rows]
    values = sample.to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("IV relevance columns must contain only finite values")

    nobs = len(sample)
    base = sample.loc[:, list(exog)].to_numpy(dtype=float)
    if add_intercept:
        base = np.column_stack([np.ones(nobs), base])
    endogenous_values = sample.loc[:, list(endog)].to_numpy(dtype=float)
    instrument_values = sample.loc[:, list(excluded)].to_numpy(dtype=float)
    residual_endogenous = _residualize(endogenous_values, base)
    residual_instruments = _residualize(instrument_values, base)
    if np.linalg.matrix_rank(residual_instruments) < len(excluded):
        raise ValueError(
            "excluded instruments are rank deficient after removing exogenous variables"
        )

    cross_moment = residual_instruments.T @ residual_endogenous
    scales = np.outer(
        np.linalg.norm(residual_instruments, axis=0),
        np.linalg.norm(residual_endogenous, axis=0),
    )
    normalized = np.divide(cross_moment, scales, out=np.zeros_like(cross_moment), where=scales > 0)
    singular_values = tuple(float(value) for value in np.linalg.svd(normalized, compute_uv=False))
    rank = int(np.linalg.matrix_rank(cross_moment))

    records: list[dict[str, float | int | str]] = []
    q = len(excluded)
    for index, name in enumerate(endog):
        other = np.delete(endogenous_values, index, axis=1)
        reduced = np.column_stack([base, other])
        full = np.column_stack([reduced, instrument_values])
        if np.linalg.matrix_rank(full) < full.shape[1]:
            raise ValueError(f"conditional first stage for {name!r} is rank deficient")
        target = endogenous_values[:, index]
        reduced_residual = target - reduced @ np.linalg.lstsq(reduced, target, rcond=None)[0]
        full_residual = target - full @ np.linalg.lstsq(full, target, rcond=None)[0]
        rss_reduced = float(reduced_residual @ reduced_residual)
        rss_full = float(full_residual @ full_residual)
        denominator_df = nobs - full.shape[1]
        if denominator_df <= 0 or rss_full <= 0:
            raise ValueError("insufficient residual degrees of freedom for conditional first stage")
        statistic = max(0.0, (rss_reduced - rss_full) / q) / (rss_full / denominator_df)
        records.append(
            {
                "endogenous": name,
                "conditional_partial_r_squared": max(0.0, 1.0 - rss_full / rss_reduced),
                "conditional_f_statistic": statistic,
                "numerator_df": q,
                "denominator_df": denominator_df,
                "p_value": float(stats.f.sf(statistic, q, denominator_df)),
            }
        )
    return IVRelevanceDiagnostics(
        pd.DataFrame.from_records(records),
        rank,
        len(endog),
        rank == len(endog),
        singular_values,
        nobs,
        exog,
        endog,
        excluded,
        add_intercept,
    )
