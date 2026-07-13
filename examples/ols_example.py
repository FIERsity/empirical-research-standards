"""Run with: uv run python examples/ols_example.py"""

from pathlib import Path

import numpy as np
import pandas as pd

from empirical_standards import fit_ols


def make_data() -> pd.DataFrame:
    """Create deterministic synthetic grouped data."""
    rng = np.random.default_rng(42)
    groups = np.repeat(np.arange(20), 15)
    x = rng.normal(size=len(groups))
    group_shock = rng.normal(scale=0.8, size=20)[groups]
    y = 1.0 + 1.8 * x + group_shock + rng.normal(scale=0.4, size=len(groups))
    return pd.DataFrame({"outcome": y, "treatment": x, "group": groups})


def main() -> None:
    data = make_data()
    classical = fit_ols(data, "outcome", ["treatment"])
    hc1 = fit_ols(data, "outcome", ["treatment"], covariance="HC1")
    clustered = fit_ols(
        data, "outcome", ["treatment"], covariance="cluster", cluster="group"
    )
    output = Path("outputs")
    output.mkdir(exist_ok=True)
    clustered.tidy().to_csv(output / "ols_clustered.csv", index=False)
    print("Classical standard errors:\n", classical.tidy().to_string(index=False))
    print("\nHC1 standard errors:\n", hc1.tidy().to_string(index=False))
    print("\nClustered standard errors:\n", clustered.tidy().to_string(index=False))


if __name__ == "__main__":
    main()

