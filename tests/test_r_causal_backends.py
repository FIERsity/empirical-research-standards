"""Optional end-to-end tests for declared R causal backends."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from empirical_standards import fit_staggered_did_r, fit_sun_abraham_r
from empirical_standards.backends import check_r_environment

ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = ROOT / "benchmarks" / "staggered_did"


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
    assert {"conf_low", "conf_high", "simultaneous_conf_low"} <= set(result.tidy())
    assert {"cohort", "time", "event_time", "weight"} <= set(
        result.tidy("aggregation_weights")
    )
    dynamic_weights = result.tidy("aggregation_weights").query("aggregation == 'dynamic'")
    assert np.allclose(dynamic_weights.groupby("event_time")["weight"].sum(), 1.0)
    assert isinstance(result.glance()["pretrend_statistic"], float)
    assert result.provenance()["package"] == "did"


@pytest.mark.skipif(not R_READY, reason="optional R causal packages are unavailable")
def test_fixest_sun_abraham_returns_only_event_time_terms() -> None:
    result = fit_sun_abraham_r(
        _panel(), "y", "g", entity="id", time="time", controls=["x"]
    )
    table = result.tidy()
    assert "event_time" in table
    assert {"conf_low", "conf_high"} <= set(table)
    assert not table["term"].eq("x").any()
    post = table.loc[table["event_time"] >= 0, "estimate"]
    assert post.mean() == pytest.approx(2.0, abs=0.2)
    support = result.tidy("support")
    assert np.allclose(support.groupby("event_time")["aggregation_weight"].sum(), 1.0)
    assert result.glance()["reference_cohort"] == "never_treated"
    assert result.glance()["pretrend_df_num"] > 0


@pytest.mark.skipif(not R_READY, reason="optional R causal packages are unavailable")
def test_locked_staggered_benchmark_matches_expected_outputs() -> None:
    data = pd.read_csv(BENCHMARK / "panel.csv")
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
    expected_did = pd.read_csv(BENCHMARK / "did_event_time_expected.csv")
    expected_sunab = pd.read_csv(BENCHMARK / "sunab_event_time_expected.csv")
    assert_frame_equal(
        staggered.tidy("event_time"), expected_did, check_dtype=False, rtol=1e-7, atol=1e-8
    )
    assert_frame_equal(
        sun_abraham.tidy("event_time"), expected_sunab, check_dtype=False, rtol=1e-7, atol=1e-8
    )


@pytest.mark.skipif(not R_READY, reason="optional R causal packages are unavailable")
def test_multiplier_bootstrap_returns_wider_simultaneous_bands() -> None:
    result = fit_staggered_did_r(
        _panel(),
        "y",
        entity="id",
        time="time",
        treatment_time="g",
        controls=["x"],
        bootstrap=True,
        simultaneous_band=True,
        bootstrap_reps=50,
        random_state=7,
    )
    event = result.tidy("event_time")
    point_width = event["conf_high"] - event["att"]
    simultaneous_width = event["simultaneous_conf_high"] - event["att"]
    assert (simultaneous_width >= point_width).all()
    assert result.glance()["dynamic_critical_value"] > 1.96


@pytest.mark.skipif(not R_READY, reason="optional R causal packages are unavailable")
def test_staggered_r_example_runs_and_exports_audit() -> None:
    completed = subprocess.run(
        [sys.executable, str(ROOT / "examples" / "staggered_did_r_example.py")],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "Callaway-Sant'Anna overall ATT" in completed.stdout
    assert (ROOT / "outputs" / "staggered_did_r" / "audit.json").is_file()


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
