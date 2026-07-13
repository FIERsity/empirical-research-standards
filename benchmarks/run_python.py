"""Generate Python fixed-effects benchmark output."""

from pathlib import Path

import pandas as pd

from empirical_standards import fit_fixed_effects


def main() -> None:
    directory = Path(__file__).parent
    data = pd.read_csv(directory / "panel_fixture.csv")
    result = fit_fixed_effects(
        data,
        "y",
        ["x", "did"],
        entity="id",
        time="time",
        time_effects=True,
        covariance="cluster_entity",
    )
    result.tidy().to_csv(directory / "python_results.csv", index=False, float_format="%.15g")


if __name__ == "__main__":
    main()
