from __future__ import annotations

import numpy as np
import pandas as pd

from empirical_standards import (
    fit_did,
    fit_event_study,
    fit_fixed_effects,
    fit_ols,
    fit_staggered_did,
)


def make_panel() -> pd.DataFrame:
    rng = np.random.default_rng(99)
    entity = np.repeat(np.arange(20), 6)
    time = np.tile(np.arange(6), 20)
    treated = (entity < 10).astype(int)
    post = (time >= 3).astype(int)
    x = rng.normal(size=len(entity))
    y = (
        rng.normal(size=20)[entity]
        + 0.1 * time
        + x
        + 1.5 * treated * post
        + rng.normal(scale=0.1, size=len(entity))
    )
    return pd.DataFrame(
        {
            "id": entity,
            "time": time,
            "treated": treated,
            "post": post,
            "adoption": np.where(treated == 1, 3.0, np.nan),
            "x": x,
            "y": y,
        }
    )


def assert_common_contract(result: object, estimator: str) -> None:
    tidy = result.tidy()  # type: ignore[attr-defined]
    glance = result.glance()  # type: ignore[attr-defined]
    spec = result.model_spec()  # type: ignore[attr-defined]
    sample = result.sample_info()  # type: ignore[attr-defined]
    provenance = result.provenance()  # type: ignore[attr-defined]
    assert isinstance(tidy, pd.DataFrame) and not tidy.empty
    assert glance["estimator"] == estimator
    assert spec["estimator"] == estimator
    assert sample["estimation_nobs"] > 0
    assert sample["data_fingerprint"].startswith("sha256:")
    assert len(sample["data_fingerprint"]) == 71
    assert provenance["package_versions"]["pandas"] != "not-installed"


def test_ols_and_fixed_effects_metadata() -> None:
    data = make_panel()
    assert_common_contract(fit_ols(data, "y", ["x"]), "ols")
    fe = fit_fixed_effects(data, "y", ["x"], entity="id", time="time", time_effects=True)
    assert_common_contract(fe, "fixed_effects")
    assert fe.model_spec()["settings"]["entity_effects"] is True


def test_causal_result_metadata() -> None:
    data = make_panel()
    did = fit_did(data, "y", "treated", "post", entity="id", time="time", controls=["x"])
    event = fit_event_study(
        data, "y", "adoption", entity="id", time="time", controls=["x"], window=(-2, 2)
    )
    staggered = fit_staggered_did(data, "y", entity="id", time="time", treatment_time="adoption")
    assert_common_contract(did, "did")
    assert_common_contract(event, "event_study")
    assert_common_contract(staggered, "staggered_did")


def test_fingerprint_changes_when_estimation_data_change() -> None:
    data = make_panel()
    first = fit_ols(data, "y", ["x"])
    changed = data.copy()
    changed.loc[0, "x"] += 1
    second = fit_ols(changed, "y", ["x"])
    assert first.sample_info()["data_fingerprint"] != second.sample_info()["data_fingerprint"]
