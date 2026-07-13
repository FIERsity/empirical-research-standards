# Ordinary least squares specification

## Estimand and design matrix

`fit_ols` estimates \(y = X\beta + \epsilon\) using `statsmodels.api.OLS`. Predictor order
is preserved. With the default `add_intercept=True`, a column named `const` is added
explicitly. Setting it to `False` estimates a regression through the origin.

The function rejects duplicate predictors, outcome leakage, non-numeric model columns,
non-finite values, insufficient observations, and rank-deficient design matrices. These
checks are deliberate: silent generalized-inverse solutions can conceal an unidentified
specification.

## Estimation sample

All outcome, predictor, and cluster columns define the model sample. Missing values raise an
error by default. `drop_missing=True` requests complete-case deletion and records the
original, retained, and dropped observation counts in the result.

## Covariance estimators

- `nonrobust`: classical homoskedastic OLS covariance.
- `HC1`: heteroskedasticity-consistent covariance with the HC1 degrees-of-freedom scaling.
- `cluster`: one-way cluster-robust covariance using the named cluster column and the
  `statsmodels` default finite-sample correction. At least two clusters are required.

Coefficient estimates are identical across covariance choices for the same sample; standard
errors, test statistics, p-values, and confidence intervals may differ.

## Result contract

`OLSResult` exposes labeled coefficients, standard errors, statistics, p-values, confidence
intervals, sample counts, degrees of freedom, R-squared values, model settings, and the raw
`statsmodels` result. `tidy()` creates a stable one-row-per-term table and can recompute
confidence intervals for a requested confidence level.

## Cross-software verification

Cross-software comparisons must align the estimation sample, intercept, variable order,
cluster definition, degrees-of-freedom correction, and confidence level. Cluster-robust
standard errors can differ between software because finite-sample corrections and degrees of
freedom are not universal. Record software versions and the exact Stata or R command beside
any comparison fixture.

