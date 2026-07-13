# Python Empirical Standards

`python-empirical-standards` is a small, transparent, and testable foundation for
empirical research and econometric analysis in Python. It documents how data and
model choices are made instead of hiding consequential decisions behind a large framework.

## Status

The project is at version 0.1.0. The first implemented component is ordinary least
squares with classical, HC1, and one-way cluster-robust standard errors. This is a working
starting point, not a complete econometrics library.

## Principles

- Correctness and explicit model specifications before convenience.
- Reproducible environments, deterministic examples, and tested outputs.
- Independent modules that can be adopted and verified separately.
- Small additions driven by concrete research workflows.
- Results that can be cross-checked against Stata, R, or direct `statsmodels` calls.

This project does not interpret substantive research questions, choose a causal design for
the researcher, or replace careful inspection of assumptions and source data.

## Install and verify

Install [uv](https://docs.astral.sh/uv/), then run:

```bash
uv sync
uv run pytest
uv run ruff check .
uv run mypy
uv build
```

## Quick start

```python
import pandas as pd
from empirical_standards import fit_ols

data = pd.DataFrame({
    "y": [1.0, 2.2, 2.8, 4.1, 5.2, 5.8],
    "x": [0.0, 1.0, 2.0, 3.0, 4.0, 5.0],
    "region": [1, 1, 1, 2, 2, 2],
})

result = fit_ols(
    data,
    outcome="y",
    predictors=["x"],
    covariance="cluster",
    cluster="region",
)
print(result.tidy())
```

Missing values cause an error by default. Pass `drop_missing=True` to explicitly request
complete-case estimation. See [the OLS specification](docs/ols.md) for all conventions.

Run the complete example with:

```bash
uv run python examples/ols_example.py
```

It writes a tidy CSV to `outputs/ols_clustered.csv`.

## Repository layout

```text
src/empirical_standards/  Installable source package
  models/                 Econometric estimators
tests/                    Numerical and validation tests
examples/                 Deterministic, runnable workflows
docs/                     Method specifications and conventions
.github/workflows/        Continuous integration
```

## Roadmap

The next useful addition is panel fixed effects with clearly specified absorbed effects and
clustered inference, backed by frozen Stata/R comparison data. Later modules may cover data
validation and lineage, DID and event studies, IV, spatial models, machine-learning
evaluation, robustness workflows, and standardized tables and figures.

See [CONTRIBUTING.md](CONTRIBUTING.md) before proposing a new estimator. Each method should
arrive with assumptions, a runnable example, validation failures, numerical tests, and a
documented external comparison strategy.

## License

MIT

