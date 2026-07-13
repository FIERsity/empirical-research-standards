"""Auditable OLS example: uv run python examples/ols_example.py."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from empirical_standards import fit_ols
from empirical_standards.reporting import collect_models, export_model_collection


def make_data() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    groups = np.repeat(np.arange(30), 20)
    x = rng.normal(size=len(groups))
    group_shock = rng.normal(scale=0.8, size=30)[groups]
    heteroskedastic_error = rng.normal(scale=0.3 + 0.2 * np.abs(x))
    y = 1.0 + 1.8 * x + group_shock + heteroskedastic_error
    return pd.DataFrame({"outcome": y, "exposure": x, "group": groups})


def run_example(output: Path) -> None:
    data = make_data()
    models = {
        "classical": fit_ols(data, "outcome", ["exposure"]),
        "hc1": fit_ols(data, "outcome", ["exposure"], covariance="HC1"),
        "clustered": fit_ols(
            data, "outcome", ["exposure"], covariance="cluster", cluster="group"
        ),
    }
    output.mkdir(parents=True, exist_ok=True)
    export_model_collection(collect_models(models), output, prefix="ols_example")
    design = {
        "claim_type": "conditional association",
        "unit_of_observation": "simulated observation nested in group",
        "outcome": "outcome",
        "exposure": "exposure",
        "estimand": "linear conditional association",
        "identifying_variation": "between and within-group exposure variation",
        "primary_covariance": "cluster by group",
        "causal_claim": False,
        "note": "covariance changes uncertainty, not the OLS coefficient or identification",
    }
    (output / "design.json").write_text(json.dumps(design, indent=2), encoding="utf-8")
    print(models["clustered"].tidy().to_string(index=False))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("outputs/ols_example"))
    run_example(parser.parse_args().output)


if __name__ == "__main__":
    main()
