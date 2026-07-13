"""Transparent group-time ATT estimator for staggered treatment adoption."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd

from empirical_standards.results import ModelMetadata, build_metadata

ControlGroup = Literal["not_yet_treated", "never_treated"]


@dataclass(frozen=True)
class StaggeredDIDResult:
    group_time_effects: pd.DataFrame
    event_time_effects: pd.DataFrame
    overall_att: float
    control_group: ControlGroup
    anticipation: int
    metadata: ModelMetadata

    def tidy(self) -> pd.DataFrame:
        return self.group_time_effects.copy()

    def glance(self) -> pd.Series:
        return pd.Series(
            {
                "estimator": "staggered_did",
                "overall_att": self.overall_att,
                "cohort_time_effects": len(self.group_time_effects),
                "event_times": len(self.event_time_effects),
                "control_group": self.control_group,
                "anticipation": self.anticipation,
            }
        )

    def model_spec(self) -> dict[str, object]:
        return self.metadata.spec.to_dict()

    def sample_info(self) -> dict[str, object]:
        return self.metadata.sample.to_dict()

    def provenance(self) -> dict[str, object]:
        return self.metadata.provenance.to_dict()


def fit_staggered_did(
    data: pd.DataFrame,
    outcome: str,
    *,
    entity: str,
    time: str,
    treatment_time: str,
    control_group: ControlGroup = "not_yet_treated",
    anticipation: int = 0,
) -> StaggeredDIDResult:
    """Estimate cohort-time ATT using changes from each cohort's last untreated period.

    This first version targets balanced panels and reports point estimates. It deliberately
    does not label TWFE coefficients as staggered-treatment effects.
    """
    if control_group not in {"not_yet_treated", "never_treated"}:
        raise ValueError("unsupported control_group")
    required = [entity, time, treatment_time, outcome]
    if any(column not in data for column in required):
        raise KeyError("required staggered-DID columns are missing")
    if data.duplicated([entity, time]).any():
        raise ValueError("entity-time pairs must be unique")
    if data[[entity, time, outcome]].isna().any().any():
        raise ValueError("panel keys and outcomes must be complete")
    adoption_counts = data.groupby(entity)[treatment_time].nunique(dropna=False)
    if (adoption_counts > 1).any():
        raise ValueError("treatment_time must be constant within entity")
    panel = data.set_index([entity, time]).sort_index()
    times = sorted(data[time].unique())
    cohorts = sorted(data[treatment_time].dropna().unique())
    rows: list[dict[str, float]] = []
    for cohort in cohorts:
        baseline = cohort - anticipation - 1
        if baseline not in times:
            continue
        treated_ids = data.loc[data[treatment_time] == cohort, entity].unique()
        for period in times:
            if period < cohort - anticipation:
                continue
            if control_group == "never_treated":
                control_ids = data.loc[data[treatment_time].isna(), entity].unique()
            else:
                control_ids = data.loc[
                    data[treatment_time].isna() | (data[treatment_time] > period + anticipation),
                    entity,
                ].unique()
            if len(control_ids) == 0:
                continue
            try:
                treated_change = (
                    panel.loc[(treated_ids, period), outcome].mean()
                    - panel.loc[(treated_ids, baseline), outcome].mean()
                )
                control_change = (
                    panel.loc[(control_ids, period), outcome].mean()
                    - panel.loc[(control_ids, baseline), outcome].mean()
                )
            except KeyError as error:
                raise ValueError("staggered DID currently requires a balanced panel") from error
            rows.append(
                {
                    "cohort": float(cohort),
                    "time": float(period),
                    "event_time": float(period - cohort),
                    "att": float(treated_change - control_change),
                    "cohort_size": float(len(treated_ids)),
                    "control_size": float(len(control_ids)),
                }
            )
    effects = pd.DataFrame(rows)
    if effects.empty:
        raise ValueError("no identifiable cohort-time effects")
    event = (
        effects.assign(weighted=lambda x: x.att * x.cohort_size)
        .groupby("event_time", as_index=False)
        .agg(weighted=("weighted", "sum"), weight=("cohort_size", "sum"))
    )
    event["att"] = event.pop("weighted") / event.pop("weight")
    overall = np.average(effects["att"], weights=effects["cohort_size"])
    metadata = build_metadata(
        estimator="staggered_did",
        outcome=outcome,
        predictors=(),
        settings={
            "entity": entity,
            "time": time,
            "treatment_time": treatment_time,
            "control_group": control_group,
            "anticipation": anticipation,
            "balanced_panel_required": True,
            "inference": "point_estimates_only",
        },
        sample=data[required],
        original_nobs=len(data),
    )
    return StaggeredDIDResult(effects, event, float(overall), control_group, anticipation, metadata)
