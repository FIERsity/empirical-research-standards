"""Group-time ATT estimation and entity-cluster bootstrap inference."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd
from scipy.stats import norm

from empirical_standards.results import ModelMetadata, build_metadata

ControlGroup = Literal["not_yet_treated", "never_treated"]


@dataclass(frozen=True)
class StaggeredDIDResult:
    group_time_effects: pd.DataFrame
    event_time_effects: pd.DataFrame
    cohort_effects: pd.DataFrame
    calendar_time_effects: pd.DataFrame
    overall_att: float
    overall_std_error: float
    overall_conf_low: float
    overall_conf_high: float
    control_group: ControlGroup
    anticipation: int
    bootstrap_reps: int
    bootstrap_successful: int
    confidence_level: float
    metadata: ModelMetadata

    def tidy(self) -> pd.DataFrame:
        return self.group_time_effects.copy()

    def glance(self) -> pd.Series:
        return pd.Series(
            {
                "estimator": "staggered_did",
                "overall_att": self.overall_att,
                "overall_std_error": self.overall_std_error,
                "overall_conf_low": self.overall_conf_low,
                "overall_conf_high": self.overall_conf_high,
                "cohort_time_effects": len(self.group_time_effects),
                "event_times": len(self.event_time_effects),
                "control_group": self.control_group,
                "anticipation": self.anticipation,
                "bootstrap_reps": self.bootstrap_reps,
                "bootstrap_successful": self.bootstrap_successful,
            }
        )

    def model_spec(self) -> dict[str, object]:
        return self.metadata.spec.to_dict()

    def sample_info(self) -> dict[str, object]:
        return self.metadata.sample.to_dict()

    def provenance(self) -> dict[str, object]:
        return self.metadata.provenance.to_dict()


def _weighted_aggregate(effects: pd.DataFrame, key: str) -> pd.DataFrame:
    result = (
        effects.assign(_weighted=lambda frame: frame["att"] * frame["cohort_size"])
        .groupby(key, as_index=False)
        .agg(_weighted=("_weighted", "sum"), weight=("cohort_size", "sum"))
    )
    result["att"] = result.pop("_weighted") / result["weight"]
    return result


def _point_estimates(
    data: pd.DataFrame,
    outcome: str,
    entity: str,
    time: str,
    treatment_time: str,
    control_group: ControlGroup,
    anticipation: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, float]:
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
    group_time = pd.DataFrame(rows)
    if group_time.empty:
        raise ValueError("no identifiable cohort-time effects")
    event = _weighted_aggregate(group_time, "event_time")
    cohort = _weighted_aggregate(group_time, "cohort")
    calendar = _weighted_aggregate(group_time, "time")
    overall = float(np.average(group_time["att"], weights=group_time["cohort_size"]))
    return group_time, event, cohort, calendar, overall


def _resample_entities(data: pd.DataFrame, entity: str, rng: np.random.Generator) -> pd.DataFrame:
    ids = data[entity].drop_duplicates().to_numpy()
    sampled = rng.choice(ids, size=len(ids), replace=True)
    blocks: list[pd.DataFrame] = []
    for synthetic_id, source_id in enumerate(sampled):
        block = data.loc[data[entity] == source_id].copy()
        block[entity] = synthetic_id
        blocks.append(block)
    return pd.concat(blocks, ignore_index=True)


def _attach_inference(
    table: pd.DataFrame,
    key_columns: list[str],
    draws: list[pd.DataFrame],
    confidence_level: float,
) -> pd.DataFrame:
    result = table.copy()
    ordered = result.set_index(key_columns)["att"]
    aligned = [draw.set_index(key_columns)["att"].reindex(ordered.index) for draw in draws]
    matrix = np.vstack([series.to_numpy(dtype=float) for series in aligned])
    standard_errors = np.nanstd(matrix, axis=0, ddof=1)
    alpha = 1.0 - confidence_level
    critical = float(norm.ppf(1.0 - alpha / 2.0))
    result["std_error"] = standard_errors
    result["conf_low"] = result["att"] - critical * standard_errors
    result["conf_high"] = result["att"] + critical * standard_errors
    usable = standard_errors > 0
    if usable.any():
        studentized = np.abs(
            (matrix[:, usable] - ordered.to_numpy()[usable]) / standard_errors[usable]
        )
        simultaneous_critical = float(
            np.nanquantile(np.nanmax(studentized, axis=1), confidence_level)
        )
    else:
        simultaneous_critical = float("nan")
    result["simultaneous_conf_low"] = result["att"] - simultaneous_critical * standard_errors
    result["simultaneous_conf_high"] = result["att"] + simultaneous_critical * standard_errors
    return result


def fit_staggered_did(
    data: pd.DataFrame,
    outcome: str,
    *,
    entity: str,
    time: str,
    treatment_time: str,
    control_group: ControlGroup = "not_yet_treated",
    anticipation: int = 0,
    bootstrap_reps: int = 0,
    confidence_level: float = 0.95,
    random_state: int | None = None,
) -> StaggeredDIDResult:
    """Estimate cohort-time ATT and optional entity-cluster bootstrap inference."""
    if control_group not in {"not_yet_treated", "never_treated"}:
        raise ValueError("unsupported control_group")
    if anticipation < 0:
        raise ValueError("anticipation must be non-negative")
    if bootstrap_reps != 0 and bootstrap_reps < 50:
        raise ValueError("bootstrap_reps must be 0 or at least 50")
    if not 0 < confidence_level < 1:
        raise ValueError("confidence_level must be strictly between 0 and 1")
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

    group_time, event, cohort, calendar, overall = _point_estimates(
        data, outcome, entity, time, treatment_time, control_group, anticipation
    )
    successful = 0
    overall_se = overall_low = overall_high = float("nan")
    if bootstrap_reps:
        rng = np.random.default_rng(random_state)
        group_draws: list[pd.DataFrame] = []
        event_draws: list[pd.DataFrame] = []
        cohort_draws: list[pd.DataFrame] = []
        calendar_draws: list[pd.DataFrame] = []
        overall_draws: list[float] = []
        for _ in range(bootstrap_reps):
            draw_data = _resample_entities(data, entity, rng)
            try:
                draw = _point_estimates(
                    draw_data, outcome, entity, time, treatment_time, control_group, anticipation
                )
            except ValueError:
                continue
            if (
                not group_time[["cohort", "time"]]
                .set_index(["cohort", "time"])
                .index.equals(draw[0][["cohort", "time"]].set_index(["cohort", "time"]).index)
            ):
                continue
            group_draws.append(draw[0])
            event_draws.append(draw[1])
            cohort_draws.append(draw[2])
            calendar_draws.append(draw[3])
            overall_draws.append(draw[4])
        successful = len(overall_draws)
        if successful < max(30, int(bootstrap_reps * 0.8)):
            raise RuntimeError(
                f"only {successful} of {bootstrap_reps} bootstrap replications were usable"
            )
        group_time = _attach_inference(
            group_time, ["cohort", "time"], group_draws, confidence_level
        )
        event = _attach_inference(event, ["event_time"], event_draws, confidence_level)
        cohort = _attach_inference(cohort, ["cohort"], cohort_draws, confidence_level)
        calendar = _attach_inference(calendar, ["time"], calendar_draws, confidence_level)
        overall_se = float(np.std(overall_draws, ddof=1))
        critical = float(norm.ppf(0.5 + confidence_level / 2.0))
        overall_low, overall_high = overall - critical * overall_se, overall + critical * overall_se

    metadata = build_metadata(
        estimator="staggered_did",
        outcome=outcome,
        predictors=(),
        settings={
            "implementation_status": "educational_reference",
            "entity": entity,
            "time": time,
            "treatment_time": treatment_time,
            "control_group": control_group,
            "anticipation": anticipation,
            "balanced_panel_required": True,
            "inference": "entity_cluster_bootstrap" if bootstrap_reps else "point_estimates_only",
            "bootstrap_reps": bootstrap_reps,
            "bootstrap_successful": successful,
            "confidence_level": confidence_level,
            "random_state": random_state,
        },
        sample=data[required],
        original_nobs=len(data),
    )
    return StaggeredDIDResult(
        group_time,
        event,
        cohort,
        calendar,
        overall,
        overall_se,
        overall_low,
        overall_high,
        control_group,
        anticipation,
        bootstrap_reps,
        successful,
        confidence_level,
        metadata,
    )
