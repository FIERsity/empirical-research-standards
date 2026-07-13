# Python Empirical Standards

`python-empirical-standards` is a small, transparent, and testable foundation for
empirical research and econometric analysis in Python. It documents how data and
model choices are made instead of hiding consequential decisions behind a large framework.

## Status

The project is at version 0.5.0. It implements validated data merges and panel diagnostics,
validated OLS, panel fixed effects, classic
DID, dynamic event studies, and a transparent first cohort-time ATT estimator for staggered
adoption. This remains a working foundation, not a complete econometrics library.

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

Panel and causal estimators are similarly explicit:

```python
from empirical_standards import fit_fixed_effects, fit_did

fe = fit_fixed_effects(data, "y", ["x"], entity="city", time="year",
                       time_effects=True, covariance="cluster_two_way")
did = fit_did(data, "y", "treated", "post", entity="city", time="year",
              controls=["x"], covariance="cluster_entity")
```

See [panel and DID conventions](docs/panel_and_did.md), including current limitations of
staggered-DID inference.

Validate data structure before estimation:

```python
from empirical_standards.data import diagnose_panel, merge_validated

merged = merge_validated(panel, attributes, on="city", relationship="many_to_one")
diagnostics = diagnose_panel(
    merged.data, entity="city", time="year", variables=["outcome", "treatment"]
)
print(diagnostics.summary())
```

See [data-validation conventions](docs/data_validation.md).

Every model result provides `tidy()`, `glance()`, `model_spec()`, `sample_info()`, and
`provenance()`. See the [result metadata contract](docs/results.md).

Run the complete example with:

```bash
uv run python examples/ols_example.py
uv run python examples/panel_did_example.py
uv run python examples/data_validation_example.py
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

The next priority is inference for cohort-time ATT (cluster bootstrap or influence-function
standard errors and simultaneous bands), formal subgroup interaction tests, and frozen
Stata/R comparison fixtures. Later modules may cover IV, spatial models, data lineage,
machine-learning evaluation, and standardized tables and figures.

See [CONTRIBUTING.md](CONTRIBUTING.md) before proposing a new estimator. Each method should
arrive with assumptions, a runnable example, validation failures, numerical tests, and a
documented external comparison strategy.

## License

MIT
