# Staggered-treatment numerical benchmark

`panel.csv` is a deterministic balanced panel with two adoption cohorts and one never-treated
cohort. The expected CSV files are generated independently by the locked R `did` and `fixest`
backends and are compared against fresh backend runs in the test suite.

Regenerate only when deliberately updating the R environment or output contract:

```bash
uv run python benchmarks/staggered_did/generate_benchmark.py
```

Review every numerical diff and update `environment.json` in the same commit. A package upgrade is
not, by itself, sufficient reason to accept changed estimates or inference.
