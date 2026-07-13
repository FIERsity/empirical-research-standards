"""Run panel FE, DID, event study, and staggered DID on deterministic simulated data."""

import numpy as np
import pandas as pd

from empirical_standards import fit_did, fit_event_study, fit_fixed_effects, fit_staggered_did
from empirical_standards.diagnostics import covariance_sensitivity


def make_panel() -> pd.DataFrame:
    rng = np.random.default_rng(20260713)
    entities, periods = 120, 10
    entity = np.repeat(np.arange(entities), periods)
    time = np.tile(np.arange(periods), entities)
    adoption_by_entity = np.r_[np.repeat(4.0, 40), np.repeat(6.0, 40), np.repeat(np.nan, 40)]
    adoption = adoption_by_entity[entity]
    treated_ever = np.isfinite(adoption).astype(int)
    treated_now = np.isfinite(adoption) & (time >= adoption)
    x = rng.normal(size=len(entity))
    y = (
        rng.normal(size=entities)[entity]
        + 0.25 * time
        + 1.4 * x
        + 2.0 * treated_now
        + rng.normal(scale=0.25, size=len(entity))
    )
    return pd.DataFrame(
        {
            "id": entity,
            "time": time,
            "adoption": adoption,
            "treated_ever": treated_ever,
            "treated_now": treated_now.astype(int),
            "x": x,
            "y": y,
            "y_adjusted": y - 1.4 * x,
        }
    )


def main() -> None:
    data = make_panel()
    fe = fit_fixed_effects(
        data,
        "y",
        ["x", "treated_now"],
        entity="id",
        time="time",
        time_effects=True,
        covariance="cluster_two_way",
    )
    did_sample = data.assign(
        post=(data["time"] >= 4).astype(int), treated=(data["adoption"] == 4).astype(int)
    )
    did_sample = did_sample.loc[did_sample["adoption"].isna() | did_sample["adoption"].eq(4)]
    did = fit_did(did_sample, "y", "treated", "post", entity="id", time="time", controls=["x"])
    event = fit_event_study(
        did_sample,
        "y",
        "adoption",
        entity="id",
        time="time",
        controls=["x"],
        window=(-3, 3),
    )
    staggered = fit_staggered_did(
        data,
        "y_adjusted",
        entity="id",
        time="time",
        treatment_time="adoption",
        bootstrap_reps=100,
        random_state=20260713,
    )
    sensitivity = covariance_sensitivity(data, "y", ["x", "treated_now"], entity="id", time="time")
    print("Two-way FE:\n", fe.tidy().to_string(index=False))
    print(f"\nDID effect: {did.effect:.3f} (SE {did.standard_error:.3f})")
    print("\nEvent study:\n", event.estimates.to_string(index=False))
    print(f"\nPre-trend joint-test p-value: {event.pretrend_p_value:.3f}")
    print("\nStaggered event-time ATT:\n", staggered.event_time_effects.to_string(index=False))
    print(f"\nStaggered overall ATT: {staggered.overall_att:.3f}")
    print(f"Staggered bootstrap SE: {staggered.overall_std_error:.3f}")
    print("\nCovariance sensitivity:\n", sensitivity.to_string(index=False))


if __name__ == "__main__":
    main()
