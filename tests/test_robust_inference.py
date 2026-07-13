from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from empirical_standards.diagnostics import (
    adjust_pvalues,
    leave_one_cluster_out_fe,
    permutation_did,
    wild_cluster_bootstrap_fe,
)


@pytest.fixture
def inference_panel() -> pd.DataFrame:
    rng = np.random.default_rng(481)
    entities, periods = 36, 6
    entity = np.repeat(np.arange(entities), periods)
    time = np.tile(np.arange(periods), entities)
    region = np.repeat(np.arange(6), 6)[entity]
    treated = (entity < 18).astype(int)
    post = (time >= 3).astype(int)
    x = rng.normal(size=len(entity))
    y = (
        rng.normal(size=entities)[entity]
        + 0.15 * time
        + 0.8 * x
        + 1.5 * treated * post
        + rng.normal(scale=0.25, size=len(entity))
    )
    return pd.DataFrame(
        {
            "id": entity,
            "time": time,
            "region": region,
            "treated": treated,
            "post": post,
            "x": x,
            "did": treated * post,
            "y": y,
        }
    )


def test_wild_cluster_bootstrap(inference_panel: pd.DataFrame) -> None:
    result = wild_cluster_bootstrap_fe(
        inference_panel,
        "y",
        ["x", "did"],
        coefficient="did",
        entity="id",
        time="time",
        cluster="id",
        time_effects=True,
        replications=50,
        random_state=11,
    )
    assert result.estimate == pytest.approx(1.5, abs=0.15)
    assert result.successful_replications == 50
    assert 0 <= result.bootstrap_p_value <= 1
    assert result.conf_low < result.estimate < result.conf_high


def test_permutation_did(inference_panel: pd.DataFrame) -> None:
    result = permutation_did(
        inference_panel,
        "y",
        "treated",
        "post",
        entity="id",
        time="time",
        controls=["x"],
        replications=50,
        random_state=12,
    )
    assert result.observed_effect == pytest.approx(1.5, abs=0.15)
    assert len(result.null_distribution) == 50
    assert result.permutation_p_value < 0.1


def test_leave_one_cluster_out(inference_panel: pd.DataFrame) -> None:
    result = leave_one_cluster_out_fe(
        inference_panel,
        "y",
        ["x", "did"],
        coefficient="did",
        entity="id",
        time="time",
        cluster="region",
        time_effects=True,
    )
    assert len(result.estimates) == 6
    assert result.minimum_estimate <= result.full_sample_estimate <= result.maximum_estimate
    assert result.maximum_absolute_change >= 0


@pytest.mark.parametrize("method", ["bonferroni", "holm", "fdr_bh"])
def test_multiple_testing_adjustment(method: str) -> None:
    values = pd.Series([0.001, 0.02, 0.2], index=["a", "b", "c"])
    result = adjust_pvalues(values, method=method)  # type: ignore[arg-type]
    assert result.index.tolist() == ["a", "b", "c"]
    assert result["adjusted_p_value"].between(0, 1).all()
    assert bool(result.loc["a", "reject"])
