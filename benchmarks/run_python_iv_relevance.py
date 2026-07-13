"""Generate Python conditional instrument-relevance benchmark output."""

from pathlib import Path

import pandas as pd

from empirical_standards import diagnose_iv_relevance


def main() -> None:
    directory = Path(__file__).parent
    data = pd.read_csv(directory / "iv_fixture.csv")
    result = diagnose_iv_relevance(
        data, exogenous=["x"], endogenous=["endogenous"], instruments=["z1", "z2"]
    )
    result.conditional_tests.to_csv(
        directory / "python_iv_relevance_results.csv", index=False, float_format="%.15g"
    )


if __name__ == "__main__":
    main()
