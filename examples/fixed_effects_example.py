"""Auditable fixed-effects example with explicit within variation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from empirical_standards import fit_fixed_effects
from empirical_standards.data import diagnose_panel
from empirical_standards.diagnostics import covariance_sensitivity
from empirical_standards.reporting import collect_models, export_model_collection


def make_data() -> pd.DataFrame:
    rng = np.random.default_rng(91)
    entities, periods = 100, 8
    entity = np.repeat(np.arange(entities), periods)
    time = np.tile(np.arange(periods), entities)
    stable = rng.normal(size=entities)[entity]
    exposure = 0.7 * stable + rng.normal(size=len(entity))
    outcome = stable + 0.2 * time + 1.25 * exposure + rng.normal(scale=0.4, size=len(entity))
    return pd.DataFrame({"entity": entity, "time": time, "outcome": outcome, "exposure": exposure})


def run_example(output: Path) -> None:
    data = make_data()
    diagnostics = diagnose_panel(data, entity="entity", time="time", variables=["exposure"])
    entity_fe = fit_fixed_effects(data, "outcome", ["exposure"], entity="entity", time="time")
    two_way = fit_fixed_effects(
        data,
        "outcome",
        ["exposure"],
        entity="entity",
        time="time",
        time_effects=True,
        covariance="cluster_entity",
    )
    output.mkdir(parents=True, exist_ok=True)
    export_model_collection(
        collect_models({"entity_fe": entity_fe, "two_way_fe": two_way}),
        output,
        prefix="fixed_effects_example",
    )
    diagnostics.variable_variation.to_csv(output / "variable_variation.csv", index=False)
    covariance_sensitivity(
        data, "outcome", ["exposure"], entity="entity", time="time"
    ).to_csv(output / "covariance_sensitivity.csv", index=False)
    design = {
        "claim_type": "within-entity association",
        "identifying_variation": "changes in exposure within entity over time",
        "fixed_effects": ["entity", "time"],
        "primary_covariance": "cluster_entity",
        "causal_claim": False,
        "note": "fixed effects remove stable entity differences, not time-varying confounding",
    }
    (output / "design.json").write_text(json.dumps(design, indent=2), encoding="utf-8")
    print(two_way.tidy().to_string(index=False))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("outputs/fixed_effects_example"))
    run_example(parser.parse_args().output)


if __name__ == "__main__":
    main()
