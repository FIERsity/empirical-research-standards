"""Research-grade staggered-treatment estimators backed explicitly by R."""

from __future__ import annotations

from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Literal, cast

import numpy as np
import pandas as pd

from empirical_standards.backends.r import run_r_backend
from empirical_standards.results import build_metadata

RControlGroup = Literal["not_yet_treated", "never_treated"]
RStaggeredMethod = Literal["dr", "ipw", "reg"]
RBasePeriod = Literal["varying", "universal"]


@dataclass(frozen=True)
class RStaggeredDIDResult:
    """Structured result returned by R's ``did::att_gt`` and ``aggte``."""

    group_time_effects: pd.DataFrame
    event_time_effects: pd.DataFrame
    overall_att: float
    overall_std_error: float
    metadata: dict[str, object]

    def tidy(self) -> pd.DataFrame:
        return self.group_time_effects.copy()

    def glance(self) -> pd.Series:
        return pd.Series(self.metadata)

    def model_spec(self) -> dict[str, object]:
        return dict(cast(dict[str, object], self.metadata["specification"]))

    def provenance(self) -> dict[str, object]:
        return {
            key: self.metadata[key]
            for key in ("backend", "package", "r_version", "package_versions", "script")
        }

    def sample_info(self) -> dict[str, object]:
        return dict(cast(dict[str, object], self.metadata["sample"]))


@dataclass(frozen=True)
class RSunAbrahamResult:
    """Aggregated event-time result returned by R's ``fixest::sunab``."""

    event_time_effects: pd.DataFrame
    metadata: dict[str, object]

    def tidy(self) -> pd.DataFrame:
        return self.event_time_effects.copy()

    def glance(self) -> pd.Series:
        return pd.Series(self.metadata)

    def model_spec(self) -> dict[str, object]:
        return dict(cast(dict[str, object], self.metadata["specification"]))

    def provenance(self) -> dict[str, object]:
        return {
            key: self.metadata[key]
            for key in ("backend", "package", "r_version", "package_versions", "script")
        }

    def sample_info(self) -> dict[str, object]:
        return dict(cast(dict[str, object], self.metadata["sample"]))


def _validate_panel(
    data: pd.DataFrame,
    columns: list[str],
    *,
    entity: str,
    time: str,
    treatment_time: str,
) -> None:
    missing = [column for column in columns if column not in data]
    if missing:
        raise KeyError(f"columns not found: {missing}")
    if data.duplicated([entity, time]).any():
        raise ValueError("entity-time pairs must be unique")
    required_complete = [column for column in columns if column != treatment_time]
    if data[required_complete].isna().any().any():
        raise ValueError("outcome, controls, and panel keys must be complete")
    numeric = [column for column in columns if column != entity]
    if any(not pd.api.types.is_numeric_dtype(data[column]) for column in numeric):
        raise TypeError("outcome, controls, time, and treatment_time must be numeric")
    finite = data[numeric].drop(columns=[treatment_time]).to_numpy(dtype=float)
    if not np.isfinite(finite).all():
        raise ValueError("numeric analysis columns must contain only finite values")
    adoption_counts = data.groupby(entity)[treatment_time].nunique(dropna=False)
    if (adoption_counts > 1).any():
        raise ValueError("treatment_time must be constant within entity")


def _script(name: str) -> Path:
    return Path(str(files("empirical_standards.backends.r_scripts").joinpath(name)))


def _attach_python_metadata(
    metadata: dict[str, object],
    *,
    data: pd.DataFrame,
    outcome: str,
    controls: tuple[str, ...],
    specification: dict[str, object],
) -> None:
    shared = build_metadata(
        estimator=str(metadata["estimator"]),
        outcome=outcome,
        predictors=controls,
        settings=specification,
        sample=data,
        original_nobs=len(data),
    )
    metadata["specification"] = specification
    metadata["sample"] = shared.sample.to_dict()
    metadata["python_provenance"] = shared.provenance.to_dict()


def fit_staggered_did_r(
    data: pd.DataFrame,
    outcome: str,
    *,
    entity: str,
    time: str,
    treatment_time: str,
    controls: list[str] | tuple[str, ...] = (),
    control_group: RControlGroup = "not_yet_treated",
    anticipation: int = 0,
    method: RStaggeredMethod = "dr",
    base_period: RBasePeriod = "varying",
    allow_unbalanced_panel: bool = False,
    bootstrap: bool = True,
    simultaneous_band: bool = True,
    bootstrap_reps: int = 999,
    random_state: int = 0,
) -> RStaggeredDIDResult:
    """Estimate Callaway--Sant'Anna group-time effects with R ``did::att_gt``.

    This function never falls back to the narrower Python reference estimator.
    """
    columns = [entity, time, treatment_time, outcome, *controls]
    _validate_panel(data, columns, entity=entity, time=time, treatment_time=treatment_time)
    if anticipation < 0:
        raise ValueError("anticipation must be non-negative")
    if bootstrap and bootstrap_reps < 50:
        raise ValueError("bootstrap_reps must be at least 50 when bootstrap=True")
    specification: dict[str, object] = {
        "outcome": outcome,
        "entity": entity,
        "time": time,
        "treatment_time": treatment_time,
        "controls": list(controls),
        "control_group": {
            "not_yet_treated": "notyettreated",
            "never_treated": "nevertreated",
        }[control_group],
        "anticipation": anticipation,
        "est_method": method,
        "base_period": base_period,
        "allow_unbalanced_panel": allow_unbalanced_panel,
        "bootstrap": bootstrap,
        "simultaneous_band": simultaneous_band and bootstrap,
        "bootstrap_reps": bootstrap_reps,
        "random_state": random_state,
    }
    metadata, tables = run_r_backend(
        data[columns], specification, script=_script("staggered_did.R"),
        required_packages=("did", "jsonlite"),
    )
    _attach_python_metadata(
        metadata,
        data=data[columns],
        outcome=outcome,
        controls=tuple(controls),
        specification=specification,
    )
    return RStaggeredDIDResult(
        tables["group_time"], tables["event_time"],
        float(cast(float, metadata["overall_att"])),
        float(cast(float, metadata["overall_std_error"])),
        metadata,
    )


def fit_sun_abraham_r(
    data: pd.DataFrame,
    outcome: str,
    treatment_time: str,
    *,
    entity: str,
    time: str,
    controls: list[str] | tuple[str, ...] = (),
    reference_period: int = -1,
    cluster: str | None = None,
) -> RSunAbrahamResult:
    """Estimate a Sun--Abraham event study with R ``fixest::sunab``."""
    cluster_name = entity if cluster is None else cluster
    columns = list(dict.fromkeys([entity, time, treatment_time, outcome, *controls, cluster_name]))
    _validate_panel(data, columns, entity=entity, time=time, treatment_time=treatment_time)
    specification: dict[str, object] = {
        "outcome": outcome,
        "entity": entity,
        "time": time,
        "treatment_time": treatment_time,
        "controls": list(controls),
        "reference_period": reference_period,
        "cluster": cluster_name,
    }
    metadata, tables = run_r_backend(
        data[columns], specification, script=_script("sun_abraham.R"),
        required_packages=("fixest", "jsonlite"),
    )
    _attach_python_metadata(
        metadata,
        data=data[columns],
        outcome=outcome,
        controls=tuple(controls),
        specification=specification,
    )
    return RSunAbrahamResult(tables["event_time"], metadata)
