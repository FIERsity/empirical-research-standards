"""Run an auditable data-to-results panel workflow on deterministic simulated data."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from empirical_standards import fit_did, fit_event_study, fit_fixed_effects
from empirical_standards.data import diagnose_panel, merge_validated
from empirical_standards.diagnostics import (
    covariance_sensitivity,
    fit_fe_heterogeneity,
    placebo_did,
)
from empirical_standards.reporting import collect_models, export_model_collection


def make_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Create a balanced city panel plus one-row-per-city attributes."""
    rng = np.random.default_rng(20260713)
    cities, periods = 80, 10
    city = np.repeat(np.arange(cities), periods)
    year = np.tile(np.arange(2015, 2015 + periods), cities)
    treated_city = city < 40
    treatment_year = np.where(treated_city, 2021.0, np.nan)
    post = year >= 2021
    x = rng.normal(size=len(city))
    region_by_city = np.where(np.arange(cities) % 2 == 0, "east", "west")
    heterogeneous_effect = np.where(region_by_city[city] == "east", 1.5, 1.0)
    outcome = (
        rng.normal(size=cities)[city]
        + 0.15 * (year - 2015)
        + 0.8 * x
        + treated_city * post * heterogeneous_effect
        + rng.normal(scale=0.35, size=len(city))
    )
    panel = pd.DataFrame(
        {
            "city": city,
            "year": year,
            "outcome": outcome,
            "control": x,
            "treated": treated_city.astype(int),
            "post": post.astype(int),
            "treated_now": (treated_city & post).astype(int),
            "treatment_year": treatment_year,
        }
    )
    attributes = pd.DataFrame({"city": np.arange(cities), "region": region_by_city})
    return panel, attributes


def run_workflow(output: Path) -> dict[str, object]:
    panel, attributes = make_data()
    merged = merge_validated(panel, attributes, on="city", relationship="many_to_one")
    data = merged.data
    diagnostics = diagnose_panel(
        data,
        entity="city",
        time="year",
        variables=["outcome", "control", "treated_now"],
    )

    fe = fit_fixed_effects(
        data,
        "outcome",
        ["control", "treated_now"],
        entity="city",
        time="year",
        time_effects=True,
        covariance="cluster_entity",
    )
    did = fit_did(
        data,
        "outcome",
        "treated",
        "post",
        entity="city",
        time="year",
        controls=["control"],
        covariance="cluster_entity",
    )
    event = fit_event_study(
        data,
        "outcome",
        "treatment_year",
        entity="city",
        time="year",
        controls=["control"],
        window=(-3, 3),
        covariance="cluster_entity",
    )
    sensitivity = covariance_sensitivity(
        data,
        "outcome",
        ["control", "treated_now"],
        entity="city",
        time="year",
    )
    placebos = placebo_did(
        data,
        "outcome",
        "treated",
        entity="city",
        time="year",
        placebo_periods=[2019, 2020],
        controls=["control"],
    )
    heterogeneity = fit_fe_heterogeneity(
        data,
        "outcome",
        "treated_now",
        entity="city",
        time="year",
        group="region",
        controls=["control"],
    )

    output.mkdir(parents=True, exist_ok=True)
    paths = export_model_collection(
        collect_models({"fixed_effects": fe, "did": did, "event_study": event}),
        output,
        prefix="research_workflow",
    )
    diagnostics.summary().rename("value").to_csv(output / "panel_diagnostics.csv")
    sensitivity.to_csv(output / "covariance_sensitivity.csv", index=False)
    placebos.to_csv(output / "placebo_results.csv", index=False)
    heterogeneity.tidy().to_csv(output / "heterogeneity_results.csv", index=False)
    manifest: dict[str, object] = {
        "design": "common-adoption DID with city and year fixed effects",
        "estimand": "average treated-by-post effect in the simulated sample",
        "unit_of_observation": "city-year",
        "treatment_assignment": "simulated; first 40 cities treated from 2021",
        "primary_covariance": "cluster_entity",
        "original_nobs": len(panel),
        "estimation_nobs": fe.nobs,
        "merge_relationship": "many_to_one",
        "parallel_trends": "true by simulation; must be justified in real research",
        "exported_files": sorted(path.name for path in paths.values()),
    }
    (output / "workflow_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("outputs/research_workflow"))
    args = parser.parse_args()
    manifest = run_workflow(args.output)
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
