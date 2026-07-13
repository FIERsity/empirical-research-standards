# Changelog

All notable changes are documented here.

## 0.5.0 - 2026-07-13

- Add cohort, calendar-time, event-time, and overall staggered-DID aggregation.
- Add entity-cluster bootstrap inference with reproducible random sampling.
- Add pointwise confidence intervals and max-studentized simultaneous confidence bands.
- Report requested and usable bootstrap replications and fail on unstable bootstrap runs.

## 0.4.0 - 2026-07-13

- Add shared model specification, sample information, and provenance metadata.
- Add deterministic estimation-sample fingerprints and dependency-version capture.
- Standardize `tidy`, `glance`, `model_spec`, `sample_info`, and `provenance` across results.

## 0.3.0 - 2026-07-13

- Add cardinality-checked merges with unmatched-key reports.
- Add panel balance, coverage, singleton, and time-coverage diagnostics.
- Add within/between variance diagnostics and fixed-effect absorption flags.
- Add data-validation documentation, example, and tests.

## 0.2.0 - 2026-07-13

- Add one-way and two-way panel fixed effects with five covariance choices.
- Add classic DID, event-study estimates, and a joint pre-trend test.
- Add point-estimated cohort-time ATT for staggered adoption.
- Add subgroup, covariance-sensitivity, and placebo-timing diagnostics.
- Add panel/DID documentation, simulation example, and numerical tests.

## 0.1.0 - 2026-07-13

- Initialize the Python package, tests, documentation, and continuous integration.
- Add validated OLS with classical, HC1, and one-way cluster-robust covariance.
- Add tidy output and a deterministic runnable example.
