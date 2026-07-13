"""Regenerate the fixed staggered-treatment benchmark artifacts."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from empirical_standards import fit_staggered_did_r, fit_sun_abraham_r

HERE = Path(__file__).resolve().parent


def make_benchmark_panel() -> pd.DataFrame:
    """Create a deterministic balanced panel with heterogeneous dynamic effects."""
    rng = np.random.default_rng(20260714)
    entities, periods = 75, 8
    entity = np.repeat(np.arange(entities), periods)
    time = np.tile(np.arange(periods), entities)
    adoption = np.r_[np.repeat(3.0, 25), np.repeat(5.0, 25), np.repeat(np.nan, 25)][entity]
    event_time = time - adoption
    treated = np.isfinite(adoption) & (event_time >= 0)
    treatment_effect = np.where(treated, 1.5 + 0.2 * np.minimum(event_time, 3), 0.0)
    x = rng.normal(size=len(entity))
    outcome = (
        rng.normal(scale=0.8, size=entities)[entity]
        + 0.15 * time
        + 0.7 * x
        + treatment_effect
        + rng.normal(scale=0.15, size=len(entity))
    )
    return pd.DataFrame(
        {"entity": entity, "period": time, "adoption": adoption, "x": x, "outcome": outcome}
    )


def main() -> None:
    data = make_benchmark_panel()
    data.to_csv(HERE / "panel.csv", index=False)
    specification = {
        "outcome": "outcome",
        "entity": "entity",
        "time": "period",
        "treatment_time": "adoption",
        "controls": ["x"],
        "control_group": "not_yet_treated",
        "bootstrap": False,
        "simultaneous_band": False,
        "confidence_level": 0.95,
    }
    (HERE / "specification.json").write_text(
        json.dumps(specification, indent=2), encoding="utf-8"
    )
    staggered = fit_staggered_did_r(
        data,
        "outcome",
        entity="entity",
        time="period",
        treatment_time="adoption",
        controls=["x"],
        bootstrap=False,
        simultaneous_band=False,
    )
    sun_abraham = fit_sun_abraham_r(
        data,
        "outcome",
        "adoption",
        entity="entity",
        time="period",
        controls=["x"],
    )
    staggered.tidy("group_time").to_csv(HERE / "did_group_time_expected.csv", index=False)
    staggered.tidy("event_time").to_csv(HERE / "did_event_time_expected.csv", index=False)
    staggered.tidy("cohort").to_csv(HERE / "did_cohort_expected.csv", index=False)
    sun_abraham.tidy("event_time").to_csv(HERE / "sunab_event_time_expected.csv", index=False)
    staggered_provenance = staggered.provenance()
    sun_abraham_provenance = sun_abraham.provenance()
    staggered_provenance["script"] = Path(str(staggered_provenance["script"])).name
    sun_abraham_provenance["script"] = Path(str(sun_abraham_provenance["script"])).name
    environment = {
        "staggered": staggered_provenance,
        "sun_abraham": sun_abraham_provenance,
        "expected_overall": {
            "staggered_did": staggered.overall_att,
            "sun_abraham": sun_abraham.overall_att,
        },
    }
    (HERE / "environment.json").write_text(
        json.dumps(environment, indent=2, default=str), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
