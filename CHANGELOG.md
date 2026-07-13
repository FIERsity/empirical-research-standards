# Changelog

All notable changes are documented here.

## 0.17.0 - 2026-07-13

- Add explicit dataframe schemas for column kinds, nullability, ranges, domains, and unique keys.
- Add exportable validation reports combining schema, merge, and panel evidence.
- Expand the runnable data-validation example and bilingual documentation.

## 0.16.0 - 2026-07-13

- Add a deterministic end-to-end panel research workflow from merge audit through exports.
- Export a human-readable design manifest alongside model, sample, provenance, diagnostic,
  placebo, covariance-sensitivity, and heterogeneity results.
- Add a bilingual workflow guide and make foundational workflow completeness the roadmap focus.

## 0.15.1 - 2026-07-13

- Reclassify capabilities as core, advanced with limits, supporting diagnostics, or absent.
- Correct stale panel-IV documentation and remove KP non-mislabeling as a capability claim.
- Add the IV relevance diagnostics to the documented `models` namespace.

## 0.15.0 - 2026-07-13

- Add absorbed-fixed-effect degrees-of-freedom correction for homoskedastic within panel IV.
- Match the scalable within backend to the exact indicator backend for coefficients and
  standard errors.
- Add an independent base-R fixed-effect projection and 2SLS covariance benchmark.

## 0.14.0 - 2026-07-13

- Add HC1 and one-way clustered conditional instrument-relevance Wald tests.
- Preserve the conventional F reference distribution only for homoskedastic diagnostics.
- Add an independent base-R HC1 matrix benchmark and explicit non-KP result labels.

## 0.13.0 - 2026-07-13

- Add transparent sample-rank diagnostics for multiple endogenous variables.
- Add homoskedastic conditional excluded-instrument F tests and conditional partial R-squared.
- Report normalized singular values without labeling them as Kleibergen-Paap statistics.

## 0.12.1 - 2026-07-13

- Remove the unused third-party benchmark placeholder and its pending validation path.
- Focus external numerical verification on reproducible Python-R comparisons.

## 0.12.0 - 2026-07-13

- Add the repository-distributed `apply-empirical-standards` Agent Skill as a core product.
- Guide agents through data audit, design declaration, estimator selection, diagnostics,
  standardized outputs, and cross-software verification without inferring causal validity.
- Add progressive API, method-selection, and output-checklist references plus a runnable
  environment and public-API check.
- Validate Skill metadata, linked resources, and required APIs in the test suite and CI.

## 0.11.0 - 2026-07-13

- Add scalable pyhdfe within-transformation for high-dimensional panel IV coefficients.
- Preserve the indicator backend as an exact finite-sample reference implementation.
- Label within-backend covariance as asymptotic and record absorbed degrees of freedom.
- Add first-stage summaries that distinguish conventional F from robust Wald statistics and
  explicitly refuse to label Wald-per-instrument as Kleibergen-Paap.

## 0.10.0 - 2026-07-13

- Add panel 2SLS with entity and/or time fixed-effect indicators.
- Add clustered panel-IV inference with entity clustering as the explicit default.
- Add Anderson-Rubin tests with controls, fixed effects, robust covariance, and clustering.
- Add grid-inverted Anderson-Rubin confidence sets that preserve disconnected acceptance sets.

## 0.9.0 - 2026-07-13

- Add validated 2SLS with explicit exogenous, endogenous, and instrument roles.
- Add first-stage strength, Wu-Hausman, Sargan, and robust Wooldridge score diagnostics.
- Add unadjusted, heteroskedasticity-robust, and one-way clustered IV covariance estimators.
- Add deterministic Python-R fixest 2SLS coefficient and standard-error benchmarks.

## 0.8.0 - 2026-07-13

- Add a deterministic Python-R fixed-effects benchmark with explicit covariance conventions.
- Add a machine-readable Python-R verification manifest.
- Add estimator-neutral coefficient, model, specification, sample, and provenance tables.
- Add CSV, Excel, and LaTeX exports plus normalized event-study plotting data.

## 0.7.0 - 2026-07-13

- Add null-imposed wild cluster bootstrap-t inference for fixed-effects coefficients.
- Add entity-level treatment-assignment permutation inference for DID.
- Add leave-one-cluster-out influence diagnostics for fixed-effects estimates.
- Add Bonferroni, Holm, and Benjamini-Hochberg p-value adjustments.

## 0.6.0 - 2026-07-13

- Add cohort-interacted Sun-Abraham event studies for staggered adoption.
- Add cohort-size weighted dynamic effects and delta-method standard errors.
- Add formal categorical fixed-effects heterogeneity estimation and joint Wald tests.
- Report group-specific treatment effects instead of comparing subgroup significance.

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
