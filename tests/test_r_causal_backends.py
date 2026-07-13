"""Optional end-to-end tests for declared R causal backends."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from empirical_standards import fit_staggered_did_r, fit_sun_abraham_r
from empirical_standards.backends import check_r_environment


def _panel() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    entities, periods = 90, 8
    entity = np.repeat(np.arange(entities), periods)
    time = np.tile(np.arange(periods), entities)
    adoption = np.r_[np.repeat(3.0, 30), np.repeat(5.0, 30), np.repeat(np.nan, 30)][entity]
    x = rng.normal(size=len(entity))
    treated = np.isfinite(adoption) & (time >= adoption)
    y = (
        rng.normal(size=entities)[entity]
        + 0.2 * time
        + x
        + 2 * treated
        + rng.normal(0, 0.1, len(entity))
    )
    return pd.DataFrame({"id": entity, "time": time, "g": adoption, "x": x, "y": y})


R_READY = check_r_environment(("did", "fixest", "jsonlite")).available


@pytest.mark.skipif(not R_READY, reason="optional R causal packages are unavailable")
def test_callaway_santanna_r_recovers_simulated_effect() -> None:
    result = fit_staggered_did_r(
        _panel(), "y", entity="id", time="time", treatment_time="g", controls=["x"],
        bootstrap=False, simultaneous_band=False,
    )
    assert result.overall_att == pytest.approx(2.0, abs=0.2)
    assert {"cohort", "time", "att", "std_error"} <= set(result.tidy())
    assert result.provenance()["package"] == "did"


@pytest.mark.skipif(not R_READY, reason="optional R causal packages are unavailable")
def test_fixest_sun_abraham_returns_only_event_time_terms() -> None:
    result = fit_sun_abraham_r(
        _panel(), "y", "g", entity="id", time="time", controls=["x"]
    )
    table = result.tidy()
    assert "event_time" in table
    assert not table["term"].eq("x").any()
    post = table.loc[table["event_time"] >= 0, "estimate"]
    assert post.mean() == pytest.approx(2.0, abs=0.2)


def test_r_backend_environment_reports_missing_package() -> None:
    environment = check_r_environment(("package_that_does_not_exist_ers",))
    assert not environment.available
    assert environment.packages["package_that_does_not_exist_ers"] is None


def test_r_wrapper_validates_panel_before_starting_r() -> None:
    duplicated = pd.concat([_panel(), _panel().iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError, match="entity-time pairs"):
        fit_staggered_did_r(
            duplicated, "y", entity="id", time="time", treatment_time="g", bootstrap=False
        )
