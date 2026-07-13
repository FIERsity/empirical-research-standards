"""Auditable common-adoption DID example with event-study and placebo diagnostics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from empirical_standards import fit_did, fit_event_study
from empirical_standards.diagnostics import placebo_did
from empirical_standards.reporting import (
    collect_models,
    event_study_plot_data,
    export_model_collection,
)


def make_data() -> pd.DataFrame:
    rng = np.random.default_rng(204)
    entities, periods = 120, 10
    entity = np.repeat(np.arange(entities), periods)
    time = np.tile(np.arange(2015, 2025), entities)
    treated = entity < 60
    post = time >= 2021
    control = rng.normal(size=len(entity))
    outcome = (
        rng.normal(size=entities)[entity]
        + 0.12 * (time - 2015)
        + 0.6 * control
        + 1.5 * treated * post
        + rng.normal(scale=0.35, size=len(entity))
    )
    return pd.DataFrame(
        {
            "entity": entity,
            "time": time,
            "outcome": outcome,
            "treated": treated.astype(int),
            "post": post.astype(int),
            "treatment_time": np.where(treated, 2021.0, np.nan),
            "control": control,
        }
    )


def run_example(output: Path) -> None:
    data = make_data()
    did = fit_did(
        data, "outcome", "treated", "post", entity="entity", time="time", controls=["control"]
    )
    event = fit_event_study(
        data,
        "outcome",
        "treatment_time",
        entity="entity",
        time="time",
        controls=["control"],
        window=(-3, 3),
    )
    output.mkdir(parents=True, exist_ok=True)
    export_model_collection(
        collect_models({"did": did, "event_study": event}), output, prefix="did_example"
    )
    event_study_plot_data(event).to_csv(output / "event_study_plot_data.csv", index=False)
    placebo_did(
        data,
        "outcome",
        "treated",
        entity="entity",
        time="time",
        placebo_periods=[2019, 2020],
        controls=["control"],
    ).to_csv(output / "placebo_results.csv", index=False)
    design = {
        "claim_type": "causal under stated assumptions",
        "estimand": "average treated-by-post effect for the treated group",
        "comparison_group": "never-treated entities",
        "treatment_timing": "common adoption in 2021",
        "assumptions": ["parallel trends", "no anticipation", "stable composition"],
        "primary_covariance": "cluster_entity",
        "warning": "pre-period insignificance does not prove parallel trends",
    }
    (output / "design.json").write_text(json.dumps(design, indent=2), encoding="utf-8")
    print(did.tidy().to_string(index=False))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("outputs/did_example"))
    run_example(parser.parse_args().output)


if __name__ == "__main__":
    main()
