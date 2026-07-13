"""Cohort-interacted event studies for staggered treatment adoption."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

import numpy as np
import pandas as pd
from scipy.stats import norm

from empirical_standards.panel.fixed_effects import (
    FixedEffectsResult,
    PanelCovariance,
    fit_fixed_effects,
)
from empirical_standards.results import ModelMetadata, build_metadata


@dataclass(frozen=True)
class SunAbrahamResult:
    cohort_event_effects: pd.DataFrame
    event_time_effects: pd.DataFrame
    reference_period: int
    window: tuple[int, int]
    pretrend_statistic: float
    pretrend_p_value: float
    model: FixedEffectsResult
    metadata: ModelMetadata

    def tidy(self) -> pd.DataFrame:
        return self.event_time_effects.copy()

    def glance(self) -> pd.Series:
        return pd.Series(
            {
                "estimator": "sun_abraham",
                "nobs": self.model.nobs,
                "cohorts": self.cohort_event_effects["cohort"].nunique(),
                "reference_period": self.reference_period,
                "window_lower": self.window[0],
                "window_upper": self.window[1],
                "pretrend_statistic": self.pretrend_statistic,
                "pretrend_p_value": self.pretrend_p_value,
                "covariance": self.model.covariance,
            }
        )

    def model_spec(self) -> dict[str, Any]:
        return self.metadata.spec.to_dict()

    def sample_info(self) -> dict[str, Any]:
        return self.metadata.sample.to_dict()

    def provenance(self) -> dict[str, Any]:
        return self.metadata.provenance.to_dict()


def fit_sun_abraham(
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
    confidence_level: float = 0.95,
) -> SunAbrahamResult:
    """Estimate cohort-interacted event effects and cohort-size weighted aggregates."""
    lower, upper = window
    if lower >= upper or not lower <= reference_period <= upper:
        raise ValueError("window and reference_period are inconsistent")
    if not 0 < confidence_level < 1:
        raise ValueError("confidence_level must be strictly between 0 and 1")
    required = [entity, time, treatment_time, outcome, *controls]
    missing = [column for column in required if column not in data]
    if missing:
        raise KeyError(f"columns not found: {missing}")
    if data.duplicated([entity, time]).any():
        raise ValueError("entity-time pairs must be unique")
    adoption_counts = data.groupby(entity)[treatment_time].nunique(dropna=False)
    if (adoption_counts > 1).any():
        raise ValueError("treatment_time must be constant within entity")
    if not data[treatment_time].isna().any():
        raise ValueError("Sun-Abraham estimation currently requires never-treated entities")

    sample = data.copy()
    cohorts = sorted(sample[treatment_time].dropna().unique())
    relative = (sample[time] - sample[treatment_time]).clip(lower=lower, upper=upper)
    terms: list[str] = []
    term_info: list[tuple[str, float, int, int]] = []
    for cohort_index, cohort in enumerate(cohorts):
        cohort_size = int(sample.loc[sample[treatment_time] == cohort, entity].nunique())
        for period in range(lower, upper + 1):
            if period == reference_period:
                continue
            mask = (sample[treatment_time] == cohort) & (relative == period)
            if not mask.any():
                continue
            event_label = "m" + str(abs(period)) if period < 0 else "p" + str(period)
            term = f"__sa_c{cohort_index}_e{event_label}"
            sample[term] = mask.astype(float)
            terms.append(term)
            term_info.append((term, float(cohort), period, cohort_size))
    if not terms:
        raise ValueError("no identifiable cohort-event terms")
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
    covariance_matrix = pd.DataFrame(model.raw_result.cov).loc[terms, terms]
    critical = float(norm.ppf(0.5 + confidence_level / 2))
    cohort_rows: list[dict[str, float | str]] = []
    for term, cohort, period, cohort_size in term_info:
        estimate = float(model.coefficients[term])
        se = float(model.standard_errors[term])
        cohort_rows.append(
            {
                "term": term,
                "cohort": cohort,
                "event_time": float(period),
                "cohort_size": float(cohort_size),
                "estimate": estimate,
                "std_error": se,
                "conf_low": estimate - critical * se,
                "conf_high": estimate + critical * se,
            }
        )
    cohort_effects = pd.DataFrame(cohort_rows)
    aggregate_rows: list[dict[str, float]] = []
    for event_time_value, period_rows in cohort_effects.groupby("event_time", sort=True):
        event_time_number = cast(float, event_time_value)
        period_terms = period_rows["term"].tolist()
        weights = period_rows["cohort_size"].to_numpy(dtype=float)
        weights = weights / weights.sum()
        estimates = period_rows["estimate"].to_numpy(dtype=float)
        estimate = float(weights @ estimates)
        sub_covariance = covariance_matrix.loc[period_terms, period_terms].to_numpy(dtype=float)
        se = float(np.sqrt(weights @ sub_covariance @ weights))
        aggregate_rows.append(
            {
                "event_time": event_time_number,
                "estimate": estimate,
                "std_error": se,
                "statistic": estimate / se,
                "p_value": float(2 * norm.sf(abs(estimate / se))),
                "conf_low": estimate - critical * se,
                "conf_high": estimate + critical * se,
                "cohorts": float(len(period_rows)),
                "treated_entities": float(period_rows["cohort_size"].sum()),
            }
        )
    event_effects = pd.DataFrame(aggregate_rows)
    pre_terms = [term for term, _, period, _ in term_info if period < 0]
    if pre_terms:
        restriction = np.zeros((len(pre_terms), len(model.coefficients)))
        for row, term in enumerate(pre_terms):
            restriction[row, model.coefficients.index.get_loc(term)] = 1
        test = model.raw_result.wald_test(restriction)
        pre_stat, pre_p = float(test.stat), float(test.pval)
    else:
        pre_stat = pre_p = float("nan")
    metadata = build_metadata(
        estimator="sun_abraham",
        outcome=outcome,
        predictors=tuple([*terms, *controls]),
        settings={
            "implementation_status": "educational_reference",
            "treatment_time": treatment_time,
            "entity": entity,
            "time": time,
            "window": window,
            "reference_period": reference_period,
            "controls": tuple(controls),
            "covariance": covariance,
            "aggregation": "cohort_size_weighted",
            "tail_binning": True,
            "control_group": "never_treated",
            "confidence_level": confidence_level,
        },
        sample=sample[required + terms],
        original_nobs=len(data),
    )
    return SunAbrahamResult(
        cohort_effects, event_effects, reference_period, window, pre_stat, pre_p, model, metadata
    )
