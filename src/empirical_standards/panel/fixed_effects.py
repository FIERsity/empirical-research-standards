"""Explicit one-way and two-way fixed-effects estimation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

import numpy as np
import pandas as pd
from linearmodels.panel import PanelOLS

from empirical_standards.results import ModelMetadata, build_metadata

PanelCovariance = Literal[
    "unadjusted", "robust", "cluster_entity", "cluster_time", "cluster_two_way"
]


@dataclass(frozen=True)
class FixedEffectsResult:
    """Auditable fixed-effects estimation result."""

    coefficients: pd.Series
    standard_errors: pd.Series
    statistic: pd.Series
    p_values: pd.Series
    confidence_intervals: pd.DataFrame
    nobs: int
    entities: int
    periods: int
    r_squared_within: float
    r_squared_overall: float
    outcome: str
    predictors: tuple[str, ...]
    entity: str
    time: str
    entity_effects: bool
    time_effects: bool
    covariance: PanelCovariance
    raw_result: Any
    metadata: ModelMetadata

    def tidy(self) -> pd.DataFrame:
        """Return one row per estimated coefficient."""
        return pd.DataFrame(
            {
                "term": self.coefficients.index,
                "estimate": self.coefficients.to_numpy(),
                "std_error": self.standard_errors.to_numpy(),
                "statistic": self.statistic.to_numpy(),
                "p_value": self.p_values.to_numpy(),
                "conf_low": self.confidence_intervals.iloc[:, 0].to_numpy(),
                "conf_high": self.confidence_intervals.iloc[:, 1].to_numpy(),
            }
        )

    def glance(self) -> pd.Series:
        return pd.Series(
            {
                "estimator": "fixed_effects",
                "nobs": self.nobs,
                "entities": self.entities,
                "periods": self.periods,
                "r_squared_within": self.r_squared_within,
                "r_squared_overall": self.r_squared_overall,
                "covariance": self.covariance,
            }
        )

    def model_spec(self) -> dict[str, Any]:
        return self.metadata.spec.to_dict()

    def sample_info(self) -> dict[str, Any]:
        return self.metadata.sample.to_dict()

    def provenance(self) -> dict[str, Any]:
        return self.metadata.provenance.to_dict()


def fit_fixed_effects(
    data: pd.DataFrame,
    outcome: str,
    predictors: list[str] | tuple[str, ...],
    *,
    entity: str,
    time: str,
    entity_effects: bool = True,
    time_effects: bool = False,
    covariance: PanelCovariance = "cluster_entity",
    drop_missing: bool = False,
) -> FixedEffectsResult:
    """Fit a one-way or two-way fixed-effects model with explicit inference settings."""
    terms = tuple(predictors)
    if not terms:
        raise ValueError("predictors must contain at least one column")
    if not entity_effects and not time_effects:
        raise ValueError("at least one of entity_effects or time_effects must be enabled")
    if covariance not in {
        "unadjusted",
        "robust",
        "cluster_entity",
        "cluster_time",
        "cluster_two_way",
    }:
        raise ValueError("unsupported panel covariance")
    required = [entity, time, outcome, *terms]
    missing = [column for column in required if column not in data.columns]
    if missing:
        raise KeyError(f"columns not found: {missing}")
    if data.duplicated([entity, time]).any():
        raise ValueError("entity-time pairs must uniquely identify observations")
    for column in [outcome, *terms]:
        if not pd.api.types.is_numeric_dtype(data[column]):
            raise TypeError(f"column {column!r} must be numeric")
    sample = data.loc[:, required].copy()
    original_nobs = len(sample)
    missing_rows = sample.isna().any(axis=1)
    if missing_rows.any() and not drop_missing:
        raise ValueError("panel model columns contain missing values; set drop_missing=True")
    sample = sample.loc[~missing_rows]
    if not np.isfinite(sample[[outcome, *terms]].to_numpy(dtype=float)).all():
        raise ValueError("outcome and predictors must contain only finite values")
    if sample[entity].nunique() < 2 or sample[time].nunique() < 2:
        raise ValueError("panel requires at least two entities and two periods")
    panel = sample.set_index([entity, time]).sort_index()
    model = PanelOLS(
        panel[outcome],
        panel[list(terms)],
        entity_effects=entity_effects,
        time_effects=time_effects,
        drop_absorbed=False,
        check_rank=True,
    )
    fit_options: dict[str, Any] = {"debiased": True}
    if covariance == "unadjusted":
        fit_options["cov_type"] = "unadjusted"
    elif covariance == "robust":
        fit_options["cov_type"] = "robust"
    else:
        fit_options["cov_type"] = "clustered"
        fit_options["cluster_entity"] = covariance in {"cluster_entity", "cluster_two_way"}
        fit_options["cluster_time"] = covariance in {"cluster_time", "cluster_two_way"}
    fitted = model.fit(**fit_options)
    intervals = fitted.conf_int()
    intervals.columns = ["conf_low", "conf_high"]
    return FixedEffectsResult(
        coefficients=fitted.params.rename("estimate"),
        standard_errors=fitted.std_errors.rename("std_error"),
        statistic=fitted.tstats.rename("statistic"),
        p_values=fitted.pvalues.rename("p_value"),
        confidence_intervals=intervals,
        nobs=int(fitted.nobs),
        entities=int(sample[entity].nunique()),
        periods=int(sample[time].nunique()),
        r_squared_within=float(fitted.rsquared_within),
        r_squared_overall=float(fitted.rsquared_overall),
        outcome=outcome,
        predictors=terms,
        entity=entity,
        time=time,
        entity_effects=entity_effects,
        time_effects=time_effects,
        covariance=covariance,
        raw_result=fitted,
        metadata=build_metadata(
            estimator="fixed_effects",
            outcome=outcome,
            predictors=terms,
            settings={
                "entity": entity,
                "time": time,
                "entity_effects": entity_effects,
                "time_effects": time_effects,
                "covariance": covariance,
                "drop_missing": drop_missing,
            },
            sample=sample,
            original_nobs=original_nobs,
        ),
    )
