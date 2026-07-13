# Contributing

Keep contributions small and auditable. Before adding an estimator, document its estimand,
sample rules, defaults, covariance convention, failure modes, and planned Stata/R comparison.

Run the complete local check before opening a pull request:

```bash
uv sync
uv run pytest
uv run ruff check .
uv run mypy
uv build
```

New behavior requires focused tests and a runnable example. Avoid generic base classes or
configuration layers until at least two implemented modules demonstrate the same need.

