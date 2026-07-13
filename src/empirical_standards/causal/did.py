"""Two-period/multi-period DID and dynamic event-study specifications."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from empirical_standards.panel.fixed_effects import (
    FixedEffectsResult,
    PanelCovariance,
    fit_fixed_effects,
)
from empirical_standards.results import ModelMetadata, build_metadata


@dataclass(frozen=True)
class DIDResult:
    effect: float
    standard_error: float
    p_value: float
    treatment_term: str
    model: FixedEffectsResult
    metadata: ModelMetadata

    def tidy(self) -> pd.DataFrame:
        return (
            self.model.tidy()
            .loc[lambda frame: frame["term"] == self.treatment_term]
            .reset_index(drop=True)
        )

    def glance(self) -> pd.Series:
        return pd.Series(
            {
                "estimator": "did",
                "nobs": self.model.nobs,
                "effect": self.effect,
                "std_error": self.standard_error,
                "p_value": self.p_value,
                "covariance": self.model.covariance,
            }
        )

    def model_spec(self) -> dict[str, object]:
        return self.metadata.spec.to_dict()

    def sample_info(self) -> dict[str, object]:
        return self.metadata.sample.to_dict()

    def provenance(self) -> dict[str, object]:
        return self.metadata.provenance.to_dict()


@dataclass(frozen=True)
class EventStudyResult:
    estimates: pd.DataFrame
    reference_period: int
    window: tuple[int, int]
    pretrend_statistic: float
    pretrend_p_value: float
    model: FixedEffectsResult
    metadata: ModelMetadata

    def tidy(self) -> pd.DataFrame:
        return self.estimates.copy()

    def glance(self) -> pd.Series:
        return pd.Series(
            {
                "estimator": "event_study",
                "nobs": self.model.nobs,
                "reference_period": self.reference_period,
                "window_lower": self.window[0],
                "window_upper": self.window[1],
                "pretrend_statistic": self.pretrend_statistic,
                "pretrend_p_value": self.pretrend_p_value,
            }
        )

    def model_spec(self) -> dict[str, object]:
        return self.metadata.spec.to_dict()

    def sample_info(self) -> dict[str, object]:
        return self.metadata.sample.to_dict()

    def provenance(self) -> dict[str, object]:
        return self.metadata.provenance.to_dict()


def fit_did(
    data: pd.DataFrame,
    outcome: str,
    treated: str,
    post: str,
    *,
    entity: str,
    time: str,
    controls: list[str] | tuple[str, ...] = (),
    covariance: PanelCovariance = "cluster_entity",
) -> DIDResult:
    """Estimate a TWFE DID with an explicit treated-by-post interaction."""
    sample = data.copy()
    for column in [treated, post]:
        if column not in sample or not set(sample[column].dropna().unique()).issubset({0, 1}):
            raise ValueError(f"{column!r} must be a binary indicator")
    term = "__did_treated_post"
    sample[term] = sample[treated].astype(float) * sample[post].astype(float)
    model = fit_fixed_effects(
        sample,
        outcome,
        [term, *controls],
        entity=entity,
        time=time,
        entity_effects=True,
        time_effects=True,
        covariance=covariance,
    )
    metadata = build_metadata(
        estimator="did",
        outcome=outcome,
        predictors=(term, *controls),
        settings={
            "treated": treated,
            "post": post,
            "entity": entity,
            "time": time,
            "entity_effects": True,
            "time_effects": True,
            "covariance": covariance,
            "controls": tuple(controls),
        },
        sample=sample[[entity, time, outcome, term, *controls]],
        original_nobs=len(data),
    )
    return DIDResult(
        float(model.coefficients[term]),
        float(model.standard_errors[term]),
        float(model.p_values[term]),
        term,
        model,
        metadata,
    )


def fit_event_study(
    data: pd.DataFrame,
    outcome: str,
    treatment_time: str,
    *,
    entity: str,
    time: str,
    window: tuple[int, int] = (-4, 4),
    reference_period: int = -1,
    controls: list[str] | tuple[str, ...] = (),
    covariance: PanelCovariance = "cluster_entity",
) -> EventStudyResult:
    """Estimate a TWFE event study; never-treated observations have missing treatment time."""
    lower, upper = window
    if lower >= upper or not lower <= reference_period <= upper:
        raise ValueError("window and reference_period are inconsistent")
    sample = data.copy()
    relative = sample[time] - sample[treatment_time]
    relative = relative.clip(lower=lower, upper=upper)
    terms: list[str] = []
    periods: list[int] = []
    for period in range(lower, upper + 1):
        if period == reference_period:
            continue
        term = f"event_{'m' + str(abs(period)) if period < 0 else 'p' + str(period)}"
        sample[term] = (relative == period).astype(float)
        terms.append(term)
        periods.append(period)
    model = fit_fixed_effects(
        sample,
        outcome,
        [*terms, *controls],
        entity=entity,
        time=time,
        entity_effects=True,
        time_effects=True,
        covariance=covariance,
    )
    table = model.tidy().set_index("term").loc[terms].reset_index()
    table.insert(0, "event_time", periods)
    pre_terms = [term for term, period in zip(terms, periods, strict=True) if period < 0]
    if pre_terms:
        restriction = np.zeros((len(pre_terms), len(model.coefficients)))
        for row, term in enumerate(pre_terms):
            restriction[row, model.coefficients.index.get_loc(term)] = 1.0
        test = model.raw_result.wald_test(restriction)
        stat, pvalue = float(test.stat), float(test.pval)
    else:
        stat, pvalue = float("nan"), float("nan")
    metadata = build_metadata(
        estimator="event_study",
        outcome=outcome,
        predictors=tuple([*terms, *controls]),
        settings={
            "treatment_time": treatment_time,
            "entity": entity,
            "time": time,
            "window": window,
            "reference_period": reference_period,
            "covariance": covariance,
            "controls": tuple(controls),
            "tail_binning": True,
        },
        sample=sample[[entity, time, outcome, treatment_time, *terms, *controls]],
        original_nobs=len(data),
    )
    return EventStudyResult(table, reference_period, window, stat, pvalue, model, metadata)
