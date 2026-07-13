from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from empirical_standards import fit_did, fit_event_study, fit_fixed_effects, fit_staggered_did
from empirical_standards.diagnostics import covariance_sensitivity, fit_fe_by_group


@pytest.fixture
def panel() -> pd.DataFrame:
    rng = np.random.default_rng(1234)
    entities, periods = 80, 10
    entity = np.repeat(np.arange(entities), periods)
    time = np.tile(np.arange(periods), entities)
    x = rng.normal(size=len(entity))
    entity_effect = rng.normal(size=entities)[entity]
    time_effect = rng.normal(scale=0.3, size=periods)[time]
    treated = (entity < 40).astype(int)
    post = (time >= 5).astype(int)
    y = (
        entity_effect
        + time_effect
        + 1.5 * x
        + 2.0 * treated * post
        + rng.normal(scale=0.25, size=len(entity))
    )
    group = np.where(entity < 40, "A", "B")
    return pd.DataFrame(
        {
            "id": entity,
            "time": time,
            "x": x,
            "y": y,
            "treated": treated,
            "post": post,
            "group": group,
        }
    )


def test_one_and_two_way_fixed_effects(panel: pd.DataFrame) -> None:
    one = fit_fixed_effects(panel, "y", ["x"], entity="id", time="time")
    two = fit_fixed_effects(
        panel, "y", ["x"], entity="id", time="time", time_effects=True, covariance="cluster_two_way"
    )
    assert one.coefficients["x"] == pytest.approx(1.5, abs=0.08)
    assert two.coefficients["x"] == pytest.approx(1.5, abs=0.08)
    assert two.entities == 80 and two.periods == 10


def test_did_recovers_effect(panel: pd.DataFrame) -> None:
    result = fit_did(panel, "y", "treated", "post", entity="id", time="time", controls=["x"])
    assert result.effect == pytest.approx(2.0, abs=0.1)


def test_event_study_and_pretrend(panel: pd.DataFrame) -> None:
    panel = panel.assign(adoption=np.where(panel["treated"].eq(1), 5.0, np.nan))
    result = fit_event_study(
        panel,
        "y",
        "adoption",
        entity="id",
        time="time",
        controls=["x"],
        window=(-3, 3),
    )
    assert set(result.estimates["event_time"]) == {-3, -2, 0, 1, 2, 3}
    assert result.estimates.loc[
        result.estimates.event_time >= 0, "estimate"
    ].mean() == pytest.approx(2.0, abs=0.15)
    assert 0 <= result.pretrend_p_value <= 1


def test_staggered_group_time_att() -> None:
    rng = np.random.default_rng(8)
    ids, periods = 90, 8
    entity = np.repeat(np.arange(ids), periods)
    time = np.tile(np.arange(periods), ids)
    adoption_by_id = np.r_[np.repeat(3.0, 30), np.repeat(5.0, 30), np.repeat(np.nan, 30)]
    adoption = adoption_by_id[entity]
    treated_now = np.isfinite(adoption) & (time >= adoption)
    y = (
        rng.normal(size=ids)[entity]
        + 0.2 * time
        + 1.75 * treated_now
        + rng.normal(scale=0.1, size=len(entity))
    )
    data = pd.DataFrame({"id": entity, "time": time, "adoption": adoption, "y": y})
    result = fit_staggered_did(data, "y", entity="id", time="time", treatment_time="adoption")
    assert result.overall_att == pytest.approx(1.75, abs=0.08)
    assert not result.group_time_effects.empty
    assert set(result.cohort_effects["cohort"]) == {3.0, 5.0}
    assert not result.calendar_time_effects.empty


def test_staggered_cluster_bootstrap_inference() -> None:
    rng = np.random.default_rng(18)
    ids, periods = 60, 6
    entity = np.repeat(np.arange(ids), periods)
    time = np.tile(np.arange(periods), ids)
    adoption_by_id = np.r_[np.repeat(2.0, 20), np.repeat(4.0, 20), np.repeat(np.nan, 20)]
    adoption = adoption_by_id[entity]
    treated = np.isfinite(adoption) & (time >= adoption)
    y = (
        rng.normal(size=ids)[entity]
        + 0.1 * time
        + 1.25 * treated
        + rng.normal(scale=0.2, size=len(entity))
    )
    data = pd.DataFrame({"id": entity, "time": time, "adoption": adoption, "y": y})
    result = fit_staggered_did(
        data,
        "y",
        entity="id",
        time="time",
        treatment_time="adoption",
        bootstrap_reps=60,
        random_state=42,
    )
    assert result.bootstrap_successful >= 48
    assert result.overall_std_error > 0
    assert result.overall_conf_low < result.overall_att < result.overall_conf_high
    for table in [
        result.group_time_effects,
        result.event_time_effects,
        result.cohort_effects,
        result.calendar_time_effects,
    ]:
        assert table["std_error"].gt(0).all()
        assert table["simultaneous_conf_low"].le(table["conf_low"]).all()
        assert table["simultaneous_conf_high"].ge(table["conf_high"]).all()


def test_staggered_bootstrap_validation() -> None:
    data = pd.DataFrame(
        {
            "id": [1, 1, 2, 2],
            "time": [0, 1, 0, 1],
            "adoption": [1.0, 1.0, np.nan, np.nan],
            "y": [0.0, 1.0, 0.0, 0.0],
        }
    )
    with pytest.raises(ValueError, match="at least 50"):
        fit_staggered_did(
            data, "y", entity="id", time="time", treatment_time="adoption", bootstrap_reps=20
        )


def test_diagnostics(panel: pd.DataFrame) -> None:
    sensitivity = covariance_sensitivity(panel, "y", ["x"], entity="id", time="time")
    assert set(sensitivity["covariance"]) == {"robust", "cluster_entity", "cluster_two_way"}
    heterogeneous = fit_fe_by_group(panel, "y", ["x"], entity="id", time="time", group="group")
    assert set(heterogeneous.estimates["group_value"]) == {"A", "B"}


def test_panel_validation(panel: pd.DataFrame) -> None:
    with pytest.raises(ValueError, match="uniquely"):
        fit_fixed_effects(pd.concat([panel, panel.iloc[[0]]]), "y", ["x"], entity="id", time="time")
